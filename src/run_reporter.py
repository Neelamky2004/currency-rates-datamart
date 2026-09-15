"""
Generates structured project updates and operational health reports for batch jobs.
"""
from datetime import datetime
from typing import Dict


class ProjectRunReporter:
    """Emits project run updates, throughput metrics, and validation summaries."""

    @staticmethod
    def generate_status_update(
        batch_id: str,
        records_processed: int,
        outliers_detected: int,
        status: str = "SUCCESS"
    ) -> Dict[str, str]:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
        update_summary = {
            "batch_id": batch_id,
            "timestamp": timestamp,
            "status": status,
            "records_processed": str(records_processed),
            "outliers_detected": str(outliers_detected),
            "summary": (
                f"[{status}] Processed {records_processed} FX rates, "
                f"flagged {outliers_detected} volatility events at {timestamp}."
            )
        }
        return update_summary
