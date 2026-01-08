# Deployment Guide

Complete guide for deploying the Labeled platform.

## Quick Start with Docker

The easiest way to deploy Labeled is using Docker Compose:

```bash
# 1. Clone the repository
git clone <repository-url>
cd labeled

# 2. Set up environment variables
cp .env.example .env
# Edit .env and set your SECRET_KEY

# 3. Start all services
docker-compose up -d

# 4. Access the platform
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   React     │◄────►│   FastAPI    │◄────►│ PostgreSQL  │
│  Frontend   │      │   Backend    │      │  Database   │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  Blockchain  │
                     │  (In-Memory) │
                     └──────────────┘
```

## Requirements

### Docker Deployment (Recommended)
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 10GB disk space

### Manual Deployment
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

## Manual Deployment

### Backend Setup

```bash
# 1. Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
pip install -r ../requirements.txt

# 3. Set up PostgreSQL database
createdb labeled

# 4. Configure environment
export DATABASE_URL="postgresql://user:password@localhost:5432/labeled"
export SECRET_KEY="your-secret-key-here"

# 5. Run migrations (automatic on startup)
# 6. Start backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
# 1. Install dependencies
cd frontend
npm install

# 2. Configure API endpoint (in vite.config.js)
# Update proxy target if needed

# 3. Build for production
npm run build

# 4. Serve (or use nginx)
npm run preview
```

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Security
SECRET_KEY=generate-a-random-secret-key

# Blockchain
MINING_DIFFICULTY=4
MINING_REWARD=10.0

# Token System
REWARD_AMOUNT=10.0
PENALTY_AMOUNT=5.0
INITIAL_TOKEN_BALANCE=100.0

# Consensus
MIN_LABELERS=4
SUPERMAJORITY_THRESHOLD=0.667
```

### Generating a Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Production Deployment

### Using Nginx (Reverse Proxy)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        root /var/www/labeled/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### SSL/HTTPS Setup

```bash
# Using Certbot (Let's Encrypt)
sudo certbot --nginx -d yourdomain.com
```

### Process Management (PM2)

```bash
# Install PM2
npm install -g pm2

# Backend
pm2 start "uvicorn backend.app.main:app --host 0.0.0.0 --port 8000" --name labeled-backend

# Save configuration
pm2 save
pm2 startup
```

### PostgreSQL Configuration

For production, configure PostgreSQL with:

```sql
-- Create user and database
CREATE USER labeled WITH PASSWORD 'secure_password';
CREATE DATABASE labeled OWNER labeled;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE labeled TO labeled;
```

## Scaling

### Horizontal Scaling

1. **Database**: Use PostgreSQL replication for read replicas
2. **Backend**: Run multiple API instances behind load balancer
3. **Frontend**: Serve static files via CDN

### Load Balancer Configuration

```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    location /api {
        proxy_pass http://backend;
    }
}
```

## Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Database connection
psql -h localhost -U labeled -d labeled -c "SELECT 1"
```

### Logging

```bash
# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend

# PM2 logs
pm2 logs labeled-backend
```

## Backup and Recovery

### Database Backup

```bash
# Backup
pg_dump labeled > labeled_backup_$(date +%Y%m%d).sql

# Restore
psql labeled < labeled_backup_20240101.sql
```

### Blockchain State

The blockchain state is stored in memory by default. For production:

1. Implement blockchain persistence to disk
2. Regular backups of blockchain state
3. Consider distributed blockchain storage

## Troubleshooting

### Common Issues

**Connection Refused**
```bash
# Check if services are running
docker-compose ps

# Check logs
docker-compose logs backend
```

**Database Connection Error**
```bash
# Verify PostgreSQL is running
pg_isready -h localhost

# Check connection string
echo $DATABASE_URL
```

**Frontend Not Loading**
```bash
# Check API proxy configuration in vite.config.js
# Verify CORS settings in backend
```

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use strong database passwords
- [ ] Enable HTTPS in production
- [ ] Configure CORS appropriately
- [ ] Set up firewall rules
- [ ] Regular security updates
- [ ] Enable rate limiting
- [ ] Implement request validation

## Performance Tuning

### Database

```sql
-- Add indexes for performance
CREATE INDEX idx_labels_user_id ON labels(user_id);
CREATE INDEX idx_labels_data_item_id ON labels(data_item_id);
CREATE INDEX idx_data_items_consensus ON data_items(has_consensus);
```

### Backend

```python
# Adjust uvicorn workers
uvicorn backend.app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

### Caching

Consider adding Redis for:
- Session management
- API response caching
- Blockchain state caching

## Updates and Migrations

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose down
docker-compose build
docker-compose up -d

# Run database migrations (if any)
# Add migration tools like Alembic for production
```
