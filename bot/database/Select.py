from typing import Union

# My Modules
from bot.database.connect import cursor


def send_query(query_text: str) -> list:
    """Произвольный запрос"""
    cursor.execute(query_text)
    return cursor.fetchall()


def user_info(user_id: int) -> list:
    """Информация о пользователе"""
    query = "SELECT user_id, user_name, joined, favorites_products, default_store_id FROM telegram WHERE user_id = %s;"
    cursor.execute(query, (user_id,))
    return cursor.fetchone()


def user_info_by_column_name(user_id: int, column_name: str) -> Union[str, int, list]:
    """Получить информацию о пользователе по названию колонки"""
    query = "SELECT {0} FROM telegram WHERE user_id = %s;".format(column_name)
    cursor.execute(query, (user_id,))
    return cursor.fetchone()[0]


def user_purchases_array(user_id: int,
                         purchases_id_array: Union[int, list] = None,
                         payment: bool = None) -> list:
    """Данные о заказах пользователя"""
    query = "SELECT purchase_id, store_id, purchase_date, payment_status FROM purchase WHERE user_id = %s "

    if purchases_id_array is None:

        if payment is None:
            cursor.execute(query, (user_id,))
        else:
            query += "AND payment = %s;"
            cursor.execute(query, (user_id, payment,))

    else:
        if type(purchases_id_array) is int:
            purchases_id_array = [purchases_id_array]

        query += "AND purchase_id = ANY(ARRAY[%s]);"
        cursor.execute(query, (user_id, purchases_id_array,))

    return cursor.fetchall()


def favorites_products_array(user_id: int) -> list:
    """Список избранных товаров"""
    query = "SELECT favorites_products FROM telegram WHERE user_id = %s;"
    cursor.execute(query, (user_id,))
    return cursor.fetchone()[0]


def categories() -> list:
    """Список категорий"""
    query = "SELECT category_id, category_name FROM category;"
    cursor.execute(query)
    return cursor.fetchall()


def products_array(category_id: int = None,
                   products_id_array: list = None,
                   limit: Union[int, str] = 5) -> list:
    """Список товаров по категории или по массиву id товаров"""
    if products_id_array is None:
        products_id_array = []

    if category_id is not None:
        query = """SELECT category_id, product_id, product_name 
                   FROM product 
                   WHERE category_id = %s 
                   ORDER BY product_name
                   LIMIT {0};""".format(limit)
        cursor.execute(query, (category_id,))

    elif products_id_array:
        query = """SELECT category_id, product_id, product_name 
                   FROM product 
                   WHERE product_id = ANY(ARRAY[%s]) 
                   ORDER BY product_name
                   LIMIT {0};""".format(limit)
        cursor.execute(query, (products_id_array,))

    return cursor.fetchall()


def product_item_data(user_id: int, product_id: int) -> list:
    """Данные о товаре"""
    query = """SELECT category_id, 
                      product_id, 
                      product_name, 
                      m.manufacturer_name,
                      description, 
                      product_id = ANY(ARRAY[(SELECT favorites_products FROM telegram WHERE user_id = %s)]),
                      (SELECT price_product(product.product_id)),
                      (SELECT number_in_cart(%s, product.product_id)),
                      (SELECT number_in_store(product.product_id))
               FROM product
               LEFT JOIN manufacturer m on m.manufacturer_id = product.manufacturer_id
               WHERE product_id = %s;"""
    cursor.execute(query, (user_id, user_id, product_id,))
    return cursor.fetchone()


def cart_item_data(user_id: int,
                   product_id: int = None,
                   product_selected: bool = False) -> list:
    """Список товаров в корзине"""
    where_product_id = ""
    where_product_selected = ""

    if product_id is not None:
        where_product_id = "AND cart_item.product_id = {0}".format(product_id)

    if product_selected:
        where_product_selected = "AND product_selected AND number_in_store(p.product_id) > 0"

    query = """SELECT p.category_id, 
                      cart_item.product_id, 
                      p.product_name, 
                      m.manufacturer_name,
                      p.description, 
                      product_selected, 
                      (SELECT price_product(p.product_id)),
                      product_count, 
                      (SELECT number_in_store(p.product_id))
               FROM cart_item 
               LEFT JOIN product p ON p.product_id = cart_item.product_id
               LEFT JOIN manufacturer m on m.manufacturer_id = p.manufacturer_id
               WHERE user_id = %s {0} {1}
               ORDER BY p.category_id, p.product_name;
               """.format(where_product_id, where_product_selected)
    cursor.execute(query, (user_id,))

    if product_id is None:
        return cursor.fetchall()
    else:
        return cursor.fetchone()


def stores_array() -> list:
    """Список магазинов"""
    query = "SELECT store_id, store_name, address, description FROM store;"
    cursor.execute(query)
    return cursor.fetchall()


def number_in_cart(user_id: int, product_id: int) -> int:
    """Количество товаров в корзине"""
    query = """SELECT number_in_cart(%s, %s);"""
    cursor.execute(query, (user_id, product_id,))
    return cursor.fetchone()[0]


def number_in_store(product_id: int) -> int:
    """Количество товара на складе"""
    query = """SELECT number_in_store(%s);"""
    cursor.execute(query, (product_id,))
    return cursor.fetchone()[0]


def free_number_product(user_id: int, product_id: int) -> int:
    """Оставшееся количество товаров на складе"""
    query = "SELECT free_number_product(%s, %s);"
    cursor.execute(query, (user_id, product_id,))
    return int(cursor.fetchone()[0])


def category_name_by_id(category_id: int) -> str:
    """Получить название категории по id"""
    query = "SELECT COALESCE(category_name, '') FROM category WHERE category_id = %s;"
    cursor.execute(query, (category_id,))
    return cursor.fetchone()[0]


def store_data_by_id(store_id: int) -> list:
    """Получить название магазина по id"""
    query = "SELECT store_id, COALESCE(store_name, ''), address FROM store WHERE store_id = %s;"
    cursor.execute(query, (store_id,))
    return cursor.fetchone()


def purchase_products_data(purchase_id: int) -> list:
    """Список товаров в заказе"""
    query = """SELECT p.category_id, 
                      purchase_item.product_id, 
                      p.product_name,
                      m.manufacturer_name, 
                      p.description, 
                      True, 
                      product_price,
                      product_count, 
                      product_count
               FROM purchase_item 
               LEFT JOIN product p ON p.product_id = purchase_item.product_id
               LEFT JOIN manufacturer m on p.manufacturer_id = m.manufacturer_id
               WHERE purchase_id = %s
               ORDER BY p.category_id, p.product_name;
               """
    cursor.execute(query, (purchase_id,))

    return cursor.fetchall()


def check_payment_purchase(purchase_id: int) -> bool:
    """Проверить оплачен ли заказ"""
    query = "SELECT payment_status FROM purchase WHERE purchase_id = %s;"
    cursor.execute(query, (purchase_id,))
    return cursor.fetchone()[0]
