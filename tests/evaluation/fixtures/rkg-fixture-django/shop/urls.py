from django.urls import path

from shop.views import create_order, varied

urlpatterns = [
    path("orders/", create_order),
    path("varied/", varied),
]
