# 🚀 Vercel Deployment Guide

Deploy ScrapeThyPlaite as a serverless API on Vercel in minutes.

## Quick Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/JackAmichai/ScrapeThyPlaite)

## Manual Deployment

### 1. Prerequisites

- [Vercel Account](https://vercel.com/signup)
- [Vercel CLI](https://vercel.com/cli) (optional)
- Node.js 18+ (for CLI)

### 2. Deploy via GitHub

1. Fork/clone this repository to your GitHub
2. Go to [Vercel Dashboard](https://vercel.com/dashboard)
3. Click "Add New" → "Project"
4. Import your GitHub repository
5. Configure environment variables (see below)
6. Click "Deploy"

### 3. Deploy via CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy from project root
cd ScrapeThyPlaite
vercel

# Deploy to production
vercel --prod
```

## Environment Variables

Set these in Vercel Dashboard → Project Settings → Environment Variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `SCRAPER_API_KEY` | Optional | API key for authentication |
| `REDIS_URL` | Optional | Redis URL for job persistence (Vercel KV) |
| `OPENAI_API_KEY` | Optional | For AI-powered extraction |
| `ANTHROPIC_API_KEY` | Optional | For Claude extraction |
| `TWOCAPTCHA_API_KEY` | Optional | For CAPTCHA solving |

### Setting Up Vercel KV (Redis)

1. Go to Vercel Dashboard → Storage
2. Click "Create Database" → "KV"
3. Follow setup wizard
4. `REDIS_URL` will be automatically configured

## API Endpoints

Once deployed, your API will be available at `https://your-project.vercel.app`

### Health Check
```bash
GET /api/health
```

### Scrape Single URL
```bash
POST /api/scrape
Content-Type: application/json
X-API-Key: your-api-key (if configured)

{
  "url": "https://example.com",
  "javascript": false,
  "timeout": 30,
  "bypass_protection": true,
  "extract": {
    "title": "h1",
    "links": "a[href]"
  }
}
```

### Batch Scrape
```bash
POST /api/batch
Content-Type: application/json

{
  "urls": [
    "https://example.com/page1",
    "https://example.com/page2"
  ],
  "concurrency": 5,
  "timeout": 30,
  "extract": {
    "title": "title"
  }
}
```

### Get Job Status
```bash
GET /api/status/{job_id}
```

## Limitations

### Vercel Serverless Constraints

| Limit | Hobby | Pro |
|-------|-------|-----|
| Execution Time | 10s | 60s |
| Memory | 1GB | 3GB |
| Payload Size | 4.5MB | 4.5MB |

### What Works on Vercel

✅ HTTP-based scraping (CloudScraper, requests)
✅ Cloudflare JS Challenge bypass
✅ Data extraction with BeautifulSoup
✅ Batch processing (within timeout)
✅ Redis job persistence (with Vercel KV)

### What Doesn't Work on Vercel

❌ Browser automation (Selenium, Playwright)
❌ Undetected Chrome
❌ Long-running scraping jobs
❌ WebSocket monitoring server

### Workarounds

For browser automation, consider:
- [Railway](https://railway.app) - Full Docker support
- [Render](https://render.com) - Background workers
- [AWS Lambda](https://aws.amazon.com/lambda/) with Puppeteer layers
- Self-hosted VPS with Docker

## Example Usage

### cURL
```bash
curl -X POST https://your-project.vercel.app/api/scrape \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"url": "https://news.ycombinator.com", "extract": {"titles": ".titleline > a"}}'
```

### JavaScript
```javascript
const response = await fetch('https://your-project.vercel.app/api/scrape', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-key'
  },
  body: JSON.stringify({
    url: 'https://news.ycombinator.com',
    extract: { titles: '.titleline > a' }
  })
});

const data = await response.json();
console.log(data.extracted_data.titles);
```

### Python
```python
import requests

response = requests.post(
    'https://your-project.vercel.app/api/scrape',
    headers={
        'Content-Type': 'application/json',
        'X-API-Key': 'your-key'
    },
    json={
        'url': 'https://news.ycombinator.com',
        'extract': {'titles': '.titleline > a'}
    }
)

data = response.json()
print(data['extracted_data']['titles'])
```

## Monitoring

For production monitoring, consider:

1. **Vercel Analytics** - Built-in performance monitoring
2. **Sentry** - Error tracking
3. **Datadog** - Full observability

## Scaling

### High Volume Scraping

For high-volume needs:

1. **Upgrade to Pro** - Higher limits
2. **Use Edge Functions** - Faster cold starts
3. **Implement Caching** - Redis/Vercel KV
4. **Queue System** - Process asynchronously

### Rate Limiting

Add rate limiting with Vercel Edge:

```javascript
// middleware.js
export function middleware(request) {
  // Implement rate limiting logic
}
```

## Troubleshooting

### "Function timed out"
- Reduce timeout in request
- Use batch endpoint for multiple URLs
- Consider longer-timeout hosting

### "Module not found"
- Check `api/requirements.txt`
- Ensure all dependencies are listed

### "502 Bad Gateway"
- Check function logs in Vercel dashboard
- Verify environment variables

## Support

- 📖 [Documentation](https://github.com/JackAmichai/ScrapeThyPlaite)
- 🐛 [Issue Tracker](https://github.com/JackAmichai/ScrapeThyPlaite/issues)
- 💬 [Discussions](https://github.com/JackAmichai/ScrapeThyPlaite/discussions)
