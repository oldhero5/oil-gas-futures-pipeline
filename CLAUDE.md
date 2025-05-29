# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An automated oil & gas futures data pipeline and analysis system with advanced options pricing capabilities. The system ingests data from Yahoo Finance and Alpha Vantage, stores it in DuckDB, and provides analytical capabilities including Black-Scholes options pricing and Greeks calculations.

**Current Status: ~85% Complete - Production Ready**

## Development Commands

```bash
# Environment setup
uv sync                                    # Install all dependencies

# Database setup
uv run python scripts/setup_db.py          # Initialize database schema

# Run application
uv run python main.py                      # Run CLI pipeline
uv run uvicorn src.api.main:app --reload   # Run FastAPI server (port 8000)

# Docker deployment (recommended)
docker-compose up --build                  # Start all services
docker-compose down                        # Stop all services

# Testing
uv run pytest                              # Run all tests
uv run pytest --cov                        # Run tests with coverage
uv run pytest tests/test_api_*.py          # Run API tests only

# Code quality
uv run ruff check --fix .                  # Format and lint code
uv run mypy .                              # Type checking

# Data operations
uv run python main.py ingest --symbol CL   # Ingest WTI crude data
uv run python main.py ingest --symbol NG   # Ingest natural gas data
uv run python main.py query prices --symbol CL --limit 10  # Query prices
```

## Architecture

### Data Flow
1. **Ingestion**: APIs (Yahoo Finance, Alpha Vantage) → Validators → Raw data buffer
2. **Storage**: Structured data → DuckDB analytical database
3. **Analytics**: DuckDB → Options pricing models → Greeks calculations
4. **Access**: Results → FastAPI REST endpoints → Next.js frontend

### Key Components
- `src/ingestion/`: Data source connectors with rate limiting ✅
- `src/storage/`: DuckDB schema and operations ✅
- `src/analytics/options_pricing/`: Black-Scholes and implied volatility models ✅
- `src/api/`: Complete FastAPI REST endpoints with authentication ✅
- `frontend/`: Next.js dashboard with React components ✅
- `docker/`: Multi-container deployment setup ✅

## Critical Development Rules

1. **Package Management**: ALWAYS use `uv add <package>` (never pip install)
2. **Type Hints**: Mandatory for all functions with proper return types
3. **Error Handling**: Use specific exceptions, log all errors with context
4. **API Keys**: Store in environment variables only, never commit
5. **Testing**: Minimum 80% coverage achieved, mock all external API calls
6. **Authentication**: All API endpoints use JWT tokens with bcrypt password hashing
7. **Code Quality**: Pre-commit hooks enforce ruff formatting and linting

## API Endpoints (Fully Implemented)

### Authentication (`/api/auth/`)
- `POST /register` - User registration with email/password
- `POST /login` - User authentication, returns JWT token
- `GET /me` - Get current user profile
- `POST /logout` - Logout (client-side token disposal)
- `POST /refresh` - Refresh JWT token

### Futures Data (`/api/futures/`)
- `GET /contracts` - List futures contracts with filters
- `GET /prices` - Get futures prices with date/commodity filters
- `GET /prices/{commodity_id}/latest` - Latest price with daily change
- `POST /prices/{commodity_id}/historical` - Historical price data

### Options Analytics (`/api/options/`)
- `POST /calculate` - Black-Scholes option pricing (calls/puts)
- `POST /greeks` - Calculate all Greeks (delta, gamma, theta, vega, rho)
- `POST /implied-volatility` - Newton-Raphson IV solver
- `GET /volatility/surface/{commodity_id}` - Volatility surface data

### User Management (`/api/users/`) - Admin Only
- `GET /` - List all users with pagination
- `GET /{user_id}` - Get specific user details
- `PUT /{user_id}` - Update user (role, status, profile)
- `DELETE /{user_id}` - Delete user account

### System Monitoring (`/api/system/`)
- `GET /status` - API and database health checks
- `GET /metrics` - Commodity metrics and key performance indicators

## DuckDB Schema (Complete)

**Core Tables:**
- `commodities`: Reference data (WTI, NG symbols)
- `futures_contracts`: Contract specifications with expiration dates
- `futures_prices`: OHLCV data with volume and open interest
- `options_contracts`: Option contract definitions
- `options_prices`: Bid/ask/last prices for options
- `implied_volatility`: Calculated IV surface points
- `greeks`: Computed Greeks values
- `market_data_log`: Ingestion audit trail

