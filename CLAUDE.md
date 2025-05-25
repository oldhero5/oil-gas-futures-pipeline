# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An automated oil & gas futures data pipeline and analysis system with advanced options pricing capabilities. The system ingests data from Yahoo Finance and Alpha Vantage, stores it in DuckDB, and provides analytical capabilities including Black-Scholes options pricing and Greeks calculations.

## Development Commands

```bash
# Environment setup
uv sync                                    # Install all dependencies

# Run application
uv run python main.py                      # Run main pipeline
uv run uvicorn src.api.main:app --reload   # Run FastAPI server

# Testing
uv run pytest                              # Run all tests
uv run pytest --cov                        # Run tests with coverage
uv run pytest tests/unit/                  # Run unit tests only

# Code quality
uv run black .                             # Format code
uv run mypy .                              # Type checking
uv run isort .                             # Sort imports

# Database
uv run python scripts/setup_db.py          # Initialize database schema
uv run python scripts/backfill.py          # Backfill historical data
```

## Architecture

### Data Flow
1. **Ingestion**: APIs (Yahoo Finance, Alpha Vantage) → Validators → Raw data buffer
2. **Storage**: Structured data → DuckDB analytical database
3. **Analytics**: DuckDB → Options pricing models → Greeks calculations
4. **Access**: Results → FastAPI endpoints → Users

### Key Components
- `src/ingestion/`: Data source connectors with rate limiting
- `src/storage/`: DuckDB schema and operations
- `src/analytics/options_pricing/`: Black-Scholes and binomial models
- `src/api/`: FastAPI REST endpoints
- `src/scheduler/`: APScheduler for automated updates

## Critical Development Rules

1. **Package Management**: ALWAYS use `uv add <package>` (never pip install)
2. **Type Hints**: Mandatory for all functions with proper return types
3. **Error Handling**: Use specific exceptions, log all errors with context
4. **API Keys**: Store in environment variables only, never commit
5. **Testing**: Minimum 80% coverage, mock all external API calls

## DuckDB Schema

Key tables:
- `futures_contracts`: Contract specifications
- `futures_prices`: Historical and real-time prices
- `options_contracts`: Option contract details
- `implied_volatility`: Calculated IV surface
- `greeks`: Computed Greeks values

## Performance Considerations

- Process large datasets in chunks to manage memory
- Use DuckDB's analytical capabilities for aggregations
- Implement caching for frequently accessed data
- Monitor query execution plans for optimization

## Current Implementation Status

The project structure is initialized but core implementation is pending. When implementing:
1. Start with database schema setup (`scripts/setup_db.py`)
2. Implement Yahoo Finance connector first (free tier)
3. Build data validation before storage operations
4. Add options pricing models after data pipeline is stable
