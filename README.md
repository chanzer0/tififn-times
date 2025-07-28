# Tiffin Times - Emergency Call Logs Mapper

A modern web application for visualizing emergency call logs from JECC (Jefferson Emergency Communications Center) on an interactive map. Built with React, FastAPI, and PostgreSQL.

## Features

- 🗺️ **Interactive Map**: View emergency calls plotted on a map with custom markers by call type
- 📋 **Log Management**: Browse, filter, and search through emergency call logs
- 🔍 **Advanced Filtering**: Filter by date range, agency, call type, and more
- 📍 **Geocoding**: Automatic address geocoding using Nominatim/OpenStreetMap
- ⚡ **Fast Performance**: Redis caching and optimized database queries
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 🔄 **Real-time Updates**: Automated scraping and data refresh

## Tech Stack

- **Frontend**: React 18 + TypeScript + Vite
- **Backend**: FastAPI + SQLAlchemy + Alembic
- **Database**: PostgreSQL
- **Caching**: Redis
- **Maps**: React-Leaflet + OpenStreetMap
- **Geocoding**: Nominatim (OpenStreetMap)

## Project Structure

```
tiffin-times/
├── client/              # React frontend
│   ├── src/
│   │   ├── components/  # Reusable UI components
│   │   ├── pages/       # Page components
│   │   ├── hooks/       # Custom React hooks
│   │   ├── services/    # API client
│   │   └── types/       # TypeScript type definitions
│   ├── public/
│   └── package.json
├── server/              # FastAPI backend
│   ├── app/
│   │   ├── api/v1/      # API routes and schemas
│   │   ├── core/        # Configuration and database
│   │   ├── models/      # Database models
│   │   ├── services/    # Business logic
│   │   └── scraper/     # JECC data scraper
│   ├── alembic/         # Database migrations
│   └── requirements.txt
├── scripts/             # Utility scripts
├── infra/              # Infrastructure as code
└── .github/workflows/  # CI/CD pipelines
```

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 12+
- Redis 6+

### 1. Clone the Repository

```bash
git clone <repository-url>
cd tiffin-times
```

### 2. Backend Setup

```bash
# Navigate to server directory
cd server

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (Command Prompt):
venv\Scripts\activate
# On Windows (PowerShell):
venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
# On Windows:
copy ..\.env.example .env
# On macOS/Linux:
cp ../.env.example .env

# Edit .env with your database credentials
# DATABASE_USER=your_db_user
# DATABASE_PASSWORD=your_db_password
# DATABASE_HOST=localhost
# DATABASE_PORT=5432
# DATABASE_NAME=tiffin_times
# REDIS_URL=redis://localhost:6379
```

### 3. Database Setup

**Option A: Using SQL (Recommended for Windows)**
```sql
-- Connect to PostgreSQL (using psql, pgAdmin, or any PostgreSQL client)
-- If using psql:
psql -U postgres
-- Then create the database:
CREATE DATABASE tiffin_times;
-- Exit psql:
\q
```

**Option B: Using createdb (if PostgreSQL bin is in PATH)**
```bash
# Create database (replace with your credentials)
createdb tiffin_times
```

**Option C: Using pgAdmin (GUI)**
1. Open pgAdmin
2. Connect to your PostgreSQL server
3. Right-click "Databases" → "Create" → "Database..."
4. Enter "tiffin_times" as database name
5. Click "Save"

**Apply Migrations (All Platforms)**
```bash
# Run from server directory with activated venv
alembic upgrade head
```

### 4. Frontend Setup

```bash
# Navigate to client directory
cd ../client

# Install dependencies
npm install

# Start development server
npm run dev
```

### 5. Start the Backend

```bash
# In the server directory
cd ../server
python -m app.main
```

### 6. Run Initial Data Scrape

```bash
# Navigate to root directory first
cd ..

# Scrape recent logs (ensure your virtual environment is activated)
python scripts/run_scraper.py --days 7

# Geocode addresses
python scripts/run_scraper.py --geocode-only
```

## Usage

### Web Interface

