# Oil & Gas Futures Analysis Pipeline

A comprehensive system for ingesting, storing, and analyzing oil and gas futures data with advanced options pricing capabilities.

## Features

- **Data Ingestion**: Automated fetching of WTI crude oil and natural gas futures data from Yahoo Finance
- **DuckDB Storage**: Efficient analytical database for time-series data
- **Options Pricing**: Black-Scholes model implementation for European options
- **Implied Volatility**: Newton-Raphson and bisection methods for IV calculation
- **CLI Interface**: Easy-to-use command-line interface for all operations

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd oil-gas-futures-pipeline

# Install dependencies using uv
uv sync
```

## Quick Start

1. **Initialize the database:**
   ```bash
   uv run python main.py setup-db
   ```

2. **Ingest futures and options data:**
   ```bash
   # Ingest data for all commodities (1 month history)
   uv run python main.py ingest

   # Ingest specific commodity with custom period
   uv run python main.py ingest --commodities WTI --period 3mo
   ```

3. **Query the data:**
   ```bash
   # Query futures prices
   uv run python main.py query prices --commodity WTI --limit 10

   # Query implied volatility surface
   uv run python main.py query volatility --commodity WTI
   ```

## Architecture

### Components

- **Data Ingestion Layer** (`src/ingestion/`)
  - Yahoo Finance connector with rate limiting
  - Data validation and transformation

- **Storage Layer** (`src/storage/`)
  - DuckDB schema management
  - CRUD operations for futures and options data

- **Analytics Engine** (`src/analytics/`)
  - Black-Scholes option pricing model
  - Greeks calculations (Delta, Gamma, Theta, Vega, Rho)
  - Implied volatility solver

- **Pipeline** (`src/pipeline/`)
  - Orchestrates data flow from ingestion to storage
  - Handles error recovery and logging

### Database Schema

Key tables:
- `commodities`: Reference data for WTI and Natural Gas
- `futures_contracts`: Contract specifications
- `futures_prices`: Historical price data
- `options_contracts`: Option contract details
- `implied_volatility`: Calculated IV values
- `greeks`: Option Greeks calculations

## Testing

Run the test suite:
```bash
uv run pytest
```

## Configuration

The system uses sensible defaults but can be configured via command-line arguments:
- `--db-path`: Custom database file location
- `--period`: Historical data period (1d, 5d, 1mo, 3mo, 6mo, 1y)
- `--commodities`: Specific commodities to process (WTI, NG)

## Development

Follow the development guidelines in CLAUDE.md:
- Use `uv` for all package management
- Maintain type hints for all functions
- Handle errors gracefully with proper logging
- Write tests for new functionality

## Limitations

- Currently supports only Yahoo Finance data (free tier)
- Options data availability depends on Yahoo Finance coverage
- Simplified contract expiration logic (production systems need proper futures calendar)
- Black-Scholes assumes European-style options (while most commodity options are American)

## Future Enhancements

- Support for additional data sources (Alpha Vantage, CME Group)
- American option pricing models (binomial tree)
- Volatility surface fitting and interpolation
- Real-time data streaming capabilities
- Web API for programmatic access
