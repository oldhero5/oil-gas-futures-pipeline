import sys
from pathlib import Path

from structlog import get_logger

# Add src to path if this module is run directly or by Celery outside main project context
# This ensures DataIngestionPipeline can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


from src.celery_app import celery_app
from src.pipeline.ingestion_pipeline import DataIngestionPipeline

# from src.config import settings # Assuming you might have a config settings module

logger = get_logger(__name__)


# A simple stand-in for settings if src.config doesn't exist or DB_PATH isn't there
class SimpleSettings:
    DB_PATH = "data/futures_analysis.db"


settings = SimpleSettings()


@celery_app.task(name="src.tasks.run_daily_data_ingestion")
def run_daily_data_ingestion():
    """
    Celery task to run the daily data ingestion pipeline.
    Fetches data for the last 1 day.
    """
    logger.info("Starting daily data ingestion task.")
    try:
        # Use db_path from settings or a default
        db_path = settings.DB_PATH

        # Ensure the data directory exists if db_path implies it
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        pipeline = DataIngestionPipeline(db_path=db_path)
        # For daily updates, we typically fetch the last 1 day of data.
        # The 'period' argument in run_full_pipeline handles this.
        stats = pipeline.run_full_pipeline(commodities=["WTI", "NG"], period="1d")
        pipeline.close()
        logger.info("Daily data ingestion task completed successfully.", stats=stats)
        return {"status": "SUCCESS", "details": stats}
    except Exception as e:
        logger.error("Daily data ingestion task failed.", error=str(e), exc_info=True)
        # You might want to add more sophisticated error handling/retry logic here
        return {"status": "FAILURE", "error": str(e)}
