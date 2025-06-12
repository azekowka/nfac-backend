# Data Fetcher System

## Overview

The Data Fetcher system is a comprehensive solution for automatically collecting, storing, and serving data from various websites and RSS feeds. It's designed to run daily scheduled tasks to fetch news articles and other web content, storing them in a PostgreSQL database for later retrieval and analysis.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   RSS Feeds     │    │   News Websites  │    │  Other Sources  │
│                 │    │                  │    │                 │
│ • BBC News      │    │ • TechCrunch     │    │ • Weather APIs  │
│ • Reuters       │    │ • CNN            │    │ • Stock APIs    │
│ • Hacker News   │    │ • Custom Sites   │    │ • Social Media  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Fetcher Service                         │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  News Fetcher   │  │ Generic Fetcher │  │ Content Parser  │ │
│  │                 │  │                 │  │                 │ │
│  │ • RSS Parsing   │  │ • HTTP Requests │  │ • HTML Cleaning │ │
│  │ • Content       │  │ • Rate Limiting │  │ • Text Extract  │ │
│  │   Extraction    │  │ • Error Handle  │  │ • Metadata      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Celery Task Queue                         │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Daily Fetch    │  │ Manual Fetch    │  │   Cleanup       │ │
│  │                 │  │                 │  │                 │ │
│  │ • 6:00 AM UTC   │  │ • On-demand     │  │ • Weekly        │ │
│  │ • Light fetch   │  │ • Full content  │  │ • Remove old    │ │
│  │ • All sources   │  │ • API triggered │  │   data          │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                       PostgreSQL Database                      │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ fetched_news    │  │ fetched_website │  │  fetch_logs     │ │
│  │                 │  │      _data      │  │                 │ │
│  │ • Articles      │  │ • Generic data  │  │ • Operations    │ │
│  │ • Metadata      │  │ • JSON storage  │  │ • Performance   │ │
│  │ • Full content  │  │ • Multi-type    │  │ • Error logs    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI REST API                        │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Data Access   │  │ Task Control    │  │   Monitoring    │ │
│  │                 │  │                 │  │                 │ │
│  │ • List articles │  │ • Trigger fetch │  │ • Health check  │ │
│  │ • Search filter │  │ • Monitor tasks │  │ • Statistics    │ │
│  │ • Pagination    │  │ • Schedule mgmt │  │ • Logs viewing  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Data Models (`data_fetcher/models.py`)

#### FetchedNews
- **Purpose**: Store news articles from RSS feeds
- **Key fields**: title, description, url, source, category, published_date, content
- **Metadata**: fetch_date, processed, sentiment_score

#### FetchedWebsiteData
- **Purpose**: Generic storage for any website data
- **Key fields**: source_name, data_type, structured_data (JSON)
- **Flexible**: Can store weather, stock prices, social media, etc.

#### FetchLog
- **Purpose**: Track all fetch operations
- **Monitoring**: execution time, success rate, error tracking
- **Analytics**: Performance metrics and operational insights

### 2. News Fetcher (`data_fetcher/news_fetcher.py`)

#### RSS Feed Sources
- **BBC News**: General news
- **Reuters**: World news
- **TechCrunch**: Technology news
- **CNN**: US news
- **Hacker News**: Tech community

#### Features
- **Async processing**: High-performance concurrent fetching
- **Content extraction**: Full article content using BeautifulSoup
- **Duplicate detection**: URL-based deduplication
- **Error handling**: Graceful failures with detailed logging
- **Rate limiting**: Respectful crawling practices

### 3. Celery Tasks (`data_fetcher/tasks.py`)

#### Daily News Fetch (`daily_news_fetch`)
- **Schedule**: 6:00 AM UTC daily
- **Mode**: Light fetch (titles, descriptions, URLs)
- **Performance**: Fast, minimal resource usage

#### Manual News Fetch (`manual_news_fetch`)
- **Trigger**: API endpoint or admin
- **Mode**: Full content fetch
- **Use case**: On-demand comprehensive collection

