import qrcode
import io
import os
from django.conf import settings


def generate_payment_qr_image(qr_data):
    """Generate a QR code image for payment data and return it as bytes."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=3,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="#1a2332", back_color="white")
    
    # Save to bytes buffer
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer.getvalue()


def generate_ticket_qr(ticket):
    """Generate a real QR code image for a ticket and return its URL."""
    qr_dir = os.path.join(settings.MEDIA_ROOT, 'qrcodes')
    os.makedirs(qr_dir, exist_ok=True)

    filename = f"ticket_{ticket.ticket_code}.png"
    filepath = os.path.join(qr_dir, filename)

    if not os.path.exists(filepath):
        # Encode ticket info into QR
        qr_data = (
            f"RIDEPASS-TICKET\n"
            f"Code: {str(ticket.ticket_code).upper()[:8]}\n"
            f"Route: {ticket.route.name}\n"
            f"From: {ticket.route.origin}\n"
            f"To: {ticket.route.destination}\n"
            f"Fare: PHP {ticket.fare_paid}\n"
            f"Status: {ticket.status.upper()}\n"
            f"UUID: {ticket.ticket_code}"
        )

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=3,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="#1a2332", back_color="white")
        img.save(filepath)

    return f"{settings.MEDIA_URL}qrcodes/{filename}"
