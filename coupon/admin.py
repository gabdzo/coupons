from .models import Coupon, CouponType, UsedCoupon

from django.contrib.admin import ModelAdmin, site


# Register your models here.

class CouponAdmin(ModelAdmin):
    model = Coupon
    list_display = ('code', 'owner')

class CouponTypeAdmin(ModelAdmin):
    list_display = ('name', 'minimum_order_value', 'combinable')


site.register(CouponType, CouponTypeAdmin)
site.register(Coupon, CouponAdmin)
