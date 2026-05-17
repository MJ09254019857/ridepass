from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from decimal import Decimal

from .models import TicketOrder
from .paymongo import create_payment_link, get_payment_link_status


def _get_wallet(user):
    from core.models import Wallet
    return Wallet.objects.get_or_create(user=user)[0]


def _unread(user):
    from core.models import Notification
    return Notification.objects.filter(user=user, is_read=False).count()


def _add_notif(user, title, message, icon="🔔"):
    from core.models import Notification
    Notification.objects.create(user=user, title=title, message=message, icon=icon)


@login_required
def initiate_payment(request, route_id):
    """
    Called when user submits the Buy Ticket form.
    Creates a PayMongo Payment Link and redirects to checkout.
    """
    from core.models import Route
    route = get_object_or_404(Route, id=route_id, is_active=True)
    amount_centavos = int(route.fare * 100)

    order = TicketOrder.objects.create(
        user=request.user,
        route_id=route.id,
        route_name=route.name,
        amount=amount_centavos,
        status="pending",
    )

    success_url = request.build_absolute_uri(
        reverse("payment_result", args=[order.pk])
    ) + "?status=success"
    cancel_url = request.build_absolute_uri(
        reverse("payment_result", args=[order.pk])
    ) + "?status=failed"

    payment_method = request.POST.get("payment_method", "gcash")
    if payment_method not in ["gcash", "paymaya", "grab_pay", "card"]:
        payment_method = "gcash"

    try:
        link_data = create_payment_link(
            amount_centavos=amount_centavos,
            description=f"RidePass Ticket – {route.name}",
            success_url=success_url,
            cancel_url=cancel_url,
            payment_method=payment_method,
        )
        order.paymongo_link_id = link_data["link_id"]
        order.checkout_url = link_data["checkout_url"]
        order.save()
        return redirect(link_data["checkout_url"])
    except Exception as e:
        order.status = "failed"
        order.save()
        messages.error(request, f"Payment error: {str(e)}")
        return redirect("buy_ticket", route_id=route_id)


@login_required
def payment_result(request, order_id):
    """
    PayMongo redirects here after payment success or failure.
    Verifies payment and activates the ticket if paid.
    """
    from core.models import Route, Ticket, Transaction
    order = get_object_or_404(TicketOrder, pk=order_id, user=request.user)
    wallet = _get_wallet(request.user)
    status_param = request.GET.get("status", "")

    if order.status == "paid":
        # Already processed (e.g. user refreshed)
        messages.success(request, "Your ticket is ready!")
        if order.ticket:
            return redirect("ticket_detail", ticket_id=order.ticket.id)
        return redirect("my_tickets")

    if status_param == "success" and order.paymongo_link_id:
        payment_status = get_payment_link_status(order.paymongo_link_id)

        if payment_status == "paid":
            # Create the ticket
            route = get_object_or_404(Route, id=order.route_id)
            ticket = Ticket.objects.create(
                user=request.user,
                route=route,
                fare_paid=Decimal(order.amount) / 100,
                status="active",
            )
            # Record transaction
            Transaction.objects.create(
                user=request.user,
                transaction_type="purchase",
                amount=Decimal(order.amount) / 100,
                description=f"Ticket: {route.name} (via PayMongo)",
                ticket=ticket,
            )
            # Update order
            order.status = "paid"
            order.ticket = ticket
            order.save()
            # Notify user
            _add_notif(request.user, "Ticket Purchased!", f"Your ticket for {route.name} is ready.", "🎟️")
            messages.success(request, "Payment successful! Your ticket is ready.")
            return redirect("ticket_detail", ticket_id=ticket.id)
        else:
            # Payment link exists but not yet marked paid — could be processing
            order.status = "pending"
            order.save()
            messages.info(request, "Payment is still being processed. Please wait a moment and refresh.")

    elif status_param == "failed":
        order.status = "failed"
        order.save()
        messages.error(request, "Payment failed or was cancelled. Please try again.")

    return render(request, "payments/result.html", {
        "order": order,
        "wallet": wallet,
        "notif_count": _unread(request.user),
    })


@login_required
def check_payment_status(request, order_id):
    """
    AJAX polling endpoint — frontend polls this to check payment status.
    """
    from core.models import Route, Ticket, Transaction
    order = get_object_or_404(TicketOrder, pk=order_id, user=request.user)

    if order.status == "paid" and order.ticket:
        return JsonResponse({
            "status": "paid",
            "redirect_url": reverse("ticket_detail", args=[order.ticket.id]),
        })

    if order.paymongo_link_id:
        payment_status = get_payment_link_status(order.paymongo_link_id)
        if payment_status == "paid" and order.status != "paid":
            route = get_object_or_404(Route, id=order.route_id)
            ticket = Ticket.objects.create(
                user=request.user,
                route=route,
                fare_paid=Decimal(order.amount) / 100,
                status="active",
            )
            Transaction.objects.create(
                user=request.user,
                transaction_type="purchase",
                amount=Decimal(order.amount) / 100,
                description=f"Ticket: {route.name} (via PayMongo)",
                ticket=ticket,
            )
            order.status = "paid"
            order.ticket = ticket
            order.save()
            _add_notif(request.user, "Ticket Purchased!", f"Your ticket for {route.name} is ready.", "🎟️")
            return JsonResponse({
                "status": "paid",
                "redirect_url": reverse("ticket_detail", args=[ticket.id]),
            })

    return JsonResponse({"status": order.status})
