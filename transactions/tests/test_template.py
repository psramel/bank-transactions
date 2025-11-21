import re
import pytest
from django.urls import reverse

from transactions.models import Transaction


@pytest.mark.django_db
def test_highlights_biggest_income(client):
    Transaction.objects.create(
        reference="r1",
        timestamp="2023-01-01T00:00:00Z",
        amount="-100",
        currency="CZK",
        description="neg",
    )
    Transaction.objects.create(
        reference="r2",
        timestamp="2023-01-02T00:00:00Z",
        amount="50",
        currency="CZK",
        description="small income",
    )
    Transaction.objects.create(
        reference="r3",
        timestamp="2023-01-03T00:00:00Z",
        amount="200",
        currency="CZK",
        description="big income",
    )

    resp = client.get(reverse("transactions"))
    assert resp.status_code == 200

    html = resp.content.decode()
    rows = re.findall(r'<tr class="biggest-income">.*?</tr>', html, re.S)
    assert len(rows) == 1, "Expected exactly one highlighted row"
    assert "200" in rows[0]


@pytest.mark.django_db
def test_highlights_multiple_biggest_incomes(client):
    Transaction.objects.create(
        reference="r1",
        timestamp="2023-01-01T00:00:00Z",
        amount="200",
        currency="CZK",
        description="income1",
    )
    Transaction.objects.create(
        reference="r2",
        timestamp="2023-01-02T00:00:00Z",
        amount="200",
        currency="CZK",
        description="income2",
    )
    resp = client.get(reverse("transactions"))
    assert resp.status_code == 200
    html = resp.content.decode()
    rows = re.findall(r'<tr class="biggest-income">.*?</tr>', html, re.S)
    assert len(rows) == 2, "Expected two highlighted rows"
