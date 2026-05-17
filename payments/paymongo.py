import base64
import requests
from django.conf import settings

PAYMONGO_BASE_URL = "https://api.paymongo.com/v1"

# PayMongo method type names
METHOD_TYPES = {
    "gcash": "gcash",
    "paymaya": "paymaya",
    "grab_pay": "grab_pay",
    "card": "card",
}


def get_auth_header():
    secret = settings.PAYMONGO_SECRET_KEY
    encoded = base64.b64encode(f"{secret}:".encode()).decode()
    return {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/json",
    }


def create_payment_link(amount_centavos: int, description: str, success_url: str, cancel_url: str, payment_method: str = "gcash") -> dict:
    """
    Creates a PayMongo Payment Link.
    payment_method: 'gcash', 'paymaya', 'grab_pay', 'card'
    The checkout page will pre-select / highlight the chosen method.
    Returns dict with link_id and checkout_url.
    """
    payload = {
        "data": {
            "attributes": {
                "amount": amount_centavos,
                "description": description,
                "currency": "PHP",
                "redirect": {
                    "success": success_url,
                    "failed": cancel_url,
                },
            }
        }
    }
    response = requests.post(
        f"{PAYMONGO_BASE_URL}/links",
        json=payload,
        headers=get_auth_header(),
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()["data"]
    checkout_url = data["attributes"]["checkout_url"]

    # Append payment method hint so PayMongo pre-selects it on their checkout page
    method_key = METHOD_TYPES.get(payment_method, "gcash")
    if "?" in checkout_url:
        checkout_url += f"&payment_method_type={method_key}"
    else:
        checkout_url += f"?payment_method_type={method_key}"

    return {
        "link_id": data["id"],
        "checkout_url": checkout_url,
        "reference_number": data["attributes"].get("reference_number", ""),
    }


def retrieve_payment_link(link_id: str) -> dict:
    """
    Retrieves a PayMongo Payment Link and returns its full data attributes.
    """
    response = requests.get(
        f"{PAYMONGO_BASE_URL}/links/{link_id}",
        headers=get_auth_header(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["data"]


def get_payment_link_status(link_id: str) -> str:
    """
    Returns the payment status of a link: 'paid', 'pending', 'unpaid', etc.
    Checks both the link-level status AND the payments array (handles QRPh, GCash, etc.)
    """
    try:
        data = retrieve_payment_link(link_id)
        attrs = data["attributes"]

        # 1. Check link-level status first — PayMongo sets this to "paid" once settled
        link_status = attrs.get("status", "unpaid")
        if link_status == "paid":
            return "paid"

        # 2. Check payments array — each payment has its own status
        payments = attrs.get("payments", [])
        for payment in payments:
            p_status = payment.get("attributes", {}).get("status", "")
            if p_status == "paid":
                return "paid"
            if p_status in ("pending", "processing"):
                return "pending"

        return link_status  # "unpaid" or whatever PayMongo returns
    except Exception:
        return "unknown"