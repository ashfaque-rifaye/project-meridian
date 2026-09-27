"""
web-checkout :: order submission client

Storefront BFF that submits carts to order-api (POST /v2/orders).
Customer IDs are issued by the identity platform; since Sep 2026 new customers
receive 12-character IDs. Runs on GKE, deployed by Google Cloud Deploy.
"""

ORDER_API = "https://order-api.orders.svc/v2/orders"


def order_payload(cart: dict, customer: dict) -> dict:
    return {
        "orderId": cart["cartId"],
        "customerId": customer["id"],
        "currencyCode": cart["currency"],
        "amount": f"{cart['total']:.2f}",
    }
