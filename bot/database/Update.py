from typing import Union

# My Modules
from bot.database.connect import cursor, connection


def send_query(query_text: str) -> list:
    """Произвольный запрос"""
    cursor.execute(query_text)
    connection.commit()
    return cursor.fetchall()


def add_in_favorites(user_id: int, product_id: int) -> bool:
    """Добавить товар в избранное"""
    query = """UPDATE telegram
                SET favorites_products = CASE 
                    WHEN NOT {1} = ANY(favorites_products)
                        THEN array_append(favorites_products, {1}::smallint)
                    ELSE array_remove(favorites_products, {1}::smallint)
                    END
                WHERE user_id = {0}
                RETURNING {1} = ANY(favorites_products);
                """.format(user_id, product_id)
    cursor.execute(query)
    connection.commit()
    return cursor.fetchone()[0]


def cart_item_product_selected(user_id: int, product_id: int) -> bool:
    """Редактируем отметку выбора товара в корзине"""
    query = """UPDATE cart_item 
               SET product_selected = NOT product_selected 
               WHERE user_id = {0} AND product_id = {1}
               RETURNING product_selected;""".format(user_id, product_id)
    cursor.execute(query)
    connection.commit()
    return cursor.fetchone()[0]


def count_product_item_cart(user_id: int,
                            product_id: int,
                            mode: str) -> int:
    """Изменение количества товаров в корзине"""
    query = """UPDATE cart_item 
               SET product_count = 
                    CASE 
                        WHEN number_in_store_product.val = 0
                            THEN 1
                        WHEN %s = 'minus' AND product_count > 1
                            THEN product_count - 1
                        WHEN %s = 'minus' AND product_count = 1
                            THEN number_in_store_product.val
                        WHEN %s = 'plus' AND product_count < number_in_store_product.val
                            THEN product_count + 1
                        ELSE 1
                    END
               FROM (SELECT number_in_store(%s) AS val) AS number_in_store_product
               WHERE user_id = %s AND product_id = %s
               RETURNING product_count;"""
    cursor.execute(query, (mode, mode, mode, product_id, user_id, product_id, ))
    connection.commit()
    return cursor.fetchone()[0]


def user_info(user_id: int,
              column_name: str,
              value: Union[str, int]) -> None:
    """Обновляем информацию о пользователе по названию колонки"""
    query = "UPDATE telegram SET {0} = %s WHERE user_id = %s;".format(column_name)
    cursor.execute(query, (value, user_id,))
    connection.commit()


def payment_status(purchase_id: int, value: bool = True) -> bool:
    """Обновить статус оплаты"""
    query = "UPDATE purchase SET payment_status = %s WHERE purchase_id = %s RETURNING payment_status;"
    cursor.execute(query, (value, purchase_id,))
    connection.commit()
    return cursor.fetchone()[0]
