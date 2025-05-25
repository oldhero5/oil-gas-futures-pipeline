"""Database operations for storing and retrieving futures data."""

from datetime import date

import duckdb
import pandas as pd
from structlog import get_logger

from src.pipeline.models import FuturesContract, ImpliedVolatility, OptionContract

logger = get_logger()


class DatabaseOperations:
    """Handle database operations for futures and options data."""

    def __init__(self, db_path: str = "data/futures_analysis.db") -> None:
        """Initialize database connection."""
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        logger.info("Connected to database", db_path=db_path)

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    # Futures Contract Operations
    def upsert_futures_contract(self, contract: FuturesContract) -> None:
        """Insert or update a futures contract."""
        query = """
            INSERT INTO futures_contracts
            (contract_id, commodity_id, symbol, expiration_date,
             first_trade_date, last_trade_date, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (contract_id) DO UPDATE SET
                commodity_id = EXCLUDED.commodity_id,
                symbol = EXCLUDED.symbol,
                expiration_date = EXCLUDED.expiration_date,
                first_trade_date = EXCLUDED.first_trade_date,
                last_trade_date = EXCLUDED.last_trade_date,
                is_active = EXCLUDED.is_active
        """

        self.conn.execute(
            query,
            [
                contract.contract_id,
                contract.commodity_id,
                contract.symbol,
                contract.expiration_date,
                contract.first_trade_date,
                contract.last_trade_date,
                contract.is_active,
            ],
        )

        logger.info("Upserted futures contract", contract_id=contract.contract_id)

    def get_active_contracts(self, commodity_id: str | None = None) -> pd.DataFrame:
        """Get active futures contracts."""
        query = """
            SELECT * FROM futures_contracts
            WHERE is_active = TRUE
        """
        params = []

        if commodity_id:
            query += " AND commodity_id = ?"
            params.append(commodity_id)

        query += " ORDER BY expiration_date"

        return self.conn.execute(query, params).df()

    # Futures Price Operations
    def bulk_insert_futures_prices(self, prices_df: pd.DataFrame) -> int:
        """Bulk insert futures prices."""
        required_columns = ["contract_id", "price_date", "close_price"]
        if not all(col in prices_df.columns for col in required_columns):
            raise ValueError(f"DataFrame must contain columns: {required_columns}")

        # Prepare data for insertion
        insert_df = prices_df[
            [
                "contract_id",
                "price_date",
                "open_price",
                "high_price",
                "low_price",
                "close_price",
                "volume",
            ]
        ].copy()

        # Handle open_interest if present
        if "open_interest" in prices_df.columns:
            insert_df["open_interest"] = prices_df["open_interest"]
        else:
            insert_df["open_interest"] = None

        # Add price_time if not present
        if "price_time" not in insert_df.columns:
            insert_df["price_time"] = None

        # Add settlement_price if not present
        if "settlement_price" not in insert_df.columns:
            insert_df["settlement_price"] = None

        # Use INSERT with ON CONFLICT to handle duplicates
        query = """
            INSERT INTO futures_prices
            (contract_id, price_date, price_time, open_price, high_price,
             low_price, close_price, settlement_price, volume, open_interest)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (contract_id, price_date) DO UPDATE SET
                open_price = EXCLUDED.open_price,
                high_price = EXCLUDED.high_price,
                low_price = EXCLUDED.low_price,
                close_price = EXCLUDED.close_price,
                settlement_price = EXCLUDED.settlement_price,
                volume = EXCLUDED.volume,
                open_interest = EXCLUDED.open_interest
        """

        records_inserted = 0
        for _, row in insert_df.iterrows():
            try:
                self.conn.execute(
                    query,
                    [
                        row["contract_id"],
                        row["price_date"],
                        row["price_time"],
                        float(row["open_price"]) if pd.notna(row["open_price"]) else None,
                        float(row["high_price"]) if pd.notna(row["high_price"]) else None,
                        float(row["low_price"]) if pd.notna(row["low_price"]) else None,
                        float(row["close_price"]),
                        float(row["settlement_price"])
                        if pd.notna(row["settlement_price"])
                        else None,
                        int(row["volume"]) if pd.notna(row["volume"]) else None,
                        int(row["open_interest"]) if pd.notna(row["open_interest"]) else None,
                    ],
                )
                records_inserted += 1
            except Exception as e:
                logger.error(
                    "Failed to insert price record",
                    contract_id=row["contract_id"],
                    date=row["price_date"],
                    error=str(e),
                )

        logger.info("Bulk inserted futures prices", records=records_inserted)
        return records_inserted

    def get_futures_prices(
        self,
        contract_id: str | None = None,
        commodity_id: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """Get futures prices with optional filters."""
        query = """
            SELECT fp.*, fc.commodity_id, fc.symbol
            FROM futures_prices fp
            JOIN futures_contracts fc ON fp.contract_id = fc.contract_id
            WHERE 1=1
        """
        params = []

        if contract_id:
            query += " AND fp.contract_id = ?"
            params.append(contract_id)

        if commodity_id:
            query += " AND fc.commodity_id = ?"
            params.append(commodity_id)

        if start_date:
            query += " AND fp.price_date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND fp.price_date <= ?"
            params.append(end_date)

        query += " ORDER BY fp.price_date DESC"

        return self.conn.execute(query, params).df()

    # Option Contract Operations
    def upsert_option_contract(self, option: OptionContract) -> None:
        """Insert or update an option contract."""
        query = """
            INSERT INTO options_contracts
            (option_id, underlying_contract_id, option_type, strike_price,
             expiration_date, exercise_style, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (option_id) DO UPDATE SET
                underlying_contract_id = EXCLUDED.underlying_contract_id,
                option_type = EXCLUDED.option_type,
                strike_price = EXCLUDED.strike_price,
                expiration_date = EXCLUDED.expiration_date,
                exercise_style = EXCLUDED.exercise_style,
                is_active = EXCLUDED.is_active
        """

        self.conn.execute(
            query,
            [
                option.option_id,
                option.underlying_contract_id,
                option.option_type,
                float(option.strike_price),
                option.expiration_date,
                option.exercise_style,
                option.is_active,
            ],
        )

        logger.info("Upserted option contract", option_id=option.option_id)

    def bulk_insert_option_prices(self, prices_df: pd.DataFrame) -> int:
        """Bulk insert option prices."""
        required_columns = ["option_id", "price_date"]
        if not all(col in prices_df.columns for col in required_columns):
            raise ValueError(f"DataFrame must contain columns: {required_columns}")

        query = """
            INSERT INTO options_prices
            (option_id, price_date, price_time, bid_price, ask_price,
             last_price, settlement_price, volume, open_interest)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (option_id, price_date) DO UPDATE SET
                bid_price = EXCLUDED.bid_price,
                ask_price = EXCLUDED.ask_price,
                last_price = EXCLUDED.last_price,
                settlement_price = EXCLUDED.settlement_price,
                volume = EXCLUDED.volume,
                open_interest = EXCLUDED.open_interest
        """

        records_inserted = 0
        for _, row in prices_df.iterrows():
            try:
                self.conn.execute(
                    query,
                    [
                        row["option_id"],
                        row["price_date"],
                        row.get("price_time"),
                        float(row["bid_price"]) if pd.notna(row.get("bid_price")) else None,
                        float(row["ask_price"]) if pd.notna(row.get("ask_price")) else None,
                        float(row["last_price"]) if pd.notna(row.get("last_price")) else None,
                        float(row["settlement_price"])
                        if pd.notna(row.get("settlement_price"))
                        else None,
                        int(row["volume"]) if pd.notna(row.get("volume")) else None,
                        int(row["open_interest"]) if pd.notna(row.get("open_interest")) else None,
                    ],
                )
                records_inserted += 1
            except Exception as e:
                logger.error(
                    "Failed to insert option price record",
                    option_id=row["option_id"],
                    date=row["price_date"],
                    error=str(e),
                )

        logger.info("Bulk inserted option prices", records=records_inserted)
        return records_inserted

    # Implied Volatility Operations
    def insert_implied_volatility(self, iv: ImpliedVolatility) -> None:
        """Insert implied volatility calculation."""
        query = """
            INSERT INTO implied_volatility
            (option_id, price_date, implied_vol, underlying_price,
             risk_free_rate, calculation_method)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (option_id, price_date) DO UPDATE SET
                implied_vol = EXCLUDED.implied_vol,
                underlying_price = EXCLUDED.underlying_price,
                risk_free_rate = EXCLUDED.risk_free_rate,
                calculation_method = EXCLUDED.calculation_method
        """

        self.conn.execute(
            query,
            [
                iv.option_id,
                iv.price_date,
                float(iv.implied_vol),
                float(iv.underlying_price),
                float(iv.risk_free_rate)
                if iv.risk_free_rate
                else 0.05,  # Default 5% risk-free rate
                iv.calculation_method,
            ],
        )

        logger.info(
            "Inserted implied volatility",
            option_id=iv.option_id,
            date=iv.price_date,
            iv=float(iv.implied_vol),
        )

    def get_implied_volatility_surface(self, commodity_id: str, price_date: date) -> pd.DataFrame:
        """Get implied volatility surface for a commodity on a specific date."""
        query = """
            SELECT
                oc.strike_price,
                oc.expiration_date,
                oc.option_type,
                iv.implied_vol,
                iv.underlying_price,
                fc.symbol as underlying_symbol
            FROM implied_volatility iv
            JOIN options_contracts oc ON iv.option_id = oc.option_id
            JOIN futures_contracts fc ON oc.underlying_contract_id = fc.contract_id
            WHERE fc.commodity_id = ? AND iv.price_date = ?
            ORDER BY oc.expiration_date, oc.strike_price
        """

        return self.conn.execute(query, [commodity_id, price_date]).df()

    # Market Data Log Operations
    def log_market_data_ingestion(
        self,
        data_source: str,
        commodity_id: str,
        start_date: date | None,
        end_date: date | None,
        records_processed: int,
        status: str = "SUCCESS",
        error_message: str | None = None,
    ) -> None:
        """Log market data ingestion activity."""
        query = """
            INSERT INTO market_data_log
            (data_source, commodity_id, start_date, end_date,
             records_processed, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        self.conn.execute(
            query,
            [
                data_source,
                commodity_id,
                start_date,
                end_date,
                records_processed,
                status,
                error_message,
            ],
        )

        logger.info(
            "Logged market data ingestion",
            source=data_source,
            commodity=commodity_id,
            records=records_processed,
            status=status,
        )
