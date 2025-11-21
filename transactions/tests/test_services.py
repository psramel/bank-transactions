import pytest
from transactions.models import Transaction
from transactions.services import validate_row, import_transactions, RowValidationError


def test_validate_row_missing_field():
    with pytest.raises(RowValidationError):
        validate_row({})


def test_validate_row_invalid_timestamp():
    row = {"reference": "r1", "timestamp": "bad", "amount": "10", "currency": "CZK"}
    with pytest.raises(RowValidationError):
        validate_row(row)


def test_validate_row_invalid_amount():
    row = {"reference": "r1", "timestamp": "2023-01-01T00:00:00Z", "amount": "xx", "currency": "CZK"}
    with pytest.raises(RowValidationError):
        validate_row(row)


def test_validate_row_missing_currency():
    row = {"reference": "r1", "timestamp": "2023-01-01T00:00:00Z", "amount": "10"}
    with pytest.raises(RowValidationError):
        validate_row(row)


def test_validate_row_missing_reference():
    row = {"timestamp": "2023-01-01T00:00:00Z", "amount": "10", "currency": "CZK"}
    with pytest.raises(RowValidationError):
        validate_row(row)


def test_validate_row_ok():
    row = {
        "reference": "r1",
        "timestamp": "2023-01-01T00:00:00Z",
        "amount": "10",
        "currency": "CZK",
        "description": "test",
    }
    resp = validate_row(row)
    assert isinstance(resp, dict)
    assert resp["amount"] == resp["amount"].__class__("10")


@pytest.mark.django_db
def test_import_transactions_creates_and_skips_duplicates():
    data = [
        {"reference": "r1", "timestamp": "2023-01-01T00:00:00Z", "amount": "10", "currency": "CZK", "description": ""},
        {"reference": "r1", "timestamp": "2023-01-02T00:00:00Z", "amount": "20", "currency": "CZK", "description": ""},
        {"reference": "r2", "timestamp": "2023-01-03T00:00:00Z", "amount": "30", "currency": "CZK", "description": ""},
    ]
    result = import_transactions(data)
    assert result.processed == 3
    assert result.errors == 0
    assert result.duplicates == 1
    assert Transaction.objects.count() == 2
    assert Transaction.objects.filter(reference="r1").count() == 1
    # r1 should keep the first occurrence values
    r1 = Transaction.objects.get(reference="r1")
    assert r1.timestamp.isoformat().startswith("2023-01-01T00:00:00")
    assert r1.amount == r1.amount.__class__("10")


@pytest.mark.django_db
def test_import_transactions_duplicates_and_errors():
    data = [
        {"reference": "r1", "timestamp": "2023-01-01T00:00:00Z", "amount": "10", "currency": "CZK", "description": ""},
        {"reference": "r1", "timestamp": "2023-01-02T00:00:00Z", "amount": "20", "currency": "CZK", "description": ""},  # duplicate
        {"reference": "r2", "timestamp": "bad", "amount": "30", "currency": "CZK", "description": ""},  # invalid timestamp
    ]
    result = import_transactions(data)
    assert result.processed == 3
    assert result.errors == 1
    assert result.duplicates == 1
    assert Transaction.objects.count() == 1
    # r1 should be persisted once with original values
    r1 = Transaction.objects.get(reference="r1")
    assert r1.timestamp.isoformat().startswith("2023-01-01T00:00:00")
    assert r1.amount == r1.amount.__class__("10")


@pytest.mark.django_db
def test_import_transactions_errors_only():
    data = [
        {"reference": "r1", "timestamp": "bad", "amount": "10", "currency": "CZK", "description": ""},
        {"reference": "", "timestamp": "2023-01-01T00:00:00Z", "amount": "10", "currency": "CZK", "description": ""},
    ]
    result = import_transactions(data)
    assert result.processed == 2
    assert result.errors == 2
    assert result.duplicates == 0
    assert result.created == 0
    assert Transaction.objects.count() == 0
