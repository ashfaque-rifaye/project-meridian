"""
order-api :: order intake

REST endpoint POST /v2/orders (OpenAPI: orders-api v2) called by web-checkout.
Validates the order and calls payment-service over gRPC (PaymentAuthorize).
Runs on EKS, deployed by GitHub Actions + Argo CD.
"""

CUSTOMER_ID_MAX = 10


def validate(order: dict) -> dict:
    if not order.get("customerId") or len(order["customerId"]) > CUSTOMER_ID_MAX:
        raise ValueError("customerId must be 1-10 characters")
    if float(order["amount"]) <= 0:
        raise ValueError("amount must be positive")
    return order
