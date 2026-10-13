from django.conf.urls import url
from django.urls import include, path, re_path
from shop.views import BareDetail, OrderDetail, health

HEALTH_ROUTE = "health/"


def _dynamic_urls():
    return "shop.urls"


urlpatterns = [
    path(HEALTH_ROUTE, health),
    path("orders/<int:pk>/", OrderDetail.as_view()),
    path("bare/", BareDetail.as_view()),
    path("shop/", include("shop.urls")),
    re_path(r"^legacy/$", "shop.views.legacy_report"),
    url(r"^old/$", health),
    path("ghost/", missing_view),
    path("dyn/", include(_dynamic_urls())),
]