#### Cleanup Task (`cleanup_old_data`)
- **Schedule**: Weekly (Sunday 2:00 AM UTC)
- **Purpose**: Remove data older than 30 days
- **Benefit**: Maintain database performance

#### Status Report (`fetch_status_report`)
- **Schedule**: Every 6 hours
- **Content**: Success rates, source breakdown, recent logs
- **Purpose**: Operational monitoring

### 4. Scheduler (`data_fetcher/scheduler.py`)

#### Scheduled Tasks
```python
# Daily news fetch at 6:00 AM UTC
'daily-news-fetch': {
    'task': 'daily_news_fetch',
    'schedule': crontab(hour=6, minute=0),
    'kwargs': {'fetch_content': False}
}

# Weekly comprehensive fetch on Sundays at 3:00 AM UTC
'weekly-comprehensive-fetch': {
    'task': 'manual_news_fetch',
    'schedule': crontab(hour=3, minute=0, day_of_week=0),
    'kwargs': {'fetch_content': True}
}
```

### 5. REST API (`data_fetcher/api.py`)

#### Data Endpoints

**GET /data-fetcher/news**
- **Purpose**: List news articles with filtering
- **Parameters**: skip, limit, source, category, from_date, to_date, search
- **Response**: Paginated list of NewsArticle objects

**GET /data-fetcher/news/{article_id}**
- **Purpose**: Get specific article details
- **Response**: Full NewsArticle object

**GET /data-fetcher/sources**
- **Purpose**: List available news sources
- **Response**: Array of {source, count} objects

**GET /data-fetcher/categories**
- **Purpose**: List article categories
- **Response**: Array of {category, count} objects

**GET /data-fetcher/stats**
- **Purpose**: Overall statistics
- **Response**: Total articles, today's count, success rate, etc.

#### Control Endpoints

**POST /data-fetcher/fetch/manual**
- **Purpose**: Trigger manual fetch
- **Parameters**: fetch_content (boolean)
- **Response**: Task ID and status

**POST /data-fetcher/cleanup**
- **Purpose**: Trigger data cleanup
- **Parameters**: days_to_keep (default: 30)
- **Response**: Task ID and status

**GET /data-fetcher/task/{task_id}**
- **Purpose**: Monitor task progress
- **Response**: Task state and result

## Installation & Setup

### 1. Dependencies
```bash
# Core dependencies already added to requirements.txt:
aiohttp==3.10.12          # Async HTTP client
feedparser==6.0.11        # RSS feed parsing
beautifulsoup4==4.12.3    # HTML parsing
python-dateutil==2.9.0.post0  # Date parsing
lxml==5.3.0               # XML/HTML parser
```

### 2. Database Setup
```bash
# The tables are created automatically when the app starts
# Tables: fetched_news, fetched_website_data, fetch_logs
```

### 3. Environment Variables
```env
# No additional environment variables required
# Uses existing DATABASE_URL and Redis configuration
```

## Usage Examples

### 1. Starting the Services
```bash
# Start all services including Celery Beat scheduler
docker-compose up -d

# Check service health
curl http://localhost:8000/data-fetcher/health
```

### 2. Manual Data Fetch
```bash
# Trigger manual fetch (without full content)
curl -X POST "http://localhost:8000/data-fetcher/fetch/manual?fetch_content=false"

# Trigger comprehensive fetch (with full content)
curl -X POST "http://localhost:8000/data-fetcher/fetch/manual?fetch_content=true"
```

### 3. Viewing Data
```bash
# Get latest news articles
curl "http://localhost:8000/data-fetcher/news?limit=10"

# Search for specific topics
curl "http://localhost:8000/data-fetcher/news?search=technology&category=technology"

# Filter by source and date
curl "http://localhost:8000/data-fetcher/news?source=BBC%20News&from_date=2024-01-01"

# Get statistics
curl "http://localhost:8000/data-fetcher/stats"
```

### 4. Monitoring
```bash
# Check fetch logs
curl "http://localhost:8000/data-fetcher/logs?limit=20"

# Monitor specific task
curl "http://localhost:8000/data-fetcher/task/{task_id}"

# Generate status report
curl -X POST "http://localhost:8000/data-fetcher/report"
```

