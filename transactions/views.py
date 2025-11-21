"""Views for CSV import and transaction"""
import csv
import logging
import io
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .models import Transaction
from .services import import_transactions


LOGGER = logging.getLogger(__name__)


# this should be handled better way in real world (need to investigate)
@csrf_exempt
def transactions_view(request):
    """POST and GET view"""
    if request.method == "POST":
        return csv_upload(request)
    return render_transactions_page(request)


def csv_upload(request):
    """Load CSV file and its validation"""
    content_type = (request.META.get("CONTENT_TYPE") or request.content_type or "").lower()
    if not content_type.startswith("text/csv"):
        LOGGER.warning("CSV upload failed: bad content type %s", request.content_type)
        return HttpResponseBadRequest("Content-Type must be text/csv")
    
    LOGGER.info(
        "CSV upload start bytes=%d content_type=%s",
        len(request.body),
        request.content_type,
    )
    if not request.body:
        LOGGER.warning("CSV upload failed: empty request body")
        return HttpResponseBadRequest("No data inside CSV file. File looks empty.")

    try:
        text = request.body.decode("utf-8")
    except UnicodeDecodeError:
        LOGGER.warning("CSV upload failed: UTF-8 decode error")
        return HttpResponseBadRequest("Problem with UTF-8 decoding.")

    if not text.strip():
        LOGGER.warning("CSV upload failed: CSV is empty after decoding")
        return HttpResponseBadRequest("CSV is empty.")

    try:
        csv_file = io.StringIO(text)
        reader = csv.DictReader(csv_file)
    except csv.Error as exc:
        LOGGER.warning("CSV upload failed: parsing error: %s", exc)
        return HttpResponseBadRequest(f"CSV parsing error: {exc}")
    
    expected_header = ["reference", "timestamp", "amount", "currency", "description"]
    real_header = reader.fieldnames or []

    if not real_header or not any(h in expected_header for h in real_header):
        LOGGER.warning("CSV upload failed: missing header in CSV file")
        return HttpResponseBadRequest("Missing header in CSV file")

    missing = []
    for item in expected_header:
        if item not in real_header:
            missing.append(item)
    
    if missing:
        missing_cols = ", ".join(missing)
        LOGGER.warning("CSV upload failed: missing columns: %s", missing_cols)
        return HttpResponseBadRequest(f"CSV header is missing columns: {missing_cols}")

    try:
        first_row = next(reader, None)
    except csv.Error as exc:
        LOGGER.warning("CSV upload failed: parsing error during row read: %s", exc)
        return HttpResponseBadRequest(f"CSV parsing error: {exc}")

    if first_row is None:
        LOGGER.warning("CSV upload failed: CSV contains header only")
        return HttpResponseBadRequest("CSV doesn't contain any rows.")

    rows = []
    try:
        rows.append(first_row)
        for row in reader:
            rows.append(row)
    except csv.Error as exc:
        LOGGER.warning(f"CSV parsing error: {exc}")
        return HttpResponseBadRequest(f"CSV parsing error: {exc}")

    result = import_transactions(rows)
    status = 201 if (result.errors == 0 and result.duplicates == 0) else 207
    response = HttpResponse(
        f"Processed {result.processed} (created {result.created}, errors {result.errors}, duplicates {result.duplicates})",
        status=status,
    )
    LOGGER.info("CSV upload done processed=%d status=%d", result.processed, response.status_code)
    return response



def render_transactions_page(request):
    """Render all transactions and highlight those with the highest positive amount."""
    transactions = Transaction.objects.all()
    max_income_amount = (
        Transaction.objects.filter(amount__gt=0)
        .order_by("-amount")
        .values_list("amount", flat=True)
        .first()
    )
    max_income_ids = set()
    if max_income_amount is not None:
        max_income_ids = set(
            Transaction.objects.filter(amount=max_income_amount)
            .values_list("id", flat=True)
        )
    return render(
        request,
        "transactions/transactions_list.html",
        {
            "transactions": transactions,
            "max_income_ids": max_income_ids,
        },
    )
