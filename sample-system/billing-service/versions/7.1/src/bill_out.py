"""
billing-service :: BILL.OUT publisher

Consumes settled payments from Kafka topic orders.v1 (consumer group
billing-svc) and publishes one billing event per settlement to IBM MQ queue
BILL.OUT as JSON. Runs on GKE, deployed by Google Cloud Deploy.
"""

import json


def to_bill_out(order_event: dict) -> bytes:
    event = {
        "billingId": f"BL-{order_event['orderId']}",
        "customerId": order_event["customerId"],
        "amount": f"{float(order_event['amount']):.2f}",
        "postedAt": order_event["settledAt"],
    }
    return json.dumps(event).encode()
