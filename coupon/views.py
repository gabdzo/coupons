from .models import Coupon
from .serializers import ValidateCouponSerializer
from .services.price_service import PriceService

from django.http import JsonResponse
from rest_framework.generics import GenericAPIView


'''
Request data:

"coupon" - @code is required, @owner is optional and should contain either ID or email of user
"price" - all values required

Template
{"coupons": 
    [
        {"code": "J1DK0D", "owner": {"email": "gabriel.zvoncek@gmail.com"}},
        {"code": "SJGMG6", "owner": {"id": 1}}
    ],
"price": 
    {
        "value": 5234.1234,
        "currency": "EUR",
        "rounding": "down",
        "decimals": 2
    }
}
'''


class ValidateCoupons(GenericAPIView):

    def get(self, request, *args, **kwargs):
        serializer = ValidateCouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # get query of valid coupons by codes
        valid_coupons = Coupon.objects.filter(code__in=serializer.valid_coupons)

        # handle price and discounts
        price_service = PriceService(serializer.validated_data['price'], valid_coupons)
        price_service.calculate_discounts()
        price_service.validate_discounts()
        price_service.calculate_price()

        return JsonResponse({
            'valid': serializer.valid_coupons,
            'invalid': serializer.invalid_coupons,
            'discounts': price_service.discounts,
            'final_price': price_service.final_price
        })


class UseCoupons(GenericAPIView):

    def put(self, request, *args, **kwargs):
        serializer = ValidateCouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        valid_coupons = Coupon.objects.filter(code__in=serializer.valid_coupons)

        for coupon in valid_coupons:
            coupon.use_coupon()

        return JsonResponse({
            'used': valid_coupons
        })
