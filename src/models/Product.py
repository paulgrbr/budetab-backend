class ProductCategory:
    def __init__(self, category_id: int, category_name: str):
        self.category_id = category_id
        self.category_name = category_name


class Beverage:
    def __init__(self, product_id: int, product_name: str, category_id: int, beverage_size: float, pricing: dict):
        self.product_id = product_id
        self.product_name = product_name
        self.category_id = category_id
        self.beverage_size = beverage_size
        self.pricing = pricing


class Product:
    def __init__(self, product_id: int, product_name: str, category_id: int,
                 product_type: str, profile_picture_path: str):
        self.product_id = product_id
        self.product_name = product_name
        self.category_id = category_id
        self.product_type = product_type
        self.profile_picture_path = profile_picture_path
