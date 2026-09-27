"""
order-api — v4.8
Receives checkout orders, validates, forwards to payment-service.
Release R-26.9: adds 12-character customerId support.
"""
SERVICE_NAME = "order-api"
VERSION = "4.8"
COMMIT = "1c2a4d"
DOWNSTREAM = "payment-service"
CUSTOMER_ID_MAX_LENGTH = 12  # upgraded from 10 in R-26.9
