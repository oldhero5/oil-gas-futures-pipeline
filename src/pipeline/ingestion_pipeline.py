"""Main data ingestion pipeline for futures and options data."""

from datetime import UTC, datetime, timedelta

import pandas as pd
from structlog import get_logger

from src.analytics import ImpliedVolatilitySolver
from src.ingestion import YahooFinanceConnector
from src.pipeline.models import FuturesContract, ImpliedVolatility
from src.storage import DatabaseOperations

logger = get_logger()


class DataIngestionPipeline:
    """Main pipeline for ingesting and processing futures data."""

    def __init__(self, db_path: str = "data/futures_analysis.db") -> None:
        """Initialize the data ingestion pipeline.

        Args:
            db_path: Path to the DuckDB database
        """
        self.yf_connector = YahooFinanceConnector()
        self.db_ops = DatabaseOperations(db_path)
        self.iv_solver = ImpliedVolatilitySolver()

    def ingest_futures_data(
        self,
        commodity_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        period: str | None = None,
    ) -> int:
        """Ingest futures price data for a commodity.

        Args:
            commodity_id: Commodity identifier (WTI, NG)
            start_date: Start date for historical data
            end_date: End date for historical data
            period: Alternative to date range (e.g., "1mo", "3mo", "1y")

        Returns:
            Number of records processed
        """
        try:
            logger.info(
                "Starting futures data ingestion",
                commodity=commodity_id,
                start_date=start_date,
                end_date=end_date,
                period=period,
            )

            # Fetch futures data
            df = self.yf_connector.fetch_futures_prices(commodity_id, start_date, end_date, period)

            if df.empty:
                logger.warning("No futures data retrieved", commodity=commodity_id)
                return 0

            # Create contract record
            contract_id = f"{commodity_id}_FRONT"
            expiration_date = datetime.now(tz=UTC).date() + timedelta(days=30)  # Simplified

            contract = FuturesContract(
                contract_id=contract_id,
                commodity_id=commodity_id,
                symbol=df["symbol"].iloc[0],
                expiration_date=expiration_date,
                is_active=True,
            )

            # Store contract
            self.db_ops.upsert_futures_contract(contract)

            # Prepare price data
            df["contract_id"] = contract_id

            # Store prices
            records_inserted = self.db_ops.bulk_insert_futures_prices(df)

            # Log ingestion
            self.db_ops.log_market_data_ingestion(
                data_source="Yahoo Finance",
                commodity_id=commodity_id,
                start_date=df["price_date"].min(),
                end_date=df["price_date"].max(),
                records_processed=records_inserted,
                status="SUCCESS",
            )

            logger.info(
                "Futures data ingestion completed", commodity=commodity_id, records=records_inserted
            )

            return records_inserted

        except Exception as e:
            logger.error("Failed to ingest futures data", commodity=commodity_id, error=str(e))

            # Log failure
            self.db_ops.log_market_data_ingestion(
                data_source="Yahoo Finance",
                commodity_id=commodity_id,
                start_date=start_date,
                end_date=end_date,
                records_processed=0,
                status="FAILED",
                error_message=str(e),
            )

            raise

    def ingest_options_data(self, commodity_id: str) -> int:
        """Ingest options chain data and calculate implied volatility.

        Args:
            commodity_id: Commodity identifier (WTI, NG)

        Returns:
            Number of options processed
        """
        try:
            logger.info("Starting options data ingestion", commodity=commodity_id)

            # Fetch options chain
            options_df = self.yf_connector.fetch_options_chain(commodity_id)

            if options_df.empty:
                logger.warning("No options data retrieved", commodity=commodity_id)
                return 0

            # Get the front month futures contract
            contracts_df = self.db_ops.get_active_contracts(commodity_id)
            if contracts_df.empty:
                logger.error("No active futures contract found", commodity=commodity_id)
                return 0

            underlying_contract_id = contracts_df.iloc[0]["contract_id"]

            # Get latest futures price
            prices_df = self.db_ops.get_futures_prices(
                contract_id=underlying_contract_id,
                start_date=datetime.now(tz=UTC).date() - timedelta(days=1),
            )

            if prices_df.empty:
                logger.error("No recent futures price found")
                return 0

            underlying_price = float(prices_df.iloc[0]["close_price"])
            price_date = prices_df.iloc[0]["price_date"]

            records_processed = 0

            # Process each option
            for _, option in options_df.iterrows():
                try:
                    # Create option contract
                    option_id = f"{commodity_id}_{option['option_type']}_{option['strike_price']}_{option['expiration_date']}"

                    from src.pipeline.models import OptionContract

                    opt_contract = OptionContract(
                        option_id=option_id,
                        underlying_contract_id=underlying_contract_id,
                        option_type=option["option_type"],
                        strike_price=option["strike_price"],
                        expiration_date=pd.to_datetime(option["expiration_date"]).date(),
                        exercise_style="AMERICAN",
                    )

                    self.db_ops.upsert_option_contract(opt_contract)

                    # Store option price
                    option_price_data = pd.DataFrame(
                        [
                            {
                                "option_id": option_id,
                                "price_date": price_date,
                                "bid_price": option.get("bid_price"),
                                "ask_price": option.get("ask_price"),
                                "last_price": option.get("last_price"),
                                "volume": option.get("volume"),
                                "open_interest": option.get("open_interest"),
                            }
                        ]
                    )

                    self.db_ops.bulk_insert_option_prices(option_price_data)

                    # Calculate implied volatility if we have a price
                    if pd.notna(option.get("last_price")) and option["last_price"] > 0:
                        # Calculate time to expiration
                        days_to_exp = (opt_contract.expiration_date - price_date).days
                        T = days_to_exp / 365.0

                        if T > 0:
                            iv = self.iv_solver.calculate_iv(
                                option_price=float(option["last_price"]),
                                S=underlying_price,
                                K=float(option["strike_price"]),
                                r=0.05,  # Risk-free rate
                                T=T,
                                option_type=option["option_type"],
                            )

                            if iv is not None:
                                iv_record = ImpliedVolatility(
                                    option_id=option_id,
                                    price_date=price_date,
                                    implied_vol=iv,
                                    underlying_price=underlying_price,
                                    risk_free_rate=0.05,
                                    calculation_method="BLACK_SCHOLES",
                                )

                                self.db_ops.insert_implied_volatility(iv_record)

                    records_processed += 1

                except Exception as e:
                    logger.error("Failed to process option", option_id=option_id, error=str(e))
                    continue

            logger.info(
                "Options data ingestion completed",
                commodity=commodity_id,
                records=records_processed,
            )

            return records_processed

        except Exception as e:
            logger.error("Failed to ingest options data", commodity=commodity_id, error=str(e))
            raise

    def run_full_pipeline(self, commodities: list[str] = None, period: str = "1mo") -> dict:
        """Run the full data ingestion pipeline.

        Args:
            commodities: List of commodity IDs to process
            period: Period for historical data

        Returns:
            Dictionary with ingestion statistics
        """
        if commodities is None:
            commodities = ["WTI", "NG"]

        stats = {}

        for commodity in commodities:
            logger.info("Processing commodity", commodity=commodity)

            try:
                # Ingest futures data
                futures_records = self.ingest_futures_data(commodity_id=commodity, period=period)

                # Ingest options data
                options_records = self.ingest_options_data(commodity_id=commodity)

                stats[commodity] = {
                    "futures_records": futures_records,
                    "options_records": options_records,
                    "status": "SUCCESS",
                }

            except Exception as e:
                logger.error("Failed to process commodity", commodity=commodity, error=str(e))
                stats[commodity] = {
                    "futures_records": 0,
                    "options_records": 0,
                    "status": "FAILED",
                    "error": str(e),
                }

        return stats

    def close(self) -> None:
        """Close database connection."""
        self.db_ops.close()
