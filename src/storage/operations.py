"""Database operations for storing and retrieving futures data."""

from datetime import date

import duckdb
import pandas as pd
from pydantic import ValidationError
from structlog import get_logger

from src.core.validators import FuturesContractValidator, FuturesPriceValidator
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
        """Insert or update a futures contract after validation."""
        try:
            contract_data = contract.model_dump()
            contract_data.setdefault("created_at", None)
            contract_data.setdefault("updated_at", None)
            validated_contract = FuturesContractValidator(**contract_data)
        except ValidationError as e:
            logger.error(
                "FuturesContract validation failed",
                contract_id=contract.contract_id,
                errors=e.errors(),
            )
            raise

        query = """
            INSERT INTO futures_contracts
            (contract_id, commodity_id, symbol, expiration_date,
             first_trade_date, last_trade_date, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (contract_id) DO UPDATE SET
                is_active = EXCLUDED.is_active,
                updated_at = get_current_timestamp()
        """

        self.conn.execute(
            query,
            [
                validated_contract.contract_id,
                validated_contract.commodity_id,
                validated_contract.symbol,
                validated_contract.expiration_date,
                validated_contract.first_trade_date,
                validated_contract.last_trade_date,
                validated_contract.is_active,
            ],
        )

        logger.info("Upserted futures contract", contract_id=validated_contract.contract_id)

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
        """Bulk insert futures prices after validation."""
        required_columns = ["contract_id", "price_date", "close_price"]
        if not all(col in prices_df.columns for col in required_columns):
            logger.error(
                "DataFrame for bulk_insert_futures_prices missing required columns",
                required=required_columns,
                actual=prices_df.columns.tolist(),
            )
            raise ValueError(f"DataFrame must contain columns: {required_columns}")

        insert_df = prices_df.copy()
        expected_validator_cols = FuturesPriceValidator.model_fields.keys()
        for col in expected_validator_cols:
            if col not in insert_df.columns:
                insert_df[col] = None

        cols_for_validation = [col for col in expected_validator_cols if col in insert_df.columns]
        records_to_validate = insert_df[cols_for_validation].to_dict(orient="records")

        valid_records = []
        invalid_count = 0
        for record in records_to_validate:
            try:
                record.setdefault("created_at", None)
                validated_record = FuturesPriceValidator(**record)
                valid_records.append(validated_record.model_dump(exclude_none=True))
            except ValidationError as e:
                logger.warning(
                    "FuturesPrice validation failed for a record",
                    contract_id=record.get("contract_id"),
                    price_date=record.get("price_date"),
                    errors=e.errors(),
                )
                invalid_count += 1

        if invalid_count > 0:
            logger.info(
                "Some futures price records failed validation",
                invalid_count=invalid_count,
                total_attempted=len(records_to_validate),
            )

        if not valid_records:
            logger.info("No valid futures price records to insert after validation.")
            return 0

        validated_df = pd.DataFrame(valid_records)

        db_insert_cols = [
            "contract_id",
            "price_date",
            "price_time",
            "open_price",
            "high_price",
            "low_price",
            "close_price",
            "settlement_price",
            "volume",
            "open_interest",
        ]
        for col in db_insert_cols:
            if col not in validated_df.columns:
                validated_df[col] = None

        temp_table_name = f"temp_futures_prices_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S%f')}"
        self.conn.register(temp_table_name, validated_df[db_insert_cols])

        query = f"""
            INSERT INTO futures_prices
            (contract_id, price_date, price_time, open_price, high_price,
             low_price, close_price, settlement_price, volume, open_interest)
            SELECT contract_id, price_date, price_time, open_price, high_price,
                   low_price, close_price, settlement_price, volume, open_interest
            FROM {temp_table_name}
            ON CONFLICT (contract_id, price_date) DO UPDATE SET
                open_price = EXCLUDED.open_price,
                high_price = EXCLUDED.high_price,
                low_price = EXCLUDED.low_price,
                close_price = EXCLUDED.close_price,
                settlement_price = EXCLUDED.settlement_price,
                volume = EXCLUDED.volume,
                open_interest = EXCLUDED.open_interest
        """

        try:
            cursor = self.conn.execute(query)
            records_inserted = cursor.rowcount if cursor.rowcount != -1 else len(validated_df)
            logger.info(
                "Bulk inserted/updated futures prices",
                records_processed=records_inserted,
                valid_records=len(valid_records),
            )
        except Exception as e:
            logger.error("Failed during bulk insert of futures prices", error=str(e))
            raise
        finally:
            self.conn.unregister(temp_table_name)

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
                float(iv.risk_free_rate) if iv.risk_free_rate else 0.05,
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
