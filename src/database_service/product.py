from numpy import double
import psycopg2
import psycopg2.extras
import sys
import os

from models.Product import Beverage, Product, ProductCategory

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), './')))

from database_service.connection import *  # noqa


def create_category(title: str):
    try:
        conn = get_auth_db_connection()
        cur = conn.cursor()

        cur.execute('''
                    INSERT INTO "product_category"(category_name)
                    VALUES
                    (%s);
                    ''',
                    (title,))
        conn.commit()
        cur.close()
        conn.close()
        return {"error": None, "message": {"categoryName": title}}

    except psycopg2.errors.UniqueViolation as Err:
        conn.rollback()
        conn.close()
        return {"error": {"exception": Err.__class__.__name__,
                          "message": "Category with this name already exists", "pgCode": Err.pgcode}, "message": None}

    except psycopg2.Error as Err:
        conn.rollback()  # Rollback in case of error
        conn.close()
        return {"error": {"exception": Err.__class__.__name__, "message": str(
            Err.diag.message_primary), "pgCode": Err.pgcode}, "message": None}


def get_all_product_categories():
    conn = get_auth_db_connection()
    cur = conn.cursor()
    cur.execute('''
                SELECT category_id, category_name
                FROM "product_category"
                '''
                )
    response = cur.fetchall()
    cur.close()
    conn.close()

    parsed_response = []
    for row in response:
        parsed_response.append(ProductCategory(row[0], row[1]))
    return parsed_response


def create_beverage(product_name: str, category_id: int, beverage_size: float, pricing: float):
    try:
        conn = get_auth_db_connection()
        cur = conn.cursor()

        cur.execute('''
                    INSERT INTO "product"(product_name, category_id, product_type)
                    VALUES
                    (%s, %s, 'beverage')
                    RETURNING product_id;
                    ''',
                    (product_name, category_id))
        product_id = cur.fetchone()[0]
        cur.execute('''
                    INSERT INTO "beverage"(product_id, beverage_size)
                    VALUES
                    (%s, %s);
                    ''',
                    (product_id, beverage_size))

        PRICING_KEY_MAPPING = {
            "normal": "normal",
            "party": "party",
            "bigEvent": "big_event"
        }
        pricing_values = [(product_id, PRICING_KEY_MAPPING[key], price) for key, price in pricing.items()]
        # Bulk insert into pricing table
        cur.executemany('''
                        INSERT INTO pricing (product_id, pricing_type, price)
                        VALUES (%s, %s, %s);
                        ''',
                        pricing_values
                        )

        conn.commit()
        cur.close()
        conn.close()
        return {"error": None, "message": {"productId": product_id, "status": "Beverage added successfully"}}

    except psycopg2.Error as Err:
        conn.rollback()  # Rollback in case of error
        conn.close()
        return {"error": {"exception": Err.__class__.__name__, "message": str(
            Err.diag.message_primary), "pgCode": Err.pgcode}, "message": None}


def get_all_beverages():
    conn = get_auth_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute('''
                SELECT p.product_id, p.product_name, p.category_id, b.beverage_size, pr.pricing_type, pr.price
                FROM product p
                JOIN beverage b ON(p.product_id = b.product_id)
                JOIN pricing pr ON(p.product_id = pr.product_id)
                '''
                )
    response = cur.fetchall()
    cur.close()
    conn.close()

    PRICING_KEY_MAPPING = {
        "normal": "normal",
        "party": "party",
        "big_event": "bigEvent"
    }

    # Dictionary to group products by product_id
    products_dict = {}

    for row in response:
        product_id = int(row["product_id"])
        product_name = str(row["product_name"])
        category_id = int(row["category_id"])
        beverage_size = float(row["beverage_size"])
        pricing_type = str(row["pricing_type"])
        price = float(row["price"])

        if product_id not in products_dict:
            products_dict[product_id] = {
                "product_id": product_id,
                "product_name": product_name,
                "category_id": category_id,
                "beverage_size": beverage_size,
                "pricing": {}
            }

        # Map pricing type using PRICING_KEY_MAPPING
        pricing_key = PRICING_KEY_MAPPING.get(pricing_type, pricing_type)
        products_dict[product_id]["pricing"][pricing_key] = price

    # Convert dictionary to a list of Product objects
    products_array = [
        Beverage(
            product_id=data["product_id"],
            product_name=data["product_name"],
            category_id=data["category_id"],
            beverage_size=data["beverage_size"],
            pricing=data["pricing"]
        )
        for data in products_dict.values()
    ]

    return products_array


def get_product_by_product_id(product_id: int):
    conn = get_auth_db_connection()
    cur = conn.cursor()
    cur.execute('''
                SELECT product_id, product_name, category_id, product_type
                FROM product
                WHERE product_id = %s
                ''',
                (product_id, ))
    response = cur.fetchone()
    cur.close()
    conn.close()
    if response:
        return Product(response[0], response[1], response[2], response[3], "")
    else:
        return None


def update_product_picture_path(product_id: int, path: str):
    try:
        conn = get_auth_db_connection()
        cur = conn.cursor()
        cur.execute('''
                    UPDATE product
                    SET product_picture_path = %s
                    WHERE product_id = %s
                    ''',
                    (
                        path,
                        product_id,
                    ))
        conn.commit()
        cur.close()
        conn.close()
        return {"error": None, "message": {"status": "Picture uploaded successfully", "productId": product_id}}

    except psycopg2.Error as Err:
        conn.rollback()
        conn.close()
        return {"error": {"exception": Err.__class__.__name__, "message": str(
            Err.diag.message_primary), "pgCode": Err.pgcode}, "message": None}


def get_product_picture_path_by_product_id(product_id: int):
    conn = get_auth_db_connection()
    cur = conn.cursor()
    cur.execute('''
                SELECT product_picture_path
                FROM product
                WHERE product_id = %s
                ''',
                (product_id, ))
    response = cur.fetchone()
    cur.close()
    conn.close()
    if response:
        return response[0]
    else:
        return None
