from django.utils.translation import gettext_lazy as _


class CouponStatus:
    OWNER = 'wrong-owner'
    PRICE = 'minimum-order-price'
    CURRENCY = 'wrong-currency'
    VALID = 'not-valid'
    COMBINABLE = 'not-combinable'
    OK = 'ok'
    NOT_FOUND = 'not-found'

    CHOICES = [
        (OWNER, _("Coupon has different owner")),
        (PRICE, _("Coupons minimum order price is higher then order price")),
        (CURRENCY, _("Coupon is available for different currency")),
        (VALID, _("Coupon is not valid")),
        (OK, _("Coupon is valid")),
        (COMBINABLE, _("Coupon is not combinable")),
        (NOT_FOUND, _("Coupon does not exist"))
    ]