## Scheduled Operations

### Daily Schedule (UTC)
- **02:00** - Weekly cleanup (Sundays only)
- **03:00** - Weekly comprehensive fetch (Sundays only)
- **06:00** - Daily news fetch (every day)
- **00:00, 06:00, 12:00, 18:00** - Status reports (every 6 hours)

### Customizing Schedule
To modify the schedule, edit `data_fetcher/scheduler.py`:

```python
# Example: Fetch every 2 hours during business days
'business-hours-fetch': {
    'task': 'daily_news_fetch',
    'schedule': crontab(minute=0, hour='9-17/2', day_of_week='1-5'),
    'kwargs': {'fetch_content': False}
}
```

## Extending the System

### Adding New Data Sources

1. **Create a new fetcher class** in `data_fetcher/`
2. **Add new task** in `data_fetcher/tasks.py`
3. **Update scheduler** in `data_fetcher/scheduler.py`
4. **Add API endpoints** in `data_fetcher/api.py`

Example for weather data:
```python
class WeatherFetcher:
    async def fetch_weather_data(self, cities: List[str]):
        # Implementation here
        pass

@celery_app.task(name="daily_weather_fetch")
def daily_weather_fetch_task(self):
    # Task implementation
    pass
```

### Adding New Data Types

Use the `FetchedWebsiteData` model for flexible data storage:

```python
weather_data = FetchedWebsiteData(
    source_name="OpenWeatherMap",
    source_url="https://api.openweathermap.org",
    data_type="weather",
    title=f"Weather for {city}",
    structured_data={
        "temperature": 25.5,
        "humidity": 60,
        "conditions": "partly_cloudy"
    }
)
```

## Performance & Monitoring

### Key Metrics
- **Fetch success rate**: Should be >95%
- **Average execution time**: <2 minutes for daily fetch
- **Database growth**: ~100-500 articles per day
- **Error rate**: <5% of operations

### Troubleshooting

#### Common Issues
1. **RSS feed timeout**: Increase timeout in `news_fetcher.py`
2. **Database lock**: Check Celery worker concurrency
3. **Memory usage**: Enable content cleanup tasks
4. **Rate limiting**: Add delays between requests

#### Logs Location
- **Application logs**: Docker container logs
- **Celery logs**: Celery worker/beat container logs
- **Database logs**: `fetch_logs` table

## Security Considerations

### Data Privacy
- **No personal data**: Only public news articles
- **URL validation**: Prevent SSRF attacks
- **Content sanitization**: HTML/XSS protection

### Resource Protection
- **Rate limiting**: Built-in delays
- **Memory limits**: Content size restrictions
- **Timeout handling**: Prevent hanging requests

## Future Enhancements

### Planned Features
1. **AI Analysis**: Sentiment analysis, topic classification
2. **Real-time Updates**: WebSocket notifications
3. **Search Enhancement**: Full-text search, elasticsearch
4. **Content Deduplication**: Similarity-based detection
5. **Multi-language Support**: International news sources
6. **API Rate Limiting**: Per-user quotas
7. **Data Export**: CSV, JSON, RSS feed generation
8. **Custom Sources**: User-defined RSS feeds

### Scalability Options
1. **Horizontal scaling**: Multiple Celery workers
2. **Database sharding**: Time-based partitioning
3. **Caching layer**: Redis caching for frequent queries
4. **CDN integration**: Static content delivery
5. **Message queuing**: RabbitMQ for high-volume processing

---

## Quick Start Commands

```bash
# 1. Start the system
docker-compose up -d

# 2. Check health
curl http://localhost:8000/data-fetcher/health

# 3. Trigger first fetch
curl -X POST "http://localhost:8000/data-fetcher/fetch/manual"

# 4. View results
curl "http://localhost:8000/data-fetcher/news?limit=5"

# 5. Check stats
curl "http://localhost:8000/data-fetcher/stats"
```

The Data Fetcher system is now ready to automatically collect and serve news data daily! 