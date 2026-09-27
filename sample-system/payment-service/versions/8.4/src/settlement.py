"""
payment-service :: settlement publisher

Authorizes payments received from order-api (gRPC PaymentAuthorize) and
publishes settled orders to Kafka topic orders.v1 using Avro subject
orders-value. Runs on AKS, deployed by Azure DevOps.

R-26.9 (LEDG-2231, LEDG-2233): 12-character customer IDs, currencyCode,
orders-value schema v4.
"""

SCHEMA_SUBJECT = "orders-value"
SCHEMA_VERSION = 4
CUSTOMER_ID_MAX = 12


def settled_order(order: dict, auth: dict) -> dict:
    if len(order["customerId"]) > CUSTOMER_ID_MAX:
        raise ValueError("customerId exceeds 12 characters")
    return {
        "orderId": order["orderId"],
        "customerId": order["customerId"],
        "currencyCode": order["currencyCode"],
        "amount": order["amount"],
        "settledAt": auth["settledAt"],
    }