1. Open http://localhost:3000 in your browser
2. Use the sidebar to filter logs by date, agency, or call type
3. Click on markers or list items to view detailed information
4. Use pagination to browse through large datasets

### API Endpoints

- `GET /api/v1/health` - Health check
- `GET /api/v1/logs` - Get logs with filtering and pagination
- `GET /api/v1/logs/{id}` - Get specific log details
- `POST /api/v1/logs/refresh` - Trigger cache refresh

### Scraper Commands

```bash
# Scrape last 7 days (run from root directory)
python scripts/run_scraper.py

# Scrape specific date
python scripts/run_scraper.py --date 2025-01-28

# Scrape date range
python scripts/run_scraper.py --start-date 2025-01-01 --end-date 2025-01-31

# Only geocode existing logs
python scripts/run_scraper.py --geocode-only --geocode-limit 100
```

## Configuration

### Environment Variables

Key environment variables (see `.env.example`):

- `DATABASE_*`: PostgreSQL connection settings
- `REDIS_URL`: Redis connection URL
- `API_HOST/API_PORT`: API server configuration
- `GEOCODING_SERVICE`: Geocoding service (default: nominatim)

### Caching

- Default cache TTL: 1 hour
- Cache keys are automatically invalidated when data is updated
- Use `POST /api/v1/logs/refresh` to manually clear cache

## Development

### Running Tests

```bash
# Backend tests
cd server
pytest

# Frontend tests
cd client
npm test
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Code Quality

```bash
# Frontend linting
cd client
npm run lint

# Backend linting (install black, flake8)
cd server
black .
flake8 .
```

## Troubleshooting

### Windows-Specific Issues

**PostgreSQL Commands Not Found**
```bash
# If createdb or psql commands are not found, add PostgreSQL to PATH:
# 1. Find your PostgreSQL installation (usually in Program Files)
# 2. Add the 'bin' directory to your system PATH
# Example path: C:\Program Files\PostgreSQL\15\bin

# Or use full path directly:
"C:\Program Files\PostgreSQL\15\bin\createdb.exe" tiffin_times
"C:\Program Files\PostgreSQL\15\bin\psql.exe" -U postgres
```

**PowerShell Execution Policy**
```powershell
# If you get execution policy errors when activating venv:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Then try activating again:
venv\Scripts\Activate.ps1
```

**Python Virtual Environment Issues**
```bash
# If venv activation fails, try:
python -m venv --clear venv
# Or use virtualenv instead:
pip install virtualenv
virtualenv venv
```

**Port Already in Use**
```bash
# If ports 3000 or 8000 are in use, modify:
# For frontend (client/vite.config.ts): change port: 3000
# For backend (server/.env): change API_PORT=8000
```

### Common Issues (All Platforms)

**Database Connection Failed**
1. Verify PostgreSQL is running
2. Check database credentials in `.env`
3. Ensure database `tiffin_times` exists
4. Test connection: `psql -U your_user -d tiffin_times`

**Redis Connection Failed**
1. **Quick Fix (Docker)**: `docker run -d -p 6379:6379 --name redis redis:7-alpine`
2. **Alternative**: Install Redis natively on Windows
3. Verify Redis URL in `.env` (should be `redis://localhost:6379`)
4. Test connection: `redis-cli ping` or `docker exec -it redis redis-cli ping`

**Migration Errors**
```bash
# Reset migrations if needed:
alembic downgrade base
alembic upgrade head
```

**Frontend Build Errors**
```bash
# Clear node modules and reinstall:
rm -rf node_modules package-lock.json  # Linux/Mac
rmdir /s node_modules & del package-lock.json  # Windows
npm install
```

## Deployment

### Docker (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Manual Deployment

1. Set up production database and Redis
2. Configure production environment variables
3. Build frontend: `npm run build`
4. Deploy static files to CDN/S3
5. Deploy API to cloud service (AWS ECS, Google Cloud Run, etc.)
6. Set up scheduled scraper task

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Acknowledgments

- JECC for providing public access to emergency call logs
- OpenStreetMap/Nominatim for geocoding services
- The open-source community for the excellent tools and libraries