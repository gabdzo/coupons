import pycountry
import random

from dateutil.relativedelta import relativedelta
from string import ascii_uppercase, digits

from django.db.models import (BooleanField, CASCADE, CharField, DateTimeField, ForeignKey, IntegerField, Model,
                              PositiveIntegerField, TextField)
from django.utils.timezone import now
from django.utils.translation import ugettext as _

from .enums import CouponStatus


CURRENCIES = sorted([(c.alpha_3, c.name) for c in pycountry.currencies], key=lambda tup: tup[1])


class CouponType(Model):
    name = CharField(_("name"), max_length=255, blank=False)
    minimum_order_value = IntegerField(_("minimum order value"), default=0)
    combinable = BooleanField(_("possible to combine with other coupons"), default=False)

    class Meta:
        verbose_name = _("coupon type")
        verbose_name_plural = _("coupon types")

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<{klass}: {name}>'.format(klass=self.__class__.__name__, name=self.name)


class UsedCoupon(Model):
    order = PositiveIntegerField(blank=True, null=True),
    coupon = ForeignKey("coupon.Coupon", related_name="used_coupons", on_delete=CASCADE)
    owner = CharField(max_length=255, blank=True, null=True)


class Coupon(Model):
    name = CharField(_("name"), max_length=255, blank=False)
    coupon_type = ForeignKey(CouponType, related_name="coupons", verbose_name=_("coupon type"), on_delete=CASCADE)
    quantity = IntegerField(_("quantity (0 = limited solely by expiration)"), default=1)
    units_used = IntegerField(_("units used"), blank=True, default=0)
    valid_period = IntegerField(_("valid period"), blank=True, default=6)
    value = PositiveIntegerField(_("value (by type)"), blank=False, null=True)
    code = CharField(_("coupon code (unique)"), max_length=20, unique=True, blank=True)
    note = TextField(_("note"), null=True, blank=True)

    valid_from = DateTimeField(blank=False, null=False)
    valid_to = DateTimeField(blank=True, null=True)
    used_up = DateTimeField(blank=True, null=True)

    owner = CharField(max_length=255, blank=True, null=True)
    currency = CharField(choices=CURRENCIES, max_length=3, null=True, blank=True)

    class Meta:
        verbose_name = _("coupon")
        verbose_name_plural = _("coupons")

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<{klass}: {name}>'.format(klass=self.__class__.__name__, name=self.name)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_unique_code()
        if not self.valid_to:
            self.valid_to = self.generate_expiration_date()
        if self.units_used >= self.quantity:
            self.used_up = now()
        super().save(*args, **kwargs)

    @property
    def valid(self):
        return not self.expired and not self.used_up

    @property
    def expired(self):
        return now() > self.valid_to

    def total_used(self):
        if self.quantity == 0:
            return "Not limited by quantity"
        return "{used}/{quantity}".format(used=self.units_used, quantity=self.quantity)
    total_used.short_description = "total used"

    @classmethod
    def generate_unique_code(cls, length=6):
        code = ""
        code = code.join(random.choice(ascii_uppercase + digits) for i in range(length))
        if cls.objects.filter(code=code).exists():
            return cls.generate_unique_code()
        return code

    @classmethod
    def generate_expiration_date(cls):
        expiration_date = (now() + relativedelta(months=+6)).replace(hour=23, minute=59, second=59)
        return expiration_date

    def use_coupon(self, order, user):
        UsedCoupon.objects.create(
            coupon=self,
            order=order,
            user=user
        )
        self.units_used += 1
        self.save()

    def can_be_used_on_order(self, price):
        return self.valid and self.coupon_type.minimum_order_value <= price

    def validate_coupon(self, price, code_count, owner):
        if not self.valid:
            return CouponStatus.VALID
        if not self.can_be_used_on_order(price['value']):
            return CouponStatus.PRICE
        if not self.currency == price['currency']:
            return CouponStatus.CURRENCY
        if self.owner and not owner == self.owner:
            return CouponStatus.OWNER
        if code_count > 1:
            if not self.coupon_type.combinable:
                return CouponStatus.COMBINABLE
        return CouponStatus.OK
