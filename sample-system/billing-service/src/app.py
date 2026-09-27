"""
billing-service — v7.2
Consumes Kafka orders topic, writes billing records to IBM MQ BILL.OUT queue.
"""
SERVICE_NAME = "billing-service"
VERSION = "7.2"
COMMIT = "e3f8a1"
DOWNSTREAM = "mq-bridge"
MQ_QUEUE = "BILL.OUT"
