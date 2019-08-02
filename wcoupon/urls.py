from django.contrib import admin
from django.urls import path

from coupon.views import ValidateCoupons, UseCoupons

urlpatterns = [
    path('admin/', admin.site.urls),
    path('validate_coupons/', ValidateCoupons.as_view(), name='coupon'),
    path('use_coupons/', UseCoupons.as_view(), name='use_coupon')
]
