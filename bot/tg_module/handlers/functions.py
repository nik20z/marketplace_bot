from typing import Union

from aiogram.filters.callback_data import CallbackData

# My Modules
from bot.database import Select


class CatalogCallback(CallbackData, prefix="cc"):
    """Каталог"""
    category_id: int = 0
    product_id: int = 0
    paging_direction: str = "empty"


class InteractionProduct(CallbackData, prefix="ip"):
    """Взаимодействие с товаром"""
    product_id: int = 0
    last_state: str = "CatalogCallback"
    add_in_favorites: bool = False
    add_in_cart: bool = False


class CounterProductItemCartCallback(CallbackData, prefix="cpicc"):
    """Счётчик количество товаров в Корзине"""
    minus: bool = False
    plus: bool = False
    product_id: int = 0


class PersonalAreaCallback(CallbackData, prefix="pac"):
    """Личный кабинет"""
    view_purchases: bool = False
    view_favorites: bool = False
    view_cart: bool = False


class OrderingCartCallback(CallbackData, prefix="opc"):
    """Взаимодействие с корзиной"""
    product_id: int = 0  # id товара, с которым происходит взаимодействие

    product_selected: bool = False  # Отметить товар в корзине
    product_delete: bool = False  # Удалить товар из корзины

    select_store: bool = False  # Окно выбора ПВЗ
    store_id: int = 0  # Выбранный ПВЗ
    ordering: bool = False  # Оформление заказа
    purchase_id: int = 0  # Номер заказа, который необходимо оплатить
    payment_time: int = 0  # время в секундах от момента нажатия на кнопку "Оформить"
    payment: bool = False  # Высталение счёта


class FavoritesCallback(CallbackData, prefix="fc"):
    """Избранное"""
    product_id: int = 0


class PurchasesCallback(CallbackData, prefix="pc"):
    """Покупки"""
    purchase_id: int = 0


class OtherCallback(CallbackData, prefix="oc"):
    """Прочие колбэки"""
    action: str = ""
    value: Union[str, int] = None


def get_index_product(products_array: list, current_product_id: int) -> int:
    """Получить индекс """
    ind = 0
    for (category_id, product_id, product_name,) in products_array:
        if product_id == current_product_id:
            break
        ind += 1
    return ind


def get_array_slice(array: list,
                    ind: int,
                    limit: int,
                    mode: str = 'left') -> list:
    """Получить корректный срез массива"""
    len_array = len(array)
    limit = min(limit, len_array)

    start_ind = ind
    stop_ind = start_ind + limit

    if mode == 'left':
        start_ind = ind - limit
        stop_ind = ind

    elif mode == 'right':
        start_ind += 1
        stop_ind = start_ind + limit

    if stop_ind == 0:
        return array[-(len_array % limit):]

    if start_ind == len_array:
        return array[:limit]

    if start_ind < 0:
        return array[start_ind:] + array[:stop_ind]

    if stop_ind > len_array:
        return array[start_ind:]

    return array[start_ind:stop_ind]


def get_current_and_number_list(array: list,
                                ind: int,
                                paging_direction: str,
                                default_limit: int) -> list:
    """Получить текущую страницу"""
    len_array = len(array)
    number_list = len_array // default_limit + 1

    if (paging_direction in ('empty', 'right',) and ind == 0) or ind == (len_array - 1):
        current_list = 1

    elif paging_direction == 'left' and ind == 0:
        current_list = number_list

    else:
        if paging_direction == 'left':
            ind -= 1
        elif paging_direction == 'right':
            ind += 1

        current_list = ind // default_limit + 1

    return [current_list, number_list]


def get_purchase_item_text(purchase_id: int,
                           store_data: list,
                           products_data: list,
                           payment_status: bool = False) -> str:
    """Сообщение с информацией о заказе"""
    payment_status_text = '✅' if payment_status else '❌' if not payment_status else 'NULL'

    [store_id,
     store_name,
     address] = store_data

    text = f"<b>Заказ №</b> <code>{purchase_id}</code>\n" \
           f"<b>Статус оплаты</b>: {payment_status_text}\n"

    last_category_id = 0
    total_price = 0

    for (category_id,
         product_id,
         product_name,
         manufacturer_name,
         description,
         product_selected,
         product_price,
         number_in_cart,
         number_in_store,) in products_data:
        """Перебираем список товаров"""

        if category_id != last_category_id:
            last_category_id = category_id
            category_name = Select.category_name_by_id(category_id)
            text += f"\n{category_name}\n"

        number_product = min(number_in_cart, number_in_store)
        price_product_item = float(product_price) * number_in_cart

        text += f"🔹 {product_name} <code>{product_price} × {number_product} шт = {price_product_item} ₽</code>\n"

        total_price += price_product_item

    text += f"\n" \
            f"<b>Пункт выдачи заказа</b>:\n" \
            f"{store_name} ({address})\n"

    text += f"\n" \
            f"<b>Итог</b>: <code>{total_price} ₽</code>"

    return text
