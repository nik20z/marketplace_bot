from datetime import datetime

# My Modules
from bot.database.connect import cursor, connection


def send_query(query_text: str) -> list:
    """Произвольный запрос"""
    cursor.execute(query_text)
    return cursor.fetchall()


def new_user(new_user_data: tuple) -> None:
    """Заносим данные о новом пользователе"""
    query = "INSERT INTO telegram (user_id, user_name, joined) VALUES (%s, %s, %s);"
    cursor.execute(query, new_user_data)
    connection.commit()


def cart_item(cart_item_data: tuple) -> None:
    """Добавляем товар в корзину"""
    query = """INSERT INTO cart_item (user_id, product_id, product_count) 
               VALUES (%s, %s, %s) 
               ON CONFLICT (user_id, product_id) DO UPDATE
               SET product_count = cart_item.product_count + EXCLUDED.product_count;"""

    cursor.execute(query, cart_item_data)
    connection.commit()


def create_purchase(user_id: int, store_id: int, cart_item_data: list) -> int:
    """Занести данные о заказе"""
    purchase_date = datetime.now().replace(tzinfo=None)

    query = "INSERT INTO purchase (user_id, store_id, purchase_date) VALUES (%s, %s, %s) RETURNING purchase_id;"
    cursor.execute(query, (user_id, store_id, purchase_date,))
    purchase_id = cursor.fetchone()[0]

    # Список товаров
    purchase_item_data = list()
    for (category_id,
         product_id,
         product_name,
         manufacturer_name,
         description,
         product_selected,
         product_price,
         number_in_cart,
         number_in_store,) in cart_item_data:
        purchase_item_data.append((purchase_id, product_id, number_in_cart, product_price))

    query = "INSERT INTO purchase_item (purchase_id, product_id, product_count, product_price) VALUES (%s, %s, %s, %s);"
    cursor.executemany(query, purchase_item_data)

    return purchase_id
