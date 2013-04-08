# -*- coding: utf-8 -*-
from decimal import Decimal
from shop.cart.cart_modifiers_base import BaseCartModifier
from shop.models.productmodel import Product
from shop.util.loader import get_model_string
from django.db import models


class ProductProxy(Product):
    """
    This is an example model of a free product proxy. It serves to "mark"
    instances of Product subclasses as being a free item, added to the cart
    only as a gift.
    It behaves almost exactly like the wrapped product instance.
    """
    real_product = models.ForeignKey(get_model_string('Product'))

    def __init__(self, real_product):
        self.real_product = real_product

    def __getattr__(self, name):
        return getattr(self.real_product, name)


class FreeProductProxy(ProductProxy):
    """
    Just a marker class, so that we can differentiate on types of proxies.
    """


class FreeProductModifier(BaseCartModifier):
    """
    If the cart reaches a certain total, we add a free product as a gift.
    Of course, this is only an example.
    """
    treshold = Decimal("100")  # that's a hundred bucks
    product_class = None  # make this point to your real product class

    def get_instance(self):
        # Query your real product class for the exact product you wish to
        # give as a reward.
        # return Books.objects.get(title="free besteller") ...
        raise NotImplemented  # This is just an example class.

    def process_cart_item(self, cart_item, state):
        """
        If the item passed is a ProductAdapter and contains a {"free": True}
        entry, then we add a price modifier for the negative price.

        Again, this is just an example.
        """
        if isinstance(cart_item, FreeProductProxy):
            rebate = -cart_item.price
            field = (u"Complimetary copy", rebate )
            cart_item.current_total = cart_item.current_total + rebate
            cart_item.extra_price_fields.append(field)

    def post_process_cart(self, cart, state):
        from shop.models import CartItem

        if cart.total_price >= self.treshold:
            product_instance = self.get_instance()
            items = CartItem.objects.filter(cart=cart)
            has_free_product = False
            for item in items:
                if isinstance(item, FreeProductProxy):
                    if item.real_product == product_instance:
                        has_free_product = True
                        break

            if not has_free_product:
                proxy = FreeProductProxy(product_instance)
                cart.add_product(proxy,
                                 quantity=1,
                                 merge=False)
                # We flag the cart for another update pass. That's a little
                # inefficient.
                cart.needs_new_update()
