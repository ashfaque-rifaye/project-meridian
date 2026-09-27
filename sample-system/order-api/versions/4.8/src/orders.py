"""
order-api :: order intake

REST endpoint POST /v2/orders (OpenAPI: orders-api v2) called by web-checkout.
Validates the order and calls payment-service over gRPC (PaymentAuthorize).
Runs on EKS, deployed by GitHub Actions + Argo CD.

R-26.9 (LEDG-2231): accept 12-character customer IDs; currencyCode required.
"""

CUSTOMER_ID_MAX = 12
SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP", "JPY", "CAD"}


def validate(order: dict) -> dict:
    if not order.get("customerId") or len(order["customerId"]) > CUSTOMER_ID_MAX:
        raise ValueError("customerId must be 1-12 characters")
    if order.get("currencyCode") not in SUPPORTED_CURRENCIES:
        raise ValueError("unsupported currencyCode")
    if float(order["amount"]) <= 0:
        raise ValueError("amount must be positive")
    return order
