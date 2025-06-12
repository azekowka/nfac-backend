#!/usr/bin/env python3
"""
Test script for Data Fetcher System
Run this to verify all components are working correctly
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_fetcher.news_fetcher import news_fetcher
from data_fetcher.models import create_tables, FetchedNews
from database import SessionLocal

async def test_news_fetcher():
    """Test the news fetcher functionality"""
    print("🧪 Testing Data Fetcher System...")
    print("=" * 50)
    
    # Test 1: Create database tables
    print("1. Creating database tables...")
    try:
        create_tables()
        print("   ✅ Database tables created successfully")
    except Exception as e:
        print(f"   ❌ Error creating tables: {e}")
        return False
    
    # Test 2: Test single RSS feed
    print("\n2. Testing single RSS feed fetch...")
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            # Test BBC News feed
            feed_config = {
                'name': 'BBC News',
                'url': 'http://feeds.bbci.co.uk/news/rss.xml',
                'category': 'general'
            }
            articles = await news_fetcher.fetch_rss_feed(session, feed_config)
            if articles:
                print(f"   ✅ Successfully fetched {len(articles)} articles from BBC News")
                print(f"   📰 Sample article: '{articles[0]['title'][:50]}...'")
            else:
                print("   ⚠️  No articles fetched (this might be normal)")
    except Exception as e:
        print(f"   ❌ Error fetching RSS feed: {e}")
        return False
    
    # Test 3: Test database save
    print("\n3. Testing database save functionality...")
    try:
        if articles:
            # Take only first article for testing
            test_articles = articles[:1]
            new_count = await news_fetcher.save_articles_to_db(test_articles)
            print(f"   ✅ Successfully saved {new_count} new articles to database")
        else:
            print("   ⚠️  Skipped database test (no articles to save)")
    except Exception as e:
        print(f"   ❌ Error saving to database: {e}")
        return False
    
    # Test 4: Test database read
    print("\n4. Testing database read functionality...")
    try:
        db = SessionLocal()
        article_count = db.query(FetchedNews).count()
        db.close()
        print(f"   ✅ Total articles in database: {article_count}")
    except Exception as e:
        print(f"   ❌ Error reading from database: {e}")
        return False
    
    # Test 5: Test full fetch process
    print("\n5. Testing complete fetch process...")
    try:
        result = await news_fetcher.fetch_all_news(fetch_content=False)
        if result['success']:
            print(f"   ✅ Full fetch completed successfully!")
            print(f"   📊 Total fetched: {result['total_fetched']}")
            print(f"   📊 New articles: {result['total_new']}")
            print(f"   📊 Sources processed: {result['sources_processed']}")
            print(f"   ⏱️  Execution time: {result['execution_time']:.2f}s")
            if result['errors']:
                print(f"   ⚠️  Errors encountered: {len(result['errors'])}")
        else:
            print(f"   ❌ Full fetch failed: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"   ❌ Error in full fetch process: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed successfully!")
    print("The Data Fetcher system is ready to use.")
    
    return True

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing module imports...")
    
    try:
        from data_fetcher.models import FetchedNews, FetchLog, FetchedWebsiteData
        print("   ✅ Data models imported successfully")
        
        from data_fetcher.news_fetcher import NewsFetcher
        print("   ✅ News fetcher imported successfully")
        
        from data_fetcher.tasks import daily_news_fetch_task
        print("   ✅ Celery tasks imported successfully")
        
        from data_fetcher.api import router
        print("   ✅ API router imported successfully")
        
        from data_fetcher.scheduler import celery_app
        print("   ✅ Scheduler imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Data Fetcher System Tests")
    print("This will verify that all components are working correctly.\n")
    
    # Test imports first
    if not test_imports():
        print("\n❌ Import tests failed. Please check your dependencies.")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    
    # Run async tests
    try:
        result = asyncio.run(test_news_fetcher())
        if result:
            print("\n✨ Data Fetcher System is ready!")
            print("\nNext steps:")
            print("1. Start the services: docker-compose up -d")
            print("2. Check API health: curl http://localhost:8000/data-fetcher/health")
            print("3. Trigger manual fetch: curl -X POST http://localhost:8000/data-fetcher/fetch/manual")
            print("4. View fetched data: curl http://localhost:8000/data-fetcher/news?limit=5")
        else:
            print("\n❌ Some tests failed. Please check the errors above.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1) 