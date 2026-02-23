# Deployment Guide

## Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 14+ (or SQLite for dev)
- Redis 6+
- Git

## Environment Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd enterprise-ai-security-platform
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your configuration
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env
# Edit .env if needed (usually defaults work for local dev)
```

### 4. Database Setup

#### Option A: SQLite (Development)
SQLite is used by default. No setup required.

#### Option B: PostgreSQL (Production)
```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb ai_security

# Update .env
DATABASE_URL=postgresql://user:password@localhost:5432/ai_security
```

### 5. Redis Setup

```bash
# Install Redis
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis

# Verify
redis-cli ping
# Should return: PONG
```

### 6. Ollama Setup (Optional - for local models)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3.2

# Start Ollama server
ollama serve
```

## Running Locally

### Development Mode

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 - RQ Worker (Optional):**
```bash
cd backend
source venv/bin/activate
./start_worker.sh
```

Access the application:
- Frontend: http://localhost:3001
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Production Mode

```bash
# Backend
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Frontend
cd frontend
npm run build
npm run preview
```

## Cloud Deployment

### Railway (Recommended)

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Login and create project:
```bash
railway login
railway init
```

3. Deploy:
```bash
railway up
```

4. Add environment variables in Railway dashboard:
   - DATABASE_URL
   - REDIS_URL
   - SECRET_KEY
   - API_KEYS
   - OPENAI_API_KEY (optional)
   - ANTHROPIC_API_KEY (optional)

### Render

1. Create `render.yaml`:
```yaml
services:
  - type: web
    name: ai-security-backend
    env: python
    buildCommand: cd backend && pip install -r requirements.txt
    startCommand: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: ai-security-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: ai-security-redis
          property: connectionString

  - type: web
    name: ai-security-frontend
    env: static
    buildCommand: cd frontend && npm install && npm run build
    staticPublishPath: frontend/dist
    routes:
      - type: rewrite
        source: /
        destination: /index.html

databases:
  - name: ai-security-db
    databaseName: ai_security
    user: ai_security

redis:
  - name: ai-security-redis
```

2. Deploy via Render dashboard or CLI.

### Vercel (Frontend Only)

1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Deploy:
```bash
cd frontend
vercel
```

3. Set environment variable:
```bash
vercel env add VITE_API_URL
# Enter: https://your-backend-url.com/api/v1
```

## Docker Deployment

### Development

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Production

```bash
# Build production images
docker-compose -f docker-compose.prod.yml up -d
```

## Environment Variables

### Backend (.env)

```env
# Required
DATABASE_URL=sqlite:///./ai_security.db
SECRET_KEY=your-secret-key-here
API_KEYS=test-api-key-1,test-api-key-2
ALLOWED_ORIGINS=http://localhost:3001,http://localhost:5173

# Optional - Model API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Optional - Model Configuration
OPENAI_MODEL=gpt-4
ANTHROPIC_MODEL=claude-3-opus-20240229
OLLAMA_BASE_URL=http://localhost:11434
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_API_KEY=test-api-key-1
```

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use strong API keys in production
- [ ] Enable HTTPS
- [ ] Set up CORS properly
- [ ] Configure rate limiting
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set up database backups
- [ ] Enable logging
- [ ] Use environment variables for secrets
- [ ] Regular security updates

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill <PID>
```

### Database Connection Issues
```bash
# Test PostgreSQL connection
psql $DATABASE_URL -c "SELECT 1"

# Check Redis
redis-cli ping
```

### RQ Worker Not Processing Jobs
```bash
# Check if worker is running
ps aux | grep "rq worker"

# Restart worker
cd backend
./start_worker.sh
```

## Monitoring

### Health Checks
```bash
# Backend health
curl https://your-api.com/health

# Production health
curl https://your-api.com/api/v1/health/production
```

### Logs
```bash
# Backend logs
tail -f logs/app.log

# RQ worker logs
tail -f /tmp/rq_worker.log

# Docker logs
docker-compose logs -f
```

## Backup & Recovery

### Database Backup
```bash
# PostgreSQL
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql
```

### SQLite Backup
```bash
# Copy database file
cp ai_security.db ai_security_backup.db
```

## Scaling

### Horizontal Scaling
- Run multiple backend instances behind load balancer
- Scale RQ workers independently
- Use Redis for session storage

### Database Scaling
- Use read replicas for analytics queries
- Implement connection pooling
- Consider database sharding for high volume

## Support

For deployment issues:
- Check logs: `logs/app.log`
- Review documentation: `/docs`
- Open GitHub issue