**User Management Tables:**
- `users`: User accounts with roles (admin, editor, viewer)
- `user_sessions`: JWT token management
- `user_audit_log`: Security audit trail

## Frontend Components (Complete)

**Authentication:**
- Login/logout pages with form validation
- JWT token management and refresh
- Protected route wrapper for authenticated pages

**Dashboard Pages:**
- Overview with key metrics and system status
- Futures price grids with real-time updates
- Options analytics with Greeks calculations
- Historical charts and trend analysis
- Admin user management interface

**Technical Stack:**
- Next.js 15 with App Router
- React 19 with TypeScript
- Tailwind CSS for styling
- Recharts for data visualization

## Performance Considerations

- **Database**: DuckDB analytical queries optimized with proper indexing
- **API**: Response caching with Redis (configured in Docker)
- **Frontend**: Code splitting and lazy loading implemented
- **Memory**: Large datasets processed in chunks
- **Concurrency**: FastAPI async/await for non-blocking operations

## Current Implementation Status ✅

**✅ Completed (100%):**
1. Database schema with user management and audit trails
2. Yahoo Finance data connector with error handling
3. Black-Scholes options pricing with full Greeks suite
4. Implied volatility solver (Newton-Raphson + bisection fallback)
5. Complete FastAPI REST API with JWT authentication
6. Next.js frontend with responsive dashboard
7. Docker multi-container deployment
8. Comprehensive test suite (80%+ coverage)
9. Code quality tools (ruff, mypy, pre-commit hooks)

**🚧 In Progress (0%):**
- Alpha Vantage integration (Yahoo Finance working well)
- WebSocket real-time updates (HTTP polling sufficient for now)
- Advanced portfolio analytics (basic metrics implemented)

**📋 Documentation Status:**
- API documentation available at `/api/docs` (ReDoc)
- CLI help available with `--help` flag
- README with complete setup instructions
- Architecture diagrams and deployment guides

## Security Implementation

**Authentication & Authorization:**
- JWT tokens with configurable expiration (default 30 minutes)
- bcrypt password hashing with salt
- Role-based access control (admin, editor, viewer)
- Input validation on all API endpoints
- SQL injection protection via parameterized queries

**Infrastructure Security:**
- Docker containers run as non-root users
- Environment variables for sensitive configuration
- CORS properly configured for frontend integration
- API rate limiting and error handling

## Production Deployment

**Docker Services:**
- `backend`: FastAPI application (port 8000)
- `frontend`: Next.js application (port 3000)
- `redis`: Session and response caching (port 6379)
- `nginx`: Reverse proxy and load balancer (port 80)

**Environment Variables:**
```bash
# Required for production
JWT_SECRET_KEY=your-super-secret-key
ALPHA_VANTAGE_API_KEY=your-api-key  # Optional
DATABASE_PATH=./data/futures_analysis.db
REDIS_URL=redis://redis:6379
```

**Health Checks:**
- API: `GET /health` returns service status
- System: `GET /api/system/status` returns comprehensive health
- Database: Connection validation on each request
- Frontend: Standard Next.js health indicators

## Known Limitations

1. **Data Sources**: Currently Yahoo Finance only (Alpha Vantage planned)
2. **Real-time Updates**: HTTP polling (WebSocket planned for v2)
3. **Data Frequency**: Daily data only (intraday planned)
4. **Options Data**: Theoretical pricing only (no market options data)
5. **Scalability**: Single-node deployment (clustering planned)

## Development Workflow

1. **Feature Development**: Create feature branch from main
2. **Testing**: Ensure tests pass and coverage remains >80%
3. **Code Quality**: Pre-commit hooks validate formatting/linting
4. **API Changes**: Update OpenAPI docs and test coverage
5. **Frontend Changes**: Verify responsive design and accessibility
6. **Deployment**: Test in Docker environment before production

## Troubleshooting

**Common Issues:**
- Database not found: Run `uv run python scripts/setup_db.py`
- Import errors: Ensure `uv sync` completed successfully
- Docker build fails: Check Docker daemon is running
- API 500 errors: Check logs and database connectivity
- Frontend build errors: Verify Node.js 18+ and clean `node_modules`

**Debug Commands:**
```bash
# Check database status
uv run python -c "from src.storage.operations import DatabaseOperations; print('DB OK')"

# Validate API health
curl http://localhost:8000/health

# Check frontend build
cd frontend && npm run build
```
