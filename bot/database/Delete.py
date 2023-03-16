from typing import Union

# My Modules
from bot.database.connect import cursor, connection


def send_query(query_text: str) -> list:
    """Произвольный запрос"""
    cursor.execute(query_text)
    connection.commit()
    return cursor.fetchall()


def product_item_in_cart(user_id: int,
                         products_id_array: Union[int, list] = None,
                         only_product_selected: bool = False) -> None:
    """Удалить товары из корзины"""
    query = "DELETE FROM cart_item WHERE user_id = %s "

    if products_id_array is not None:

        if type(products_id_array) is int:
            products_id_array = [products_id_array]
        query += " AND product_id = ANY(ARRAY[{0}])".format(products_id_array)

    if only_product_selected:
        query += "AND product_selected"

    cursor.execute(query, (user_id,))

    connection.commit()
