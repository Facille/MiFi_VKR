def find_product(products, product_id):
    for product in products:
        if product["id"] == product_id:
            return product
    return None
