from decimal import Decimal
from django import template

register = template.Library()


@register.filter
def cz_amount(value):
    """
    Format number with non-breaking spaces for thousands and comma as decimal separator.
    Example: 1024.1 -> "1 024,10"
    """
    if value is None:
        return ""

    dec = Decimal(value).quantize(Decimal("0.01"))
    formatted = f"{dec:,.2f}".replace(",", " ").replace(".", ",")
    return formatted
