from decimal import Decimal
from django.conf import settings
from app_catalog.models import Product, ProductVariant, BoardParams, AddonParams, PizzaSauce

CART_SESSION_ID = "cart"


class SessionCart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_ID)
        if not cart:
            cart = self.session[CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product_id, variant_id, quantity=1, board1_id=None, board2_id=None, sauce_id=None, addons_ids=None, drink=None, update_quantity=False):
        product_id_str = str(product_id)
        variant_id_str = str(variant_id) if variant_id else ""

        item_key_parts = [product_id_str, variant_id_str]
        if board1_id:
            item_key_parts.append(f"b1_{board1_id}")
        if board2_id:
            item_key_parts.append(f"b2_{board2_id}")
        if sauce_id:
            item_key_parts.append(f"s_{sauce_id}")
        if addons_ids:
            item_key_parts.append(f'a_{"_".join(map(str, sorted(addons_ids)))}')
        if drink:
            item_key_parts.append(f"d_{drink}")

        item_key = "-".join(item_key_parts)

        if item_key not in self.cart:
            self.cart[item_key] = {
                "product_id": product_id,
                "variant_id": variant_id,
                "quantity": 0,
                "board1_id": board1_id,
                "board2_id": board2_id,
                "sauce_id": sauce_id,
                "addons_ids": addons_ids if addons_ids else [],
                "drink": drink,
            }

        if update_quantity:
            self.cart[item_key]["quantity"] = quantity
        else:
            self.cart[item_key]["quantity"] += quantity
        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, item_key):
        if item_key in self.cart:
            del self.cart[item_key]
            self.save()

    def __iter__(self):
        product_ids = [item["product_id"] for item in self.cart.values()]
        product_variants_ids = [item["variant_id"] for item in self.cart.values() if item["variant_id"]]
        board_ids = [item["board1_id"] for item in self.cart.values() if item["board1_id"]] + [item["board2_id"] for item in self.cart.values() if item["board2_id"]]
        sauce_ids = [item["sauce_id"] for item in self.cart.values() if item["sauce_id"]]

        # Flatten list of lists for addons_ids
        addons_ids = [addon_id for item in self.cart.values() if item["addons_ids"] for addon_id in item["addons_ids"]]

        products = Product.objects.filter(id__in=product_ids)
        variants = ProductVariant.objects.filter(id__in=product_variants_ids)
        boards = BoardParams.objects.filter(id__in=board_ids)
        sauces = PizzaSauce.objects.filter(id__in=sauce_ids)
        addons = AddonParams.objects.filter(id__in=addons_ids)

        product_map = {str(p.id): p for p in products}
        variant_map = {str(v.id): v for v in variants}
        board_map = {str(b.id): b for b in boards}
        sauce_map = {str(s.id): s for s in sauces}
        addon_map = {str(a.id): a for a in addons}

        for item_key, item in self.cart.items():
            product = product_map.get(str(item["product_id"]))
            variant = variant_map.get(str(item["variant_id"])) if item["variant_id"] else None
            board1 = board_map.get(str(item["board1_id"])) if item["board1_id"] else None
            board2 = board_map.get(str(item["board2_id"])) if item["board2_id"] else None
            sauce = sauce_map.get(str(item["sauce_id"])) if item["sauce_id"] else None
            item_addons = [addon_map.get(str(aid)) for aid in item["addons_ids"] if addon_map.get(str(aid))]

            total_price = Decimal(0)
            if product and variant:
                base_price = variant.price
                board1_price = board1.price if board1 else Decimal(0)
                board2_price = board2.price if board2 else Decimal(0)
                addons_price = sum(a.price for a in item_addons)

                total_price = (base_price + board1_price + board2_price + addons_price) * item["quantity"]

            item["product"] = product
            item["variant"] = variant
            item["board1"] = board1
            item["board2"] = board2
            item["sauce"] = sauce
            item["addons"] = item_addons
            item["total_price"] = str(total_price.quantize(Decimal("0.01")))  # Store as string to be safe
            item["item_key"] = item_key
            yield item

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    def get_total_price(self):
        total = Decimal("0")
        for item in self.cart.values():
            price = item["total_price"]
            if isinstance(price, Decimal):
                total += price
            else:
                total += Decimal(str(price))
        return total.quantize(Decimal("0.01"))

    def clear(self):
        del self.session[CART_SESSION_ID]
        self.save()

    def get_item_key(self, product_id, variant_id, board1_id, board2_id, sauce_id, addons_ids, drink):
        product_id_str = str(product_id)
        variant_id_str = str(variant_id) if variant_id else ""

        item_key_parts = [product_id_str, variant_id_str]
        if board1_id:
            item_key_parts.append(f"b1_{board1_id}")
        if board2_id:
            item_key_parts.append(f"b2_{board2_id}")
        if sauce_id:
            item_key_parts.append(f"s_{sauce_id}")
        if addons_ids:
            item_key_parts.append(f'a_{"_".join(map(str, sorted(addons_ids)))}')
        if drink:
            item_key_parts.append(f"d_{drink}")

        return "-".join(item_key_parts)
