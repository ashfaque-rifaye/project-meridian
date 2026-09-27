"""
payment-service :: settlement publisher

Authorizes payments received from order-api (gRPC PaymentAuthorize) and
publishes settled orders to Kafka topic orders.v1 using Avro subject
orders-value. Runs on AKS, deployed by Azure DevOps.
"""

SCHEMA_SUBJECT = "orders-value"
SCHEMA_VERSION = 3
CUSTOMER_ID_MAX = 10


def settled_order(order: dict, auth: dict) -> dict:
    if len(order["customerId"]) > CUSTOMER_ID_MAX:
        raise ValueError("customerId exceeds 10 characters")
    return {
        "orderId": order["orderId"],
        "customerId": order["customerId"],
        "amount": order["amount"],
        "settledAt": auth["settledAt"],
    }
