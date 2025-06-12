import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import aiohttp
import feedparser
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from data_fetcher.models import FetchedNews, FetchLog, create_tables
from database import SessionLocal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsFetcher:
    """News fetcher for RSS feeds and news websites"""
    
    def __init__(self):
        # Create tables if they don't exist
        create_tables()
        
        # RSS feeds to monitor
        self.rss_feeds = [
            {
                'name': 'BBC News',
                'url': 'http://feeds.bbci.co.uk/news/rss.xml',
                'category': 'general'
            },
            {
                'name': 'Reuters',
                'url': 'http://feeds.reuters.com/reuters/topNews',
                'category': 'general'
            },
            {
                'name': 'TechCrunch',
                'url': 'https://techcrunch.com/feed/',
                'category': 'technology'
            },
            {
                'name': 'Hacker News',
                'url': 'https://feeds.feedburner.com/oreilly/radar/atom',
                'category': 'technology'
            },
            {
                'name': 'CNN',
                'url': 'http://rss.cnn.com/rss/edition.rss',
                'category': 'general'
            }
        ]
    
    async def fetch_rss_feed(self, session: aiohttp.ClientSession, feed_config: Dict[str, str]) -> List[Dict[str, Any]]:
        """Fetch and parse RSS feed"""
        try:
            logger.info(f"Fetching RSS feed from {feed_config['name']}: {feed_config['url']}")
            
            async with session.get(feed_config['url'], timeout=30) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch {feed_config['name']}: HTTP {response.status}")
                    return []
                
                content = await response.text()
                
            # Parse RSS feed
            feed = feedparser.parse(content)
            articles = []
            
            for entry in feed.entries:
                # Extract article data
                article = {
                    'title': entry.get('title', '').strip(),
                    'description': self._clean_html(entry.get('summary', entry.get('description', ''))),
                    'url': entry.get('link', '').strip(),
                    'source': feed_config['name'],
                    'category': feed_config['category'],
                    'author': entry.get('author', '').strip(),
                    'published_date': self._parse_date(entry.get('published', entry.get('updated'))),
                    'tags': self._extract_tags(entry)
                }
                
                # Skip if essential fields are missing
                if not article['title'] or not article['url']:
                    continue
                
                articles.append(article)
            
            logger.info(f"Fetched {len(articles)} articles from {feed_config['name']}")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_config['name']}: {e}")
            return []
    
    async def fetch_article_content(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Fetch full article content from URL"""
        try:
            async with session.get(url, timeout=20) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Try to find article content using common selectors
                content_selectors = [
                    'article',
                    '.article-content',
                    '.entry-content',
                    '.post-content',
                    '.content',
                    'main',
                    '.article-body'
                ]
                
                content = ""
                for selector in content_selectors:
                    elements = soup.select(selector)
                    if elements:
                        content = ' '.join([elem.get_text().strip() for elem in elements])
                        break
                
                # Fallback: get all paragraphs
                if not content:
                    paragraphs = soup.find_all('p')
                    content = ' '.join([p.get_text().strip() for p in paragraphs])
                
                # Clean and truncate content
                content = self._clean_text(content)
                return content[:5000] if content else None  # Limit to 5000 chars
                
        except Exception as e:
            logger.error(f"Error fetching article content from {url}: {e}")
            return None
    
    def _clean_html(self, html_text: str) -> str:
        """Remove HTML tags and clean text"""
        if not html_text:
            return ""
        
        soup = BeautifulSoup(html_text, 'html.parser')
        text = soup.get_text()
        return self._clean_text(text)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-\'""]', '', text)
        
        return text
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_str:
            return None
        
        try:
            # feedparser usually provides a time tuple
            if hasattr(date_str, 'timetuple'):
                return datetime(*date_str.timetuple()[:6])
            
            # Try parsing common date formats
            import dateutil.parser
            return dateutil.parser.parse(date_str)
            
        except Exception:
            return None
    
    def _extract_tags(self, entry) -> List[str]:
        """Extract tags from RSS entry"""
        tags = []
        
        # Try to get tags from various fields
        if hasattr(entry, 'tags'):
            tags.extend([tag.term for tag in entry.tags if hasattr(tag, 'term')])
        
        if hasattr(entry, 'categories'):
            tags.extend(entry.categories)
        
        # Clean and deduplicate tags
        tags = [tag.strip().lower() for tag in tags if tag.strip()]
        return list(set(tags))
    
    async def save_articles_to_db(self, articles: List[Dict[str, Any]]) -> int:
        """Save articles to database, return count of new articles"""
        if not articles:
            return 0
        
        new_count = 0
        db = SessionLocal()
        
        try:
            for article_data in articles:
                # Check if article already exists
                existing = db.query(FetchedNews).filter(
                    FetchedNews.url == article_data['url']
                ).first()
                
                if existing:
                    continue  # Skip duplicate
                
                # Create new article
                article = FetchedNews(
                    title=article_data['title'],
                    description=article_data['description'],
                    url=article_data['url'],
                    source=article_data['source'],
                    author=article_data['author'],
                    published_date=article_data['published_date'],
                    category=article_data['category'],
                    tags=article_data['tags'],
                    content=article_data.get('content')
                )
                
                db.add(article)
                new_count += 1
            
            db.commit()
            logger.info(f"Saved {new_count} new articles to database")
            return new_count
            
        except Exception as e:
            logger.error(f"Error saving articles to database: {e}")
            db.rollback()
            return 0
        finally:
            db.close()
    
    def log_fetch_operation(self, task_name: str, source: str, start_time: datetime, 
                           end_time: datetime, status: str, items_fetched: int, 
                           items_new: int, error_message: str = None):
        """Log fetch operation to database"""
        db = SessionLocal()
        try:
            execution_time = (end_time - start_time).total_seconds()
            
            log_entry = FetchLog(
                task_name=task_name,
                source=source,
                start_time=start_time,
                end_time=end_time,
                status=status,
                items_fetched=items_fetched,
                items_new=items_new,
                error_message=error_message,
                execution_time=execution_time
            )
            
            db.add(log_entry)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error logging fetch operation: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def fetch_all_news(self, fetch_content: bool = False) -> Dict[str, Any]:
        """Fetch news from all configured RSS feeds"""
        start_time = datetime.utcnow()
        total_fetched = 0
        total_new = 0
        errors = []
        
        logger.info("Starting daily news fetch operation...")
        
        try:
            async with aiohttp.ClientSession() as session:
                all_articles = []
                
                # Fetch from all RSS feeds
                for feed_config in self.rss_feeds:
                    try:
                        articles = await self.fetch_rss_feed(session, feed_config)
                        
                        # Optionally fetch full content
                        if fetch_content and articles:
                            logger.info(f"Fetching full content for {len(articles)} articles from {feed_config['name']}")
                            for article in articles[:5]:  # Limit to 5 articles per source to avoid overload
                                content = await self.fetch_article_content(session, article['url'])
                                if content:
                                    article['content'] = content
                        
                        all_articles.extend(articles)
                        total_fetched += len(articles)
                        
                    except Exception as e:
                        error_msg = f"Error fetching from {feed_config['name']}: {e}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                
                # Save articles to database
                if all_articles:
                    total_new = await self.save_articles_to_db(all_articles)
                
                end_time = datetime.utcnow()
                status = "success" if not errors else "partial_success"
                
                # Log the operation
                self.log_fetch_operation(
                    task_name="daily_news_fetch",
                    source="multiple_rss",
                    start_time=start_time,
                    end_time=end_time,
                    status=status,
                    items_fetched=total_fetched,
                    items_new=total_new,
                    error_message="; ".join(errors) if errors else None
                )
                
                result = {
                    "success": True,
                    "total_fetched": total_fetched,
                    "total_new": total_new,
                    "execution_time": (end_time - start_time).total_seconds(),
                    "sources_processed": len(self.rss_feeds),
                    "errors": errors
                }
                
                logger.info(f"News fetch completed: {total_new} new articles from {total_fetched} total")
                return result
                
        except Exception as e:
            end_time = datetime.utcnow()
            error_msg = f"Critical error in fetch_all_news: {e}"
            logger.error(error_msg)
            
            # Log the failed operation
            self.log_fetch_operation(
                task_name="daily_news_fetch",
                source="multiple_rss",
                start_time=start_time,
                end_time=end_time,
                status="failed",
                items_fetched=0,
                items_new=0,
                error_message=error_msg
            )
            
            return {
                "success": False,
                "error": error_msg,
                "total_fetched": 0,
                "total_new": 0,
                "execution_time": (end_time - start_time).total_seconds()
            }


# Global news fetcher instance
news_fetcher = NewsFetcher() 