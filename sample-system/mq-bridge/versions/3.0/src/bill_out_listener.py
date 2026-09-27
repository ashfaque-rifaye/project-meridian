"""
mq-bridge :: BILL.OUT listener

Reads billing events from IBM MQ queue BILL.OUT (queue manager QM.INTEG.01),
maps each event to a LEDGREC record and puts it on LEDGER.IN.

Runs on OpenShift (namespace: integration) and is deployed by Argo CD.
"""

import json

from ledger_record import to_ledger_record

SOURCE_QUEUE = "BILL.OUT"


def handle_message(body: bytes, config: dict) -> dict:
    event = json.loads(body)
    message = to_ledger_record(event, config)
    # The real bridge calls MQPUT here; the result is returned for tracing.
    return {"source": SOURCE_QUEUE, "billingId": event.get("billingId"), **message}
