from app.db.session import SessionLocal
from app.services.windows_update_evaluation_service import evaluate_all_updates as _evaluate
from app.core.logging import logger


async def evaluate_all_updates() -> None:
    db = SessionLocal()
    try:
        logger.info("Starting Windows update evaluation")
        result = _evaluate(db)
        logger.info(f"Update evaluation done: {result}")
    except Exception as e:
        logger.error(f"Update evaluation failed: {e}")
    finally:
        db.close()
