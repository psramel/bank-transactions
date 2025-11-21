"""CSV import and validation."""
import logging
from decimal import Decimal
from dataclasses import dataclass
from django.utils.dateparse import parse_datetime

from .models import Transaction

LOGGER = logging.getLogger(__name__)
REQUIRED_FIELDS = ("reference", "timestamp", "amount", "currency")


@dataclass
class ImportResult:
    """Summary info"""
    processed: int
    created: int
    errors: int
    duplicates: int


class RowValidationError(Exception):
    """Raised when validation of row fail"""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def validate_row(row: dict):
    """Validate a CSV row"""
    for i in REQUIRED_FIELDS:
        if not row.get(i):
            LOGGER.warning("Row missing field %s: %s", i, row)
            raise RowValidationError(f"Missing field: {i}")

    reference = row["reference"]
    timestamp = row["timestamp"]
    amount = row["amount"]
    currency = row["currency"]
    description = row.get("description") or ""

    date_time = parse_datetime(timestamp)
    if date_time is None:
        LOGGER.warning("Invalid timestamp: %s | row=%s", timestamp, row)
        raise RowValidationError(f"Invalid timestamp: {timestamp}")

    try:
        amount = Decimal(amount)
    except Exception:
        LOGGER.warning("Invalid amount: %s | row=%s", amount, row)
        raise RowValidationError(f"Invalid amount: {amount}")

    return {
        "reference": reference,
        "timestamp": date_time,
        "amount": amount,
        "currency": currency,
        "description": description,
    }


def import_transactions(rows):
    """Upload CSV and report results."""
    LOGGER.info("Import start")
    processed = 0
    created = 0
    errors = 0
    duplicates = 0

    for row in rows:
        processed += 1
        try:
            validated = validate_row(row)
        except RowValidationError as exc:
            errors += 1
            LOGGER.warning("Skipping: validation error: %s | %s", row, exc.message)
            continue

        _, created_flag = Transaction.objects.get_or_create(
            reference=validated["reference"],
            defaults={
                "timestamp": validated["timestamp"],
                "amount": validated["amount"],
                "currency": validated["currency"],
                "description": validated["description"],
            },
        )

        if created_flag:
            created += 1
        else:
            duplicates += 1
            LOGGER.warning("Duplicate reference skipped: %s", validated["reference"])
            continue

    LOGGER.info(
        "Import done processed=%d created=%d errors=%d duplicates=%d",
        processed, created, errors, duplicates
    )

    return ImportResult(
        processed=processed,
        created=created,
        errors=errors,
        duplicates=duplicates,
    )
