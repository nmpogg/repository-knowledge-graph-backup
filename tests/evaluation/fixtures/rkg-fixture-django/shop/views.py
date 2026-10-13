"""Shop views. The sentinel string must never enter facts or diagnostics."""

from django.views import View
from django.views.decorators.http import require_http_methods, require_POST

_SECRET = "RKG_TEST_SECRET_DO_NOT_PERSIST"


def health(request):
    return None


def legacy_report(request):
    return None


@require_POST
def create_order(request):
    return None


def _method_names():
    return ["GET"]


@require_http_methods(_method_names())
def varied(request):
    return None


class OrderDetail(View):
    http_method_names = ["get"]

    def get(self, request, pk):
        return None


class BareDetail(View):
    def get(self, request):
        return None


def unused(request):
    return None
