import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_rejects_empty_body(client):
    url = reverse("transactions")
    resp = client.post(url, data=b"", content_type="text/csv")
    assert resp.status_code == 400
    assert b"Content-Type must be text/csv" in resp.content


@pytest.mark.django_db
def test_rejects_non_csv_content_type(client):
    url = reverse("transactions")
    resp = client.post(url, data="not csv", content_type="text/plain")
    assert resp.status_code == 400
    assert b"Content-Type must be text/csv" in resp.content


@pytest.mark.django_db
def test_accepts_non_empty_body(client):
    url = reverse("transactions")
    payload = (
        "reference,timestamp,amount,currency,description\n"
        "r1,2023-01-01T00:00:00Z,10,CZK,test\n"
    )
    resp = client.post(url, data=payload, content_type="text/csv")
    assert resp.status_code in (201, 207)


@pytest.mark.django_db
def test_rejects_invalid_utf8_body(client):
    url = reverse("transactions")
    # invalid UTF-8 byte sequence
    bad_bytes = b"\xff\xfe\xfa"
    resp = client.post(url, data=bad_bytes, content_type="text/csv")
    assert resp.status_code == 400
    assert b"Problem with UTF-8 decoding." in resp.content


@pytest.mark.django_db
def test_rejects_whitespace_only_body(client):
    url = reverse("transactions")
    resp = client.post(url, data="   \n\t", content_type="text/csv")
    assert resp.status_code == 400
    assert b"CSV is empty." in resp.content


@pytest.mark.django_db
def test_rejects_broken_csv(client):
    url = reverse("transactions")
    # include NULL byte to trigger csv.Error
    broken_csv = "reference,timestamp,amount,currency,description\x00\n1,2023-01-01T00:00:00Z,10,CZK,test\n"
    resp = client.post(url, data=broken_csv, content_type="text/csv")
    assert resp.status_code == 400
    # With a mangled header, we expect missing columns
    assert b"CSV header is missing columns" in resp.content


@pytest.mark.django_db
def test_rejects_missing_header(client):
    url = reverse("transactions")
    # CSV without header row
    data = "1,2023-01-01T00:00:00Z,10,CZK,test\n"
    resp = client.post(url, data=data, content_type="text/csv")
    assert resp.status_code == 400
    assert b"Missing header in CSV file" in resp.content


@pytest.mark.django_db
def test_rejects_missing_columns(client):
    url = reverse("transactions")
    # Missing the 'description' column
    data = (
        "reference,timestamp,amount,currency\n"
        "r1,2023-01-01T00:00:00Z,10,CZK\n"
    )
    resp = client.post(url, data=data, content_type="text/csv")
    assert resp.status_code == 400
    assert b"CSV header is missing columns: description" in resp.content


@pytest.mark.django_db
def test_rejects_header_only(client):
    url = reverse("transactions")
    data = "reference,timestamp,amount,currency,description\n"
    resp = client.post(url, data=data, content_type="text/csv")
    assert resp.status_code == 400
    assert b"CSV doesn't contain any rows." in resp.content


@pytest.mark.django_db
def test_import_with_errors_returns_207(client):
    url = reverse("transactions")
    payload = (
        "reference,timestamp,amount,currency,description\n"
        "r1,bad,10,CZK,\n"
        ",2023-01-01T00:00:00Z,10,CZK,\n"
    )
    resp = client.post(url, data=payload, content_type="text/csv")
    assert resp.status_code == 207
