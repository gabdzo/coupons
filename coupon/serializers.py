from .enums import CouponStatus
from .models import Coupon

from decimal import Decimal
from rest_framework.serializers import Serializer, CharField, IntegerField, EmailField, FloatField


class OwnerSerializer(Serializer):
    email = EmailField(required=False)
    id = IntegerField(required=False)


class CouponSerializer(Serializer):
    code = CharField(max_length=255, required=True)
    owner = OwnerSerializer(required=False)

    # all calls that can fail should be in try/expect blocks
    def validate(self, attrs):
        # updates root serializer attributes invalid_coupons and valid_coupons
        code = attrs.get('code')
        owner = attrs.get('owner')

        # if 2 or more valid coupons, use code_count of valid instead of all
        if len(self.root.valid_coupons) > 1:
            coupon_count = len(self.root.valid_coupons)
        else:
            coupon_count = len(self.root.initial_data['coupons'])

        # validate price
        price_serializer = PriceDetailSerializer(data=self.root.initial_data.get('price'))
        price_serializer.is_valid(raise_exception=True)

        # append to invalid_coupons when coupon not in DB
        if not Coupon.objects.filter(code=code).exists():
            self.root.invalid_coupons.append({code: CouponStatus.NOT_FOUND})
            return attrs

        # validates coupon
        status = Coupon.objects.get(code=code).validate_coupon(price_serializer.validated_data, coupon_count, owner)

        # append invalid_coupons with error status
        if status != CouponStatus.OK:
            self.root.invalid_coupons.append({code: status})
            return attrs

        self.root.valid_coupons.append(code)
        return attrs


class PriceDetailSerializer(Serializer):
    value = FloatField(required=True)
    currency = CharField(required=False, max_length=3, default='EUR')
    decimals = IntegerField(required=False, default=2)
    rounding = CharField(required=False, default='ROUND_DOWN')

    def validate_decimals(self, value):
        return Decimal(10) ** -abs(value)

    def validate_value(self, value):
        return abs(value)

    def validate_rounding(self, rounding):
        if rounding == 'up':
            return 'ROUND_UP'
        else:
            return 'ROUND_DOWN'


class ValidateCouponSerializer(Serializer):
    coupons = CouponSerializer(many=True)
    price = PriceDetailSerializer(required=True)

    def __init__(self, *args, **kwargs):
        super(ValidateCouponSerializer, self).__init__(*args, **kwargs)
        self.valid_coupons = []
        self.invalid_coupons = []
