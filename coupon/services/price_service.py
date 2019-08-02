from decimal import Decimal
from django.db.models import Sum
from prices import Price


class PriceService:

    def __init__(self, price, coupons):
        self.discounts = {}
        self.final_price = {}
        self.price = Decimal(price['value']).quantize(price['decimals'], rounding=price['rounding'])
        self.decimals = price['decimals']
        self.rounding = price['rounding']
        self.currency = price['currency']
        self.coupons = coupons

    def _get_sum(self, coupon_type):
        # sum all valid coupons by type
        return self.coupons.filter(coupon_type__name=coupon_type).aggregate(Sum('value'))['value__sum'] or 0.0

    def _get_discount(self, percentage, absolute=0):
        # get discount, if absolute discount available subtract it from price
        return Decimal(((self.price - absolute) / 100) * percentage).quantize(self.decimals, rounding=self.rounding)

    def calculate_discounts(self):
        # calculate two types of discounts ((price - absolute) - percentage) && (price - percentage - absolute)
        self.absolute_sum = self._get_sum('absolute')
        self.percentage_sum = self._get_sum('percentage')

        full_price_percentage = self._get_discount(self.percentage_sum)
        price_without_absolute_percentage = self._get_discount(self.percentage_sum, self.absolute_sum)

        self.discounts = {
            'absolute': self.absolute_sum,
            'percentage': full_price_percentage,
            'combined_absolute_first': full_price_percentage + self.absolute_sum,
            'combined_percentage_first': price_without_absolute_percentage + self.absolute_sum,
        }

    def validate_discounts(self):
        # if absolute discount is higher then price or percentage over 100 set discount to price value
        if self.absolute_sum >= self.price or self.percentage_sum >= 100:
            self.discounts['combined_percentage_first'] = self.price
            self.discounts['combined_absolute_first'] = self.price

    def calculate_price(self):
        # calculate price in Price object
        self.final_price = {
            'absolute_first': self._get_final_price(self.discounts['combined_absolute_first']),
            'percentage_first': self._get_final_price(self.discounts['combined_percentage_first'])
        }

    def _get_final_price(self, discount):
        net = Decimal(self.price - discount).quantize(self.decimals, rounding=self.rounding)
        return Price(net=net, currency=self.currency)
