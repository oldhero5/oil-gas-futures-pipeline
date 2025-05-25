#!/usr/bin/env python3
"""Main CLI interface for the oil & gas futures pipeline."""

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from structlog import get_logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline.ingestion_pipeline import DataIngestionPipeline
from src.storage import DatabaseManager

logger = get_logger()


def setup_database(args):
    """Initialize the database schema."""
    logger.info("Setting up database schema...")

    from scripts.setup_db import setup_database as run_setup

    try:
        run_setup(args.db_path)
        print("✓ Database schema created successfully")
    except Exception as e:
        print(f"✗ Failed to create database schema: {e}")
        sys.exit(1)


def ingest_data(args):
    """Run data ingestion pipeline."""
    logger.info("Starting data ingestion", commodities=args.commodities, period=args.period)

    # Check database health
    db_manager = DatabaseManager(args.db_path)
    if not db_manager.health_check():
        print("✗ Database is not properly initialized. Run 'setup-db' first.")
        sys.exit(1)

    # Run pipeline
    pipeline = DataIngestionPipeline(args.db_path)

    try:
        stats = pipeline.run_full_pipeline(commodities=args.commodities, period=args.period)

        # Print results
        print("\n📊 Ingestion Results:")
        print("=" * 50)

        for commodity, result in stats.items():
            status_icon = "✓" if result["status"] == "SUCCESS" else "✗"
            print(f"\n{status_icon} {commodity}:")
            print(f"  - Futures records: {result['futures_records']}")
            print(f"  - Options records: {result['options_records']}")

            if result["status"] == "FAILED":
                print(f"  - Error: {result.get('error', 'Unknown error')}")

        print("\n" + "=" * 50)

        # Overall status
        all_success = all(r["status"] == "SUCCESS" for r in stats.values())
        if all_success:
            print("✓ All commodities processed successfully")
        else:
            print("⚠️ Some commodities failed to process")
            sys.exit(1)

    except Exception as e:
        logger.error("Pipeline failed", error=str(e))
        print(f"\n✗ Pipeline failed: {e}")
        sys.exit(1)
    finally:
        pipeline.close()


def query_data(args):
    """Query stored data."""

    try:
        if args.query_type == "prices":
            # Query futures prices
            from src.storage import DatabaseOperations

            with DatabaseOperations(args.db_path) as db_ops:
                df = db_ops.get_futures_prices(
                    commodity_id=args.commodity, start_date=args.start_date, end_date=args.end_date
                )

                if df.empty:
                    print("No data found for the specified criteria")
                else:
                    print(f"\n📊 Futures Prices for {args.commodity or 'All Commodities'}:")
                    print("=" * 70)
                    print(df.to_string(index=False, max_rows=args.limit))
                    print(f"\nTotal records: {len(df)}")

        elif args.query_type == "volatility":
            # Query implied volatility
            from src.storage import DatabaseOperations

            with DatabaseOperations(args.db_path) as db_ops:
                if not args.date:
                    args.date = datetime.now(tz=UTC).date()

                df = db_ops.get_implied_volatility_surface(
                    commodity_id=args.commodity, price_date=args.date
                )

                if df.empty:
                    print(f"No volatility data found for {args.commodity} on {args.date}")
                else:
                    print(f"\n📊 Implied Volatility Surface for {args.commodity} on {args.date}:")
                    print("=" * 70)
                    print(df.to_string(index=False))

    except Exception as e:
        print(f"✗ Query failed: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Oil & Gas Futures Analysis Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Setup database
  %(prog)s setup-db

  # Ingest data for all commodities (1 month)
  %(prog)s ingest

  # Ingest specific commodity with custom period
  %(prog)s ingest --commodities WTI --period 3mo

  # Query futures prices
  %(prog)s query prices --commodity WTI --limit 10

  # Query implied volatility surface
  %(prog)s query volatility --commodity WTI --date 2024-01-25
        """,
    )

    parser.add_argument(
        "--db-path", default="data/futures_analysis.db", help="Path to DuckDB database file"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Setup database command
    subparsers.add_parser("setup-db", help="Initialize database schema")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Run data ingestion pipeline")
    ingest_parser.add_argument(
        "--commodities",
        nargs="+",
        choices=["WTI", "NG"],
        default=["WTI", "NG"],
        help="Commodities to ingest",
    )
    ingest_parser.add_argument(
        "--period",
        default="1mo",
        choices=["1d", "5d", "1mo", "3mo", "6mo", "1y"],
        help="Period for historical data",
    )

    # Query command
    query_parser = subparsers.add_parser("query", help="Query stored data")
    query_subparsers = query_parser.add_subparsers(dest="query_type", help="Query type")

    # Query prices
    prices_parser = query_subparsers.add_parser("prices", help="Query futures prices")
    prices_parser.add_argument("--commodity", choices=["WTI", "NG"], help="Filter by commodity")
    prices_parser.add_argument(
        "--start-date", type=lambda s: datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=UTC).date()
    )
    prices_parser.add_argument(
        "--end-date", type=lambda s: datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=UTC).date()
    )
    prices_parser.add_argument("--limit", type=int, default=20, help="Limit number of results")

    # Query volatility
    vol_parser = query_subparsers.add_parser("volatility", help="Query implied volatility")
    vol_parser.add_argument("--commodity", required=True, choices=["WTI", "NG"])
    vol_parser.add_argument(
        "--date", type=lambda s: datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=UTC).date()
    )

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == "setup-db":
        setup_database(args)
    elif args.command == "ingest":
        ingest_data(args)
    elif args.command == "query":
        if not args.query_type:
            query_parser.print_help()
            sys.exit(1)
        query_data(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
