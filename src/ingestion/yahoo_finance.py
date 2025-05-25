"""Yahoo Finance connector for futures data."""

from datetime import UTC, datetime, timedelta

import pandas as pd
import yfinance as yf
from structlog import get_logger

logger = get_logger()


class YahooFinanceConnector:
    """Connector for fetching futures data from Yahoo Finance."""

    # Mapping of commodity IDs to Yahoo Finance symbols
    SYMBOL_MAPPING = {
        "WTI": "CL=F",  # WTI Crude Oil Futures
        "NG": "NG=F",  # Natural Gas Futures
    }

    def __init__(self) -> None:
        """Initialize the Yahoo Finance connector."""
        self.session = None

    def get_futures_symbol(self, commodity_id: str, month_offset: int = 0) -> str:
        """Get Yahoo Finance symbol for a specific futures contract.

        Args:
            commodity_id: Commodity identifier (WTI, NG)
            month_offset: Number of months ahead (0 for front month)

        Returns:
            Yahoo Finance symbol
        """
        if month_offset == 0:
            return self.SYMBOL_MAPPING.get(commodity_id, "")

        # For specific month contracts, we need to construct the symbol
        # This is simplified - in production, you'd calculate the actual contract codes
        base_symbol = commodity_id
        if base_symbol == "WTI":
            base_symbol = "CL"

        # Yahoo uses format like CLF24 for January 2024 WTI Crude
        # This would need proper month/year calculation in production
        return f"{base_symbol}=F"

    def fetch_futures_prices(
        self,
        commodity_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        period: str | None = None,
    ) -> pd.DataFrame:
        """Fetch futures price data from Yahoo Finance.

        Args:
            commodity_id: Commodity identifier (WTI, NG)
            start_date: Start date for historical data
            end_date: End date for historical data
            period: Alternative to date range (e.g., "1mo", "3mo", "1y")

        Returns:
            DataFrame with price data
        """
        symbol = self.get_futures_symbol(commodity_id)
        if not symbol:
            raise ValueError(f"Unknown commodity: {commodity_id}")

        logger.info(
            "Fetching futures data",
            symbol=symbol,
            commodity=commodity_id,
            start_date=start_date,
            end_date=end_date,
            period=period,
        )

        try:
            ticker = yf.Ticker(symbol)

            if period:
                df = ticker.history(period=period)
            else:
                if not start_date:
                    start_date = datetime.now(tz=UTC) - timedelta(days=365)
                if not end_date:
                    end_date = datetime.now(tz=UTC)

                df = ticker.history(start=start_date, end=end_date)

            if df.empty:
                logger.warning("No data returned", symbol=symbol)
                return pd.DataFrame()

            # Add commodity_id and clean up the data
            df["commodity_id"] = commodity_id
            df["symbol"] = symbol
            df = df.reset_index()
            df = df.rename(
                columns={
                    "Date": "price_date",
                    "Open": "open_price",
                    "High": "high_price",
                    "Low": "low_price",
                    "Close": "close_price",
                    "Volume": "volume",
                }
            )

            logger.info("Fetched futures data successfully", symbol=symbol, records=len(df))

            return df

        except Exception as e:
            logger.error("Failed to fetch futures data", symbol=symbol, error=str(e))
            raise

    def fetch_contract_info(self, commodity_id: str) -> dict:
        """Fetch contract information from Yahoo Finance.

        Args:
            commodity_id: Commodity identifier

        Returns:
            Dictionary with contract information
        """
        symbol = self.get_futures_symbol(commodity_id)
        if not symbol:
            raise ValueError(f"Unknown commodity: {commodity_id}")

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                "symbol": symbol,
                "commodity_id": commodity_id,
                "name": info.get("longName", ""),
                "exchange": info.get("exchange", ""),
                "currency": info.get("currency", "USD"),
                "regular_market_price": info.get("regularMarketPrice"),
                "regular_market_volume": info.get("regularMarketVolume"),
                "bid": info.get("bid"),
                "ask": info.get("ask"),
                "day_high": info.get("dayHigh"),
                "day_low": info.get("dayLow"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            }

        except Exception as e:
            logger.error("Failed to fetch contract info", symbol=symbol, error=str(e))
            raise

    def fetch_options_chain(self, commodity_id: str) -> pd.DataFrame:
        """Fetch options chain data for a futures contract.

        Args:
            commodity_id: Commodity identifier

        Returns:
            DataFrame with options data
        """
        symbol = self.get_futures_symbol(commodity_id)
        if not symbol:
            raise ValueError(f"Unknown commodity: {commodity_id}")

        try:
            ticker = yf.Ticker(symbol)

            # Get available expiration dates
            expirations = ticker.options
            if not expirations:
                logger.warning("No options data available", symbol=symbol)
                return pd.DataFrame()

            all_options = []

            for exp_date in expirations[:3]:  # Limit to first 3 expirations for now
                try:
                    opt_chain = ticker.option_chain(exp_date)

                    # Process calls
                    calls = opt_chain.calls.copy()
                    calls["option_type"] = "CALL"
                    calls["expiration_date"] = exp_date

                    # Process puts
                    puts = opt_chain.puts.copy()
                    puts["option_type"] = "PUT"
                    puts["expiration_date"] = exp_date

                    all_options.extend([calls, puts])

                except Exception as e:
                    logger.warning(
                        "Failed to fetch options for expiration", expiration=exp_date, error=str(e)
                    )
                    continue

            if all_options:
                df = pd.concat(all_options, ignore_index=True)
                df["commodity_id"] = commodity_id
                df["underlying_symbol"] = symbol

                # Rename columns to match our schema
                df = df.rename(
                    columns={
                        "strike": "strike_price",
                        "lastPrice": "last_price",
                        "bid": "bid_price",
                        "ask": "ask_price",
                        "volume": "volume",
                        "openInterest": "open_interest",
                        "impliedVolatility": "implied_volatility",
                    }
                )

                logger.info("Fetched options chain successfully", symbol=symbol, records=len(df))

                return df

            return pd.DataFrame()

        except Exception as e:
            logger.error("Failed to fetch options chain", symbol=symbol, error=str(e))
            raise
