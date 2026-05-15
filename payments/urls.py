from django.urls import path
from . import views

urlpatterns = [
    path("pay/<int:route_id>/", views.initiate_payment, name="initiate_payment"),
    path("result/<int:order_id>/", views.payment_result, name="payment_result"),
    path("status/<int:order_id>/", views.check_payment_status, name="check_payment_status"),
]
