from typing import Union

from datetime import datetime

# My Modules
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database import Select

from bot.tg_module.functions import get_coordinate_button_by_callback_data

from bot.tg_module.handlers.functions import CatalogCallback
from bot.tg_module.handlers.functions import InteractionProduct
from bot.tg_module.handlers.functions import CounterProductItemCartCallback
from bot.tg_module.handlers.functions import PersonalAreaCallback
from bot.tg_module.handlers.functions import PurchasesCallback
from bot.tg_module.handlers.functions import OrderingCartCallback
from bot.tg_module.handlers.functions import FavoritesCallback
from bot.tg_module.handlers.functions import OtherCallback


_close_button = InlineKeyboardButton(text="❌", callback_data=OtherCallback(action="close").pack())


def _paging_button(category_id: int, product_id: int, direction: str):
    """Получить кнопку листания вправо-влево"""
    text = '«' if direction == "left" else '»'
    callback_data = CatalogCallback(category_id=category_id, product_id=product_id, paging_direction=direction).pack()
    return InlineKeyboardButton(text=text, callback_data=callback_data)


def _back_button(last_callback_data: Union[CatalogCallback, PersonalAreaCallback, OrderingCartCallback]):
    """Кнопка возврата"""
    return InlineKeyboardButton(text="🔙", callback_data=last_callback_data.pack())


def _smile_by_bool(condition, var="check") -> str:
    d_smile = {
        "check": ['✅', '☑'],
        "heart": ['❤', '🤍'],
        "payment_status": ['✅', '❌']
    }
    smile_arr = d_smile[var]
    if condition is None:
        return '❌'
    return smile_arr[0] if condition else smile_arr[-1]


def view_categories(categories_array: list,
                    width: int = 2) -> InlineKeyboardMarkup:
    """Клавиатура выбора категории товара"""
    builder = InlineKeyboardBuilder()

    for (category_id, category_name,) in categories_array:
        text = category_name
        callback_data = CatalogCallback(category_id=category_id).pack()
        builder.button(text=text, callback_data=callback_data)

    builder.adjust(width)
    builder.row(_close_button)

    return builder.as_markup()


def view_products_by_category(products_array: list,
                              width: int = 2,
                              add_paging_btn: bool = True) -> InlineKeyboardMarkup:
    """Вывести список товаров по категории"""
    builder = InlineKeyboardBuilder()
    category_id = products_array[0][0]
    start_product_id = products_array[0][1]
    stop_product_id = products_array[-1][1]

    for (category_id, product_id, product_name,) in products_array:
        text = product_name
        callback_data = CatalogCallback(category_id=category_id, product_id=product_id).pack()
        builder.button(text=text, callback_data=callback_data)

    builder.adjust(width)

    if add_paging_btn:
        """Добавляем кнопки пролистывания"""
        left_paging_btn = _paging_button(category_id, start_product_id, "left")
        right_paging_btn = _paging_button(category_id, stop_product_id, "right")

        builder.row(left_paging_btn, right_paging_btn)

    builder.row(_back_button(CatalogCallback()))

    return builder.as_markup()


def view_product_item(product_item_data: list,
                      callback_data: Union[CatalogCallback,
                                           FavoritesCallback,
                                           InteractionProduct]) -> InlineKeyboardMarkup:
    """Карточка товара"""
    type_callback_data = type(callback_data)

    builder = InlineKeyboardBuilder()

    [category_id,
     product_id,
     product_name,
     manufacturer_name,
     description,
     is_favorite,
     product_price,
     number_in_cart,
     number_in_store] = product_item_data

    # Определяем last_state
    last_state = ''

    if type_callback_data is InteractionProduct:
        last_state = callback_data.last_state

    elif type_callback_data is CatalogCallback:
        last_state = "Catalog"

    elif type_callback_data is FavoritesCallback:
        last_state = "Favorites"

    # Назначаем last_callback для back_button
    last_callback = ''
    if last_state == "Catalog":
        last_callback = CatalogCallback(category_id=category_id)

    elif last_state == "Favorites":
        last_callback = PersonalAreaCallback(view_favorites=True)

    # Создаём кнопки
    builder.button(text="Изменение цены", callback_data=OtherCallback(action="view", value="Изменение цены").pack())
    builder.button(text=f"{product_price} ₽",
                   callback_data=OtherCallback(action="view", value=f"{product_price} ₽").pack())
    builder.add(_back_button(last_callback))
    builder.button(text="🛒" + (f"({number_in_cart})" if number_in_cart else ""),
                   callback_data=InteractionProduct(product_id=product_id,
                                                    last_state=last_state,
                                                    add_in_cart=True).pack())
    builder.button(text=_smile_by_bool(is_favorite, var="heart"),
                   callback_data=InteractionProduct(product_id=product_id,
                                                    last_state=last_state,
                                                    add_in_favorites=True).pack())

    builder.adjust(2, 3)

    return builder.as_markup()


def counter_product_item(callback: CallbackQuery,
                         number_product: int,
                         row_ind: int,
                         btn_ind: int):
    """Изменение количества товаров перед добавлением в корзину"""
    current_keyboard = callback.message.reply_markup.dict()

    current_keyboard['inline_keyboard'][row_ind][btn_ind]['text'] = number_product

    return current_keyboard


def add_in_favorites(callback: CallbackQuery, callback_data: InteractionProduct, is_favorite: bool):
    """Изменяем состояние сердечка"""
    current_keyboard = callback.message.reply_markup.dict()
    [row_ind, btn_ind] = get_coordinate_button_by_callback_data(current_keyboard['inline_keyboard'], callback_data.pack())

    current_keyboard['inline_keyboard'][row_ind][btn_ind]['text'] = _smile_by_bool(is_favorite, var="heart")

    return current_keyboard


def personal_area() -> InlineKeyboardMarkup:
    """Личный кабинет"""
    builder = InlineKeyboardBuilder()

    builder.button(text="Покупки", callback_data=PersonalAreaCallback(view_purchases=True).pack())
    builder.button(text="Избранное", callback_data=PersonalAreaCallback(view_favorites=True).pack())
    builder.button(text="Корзина", callback_data=PersonalAreaCallback(view_cart=True).pack())
    builder.add(_close_button)

    builder.adjust(1, 2, 1)

    return builder.as_markup()


def view_purchases(purchases_array: list, width: int = 1) -> InlineKeyboardMarkup:
    """Покупки"""
    builder = InlineKeyboardBuilder()

    for (purchase_id,
         store_id,
         purchase_date,
         payment_status) in purchases_array:
        text = f"Заказ № {purchase_id} {_smile_by_bool(payment_status, var='payment_status')}"
        callback_data = PurchasesCallback(purchase_id=purchase_id)
        builder.button(text=text, callback_data=callback_data)

    builder.adjust(width)
    builder.row(_back_button(PersonalAreaCallback()))

    return builder.as_markup()


def view_purchase_item() -> InlineKeyboardMarkup:
    """Конкретная покупка"""
    builder = InlineKeyboardBuilder()

    builder.add(_back_button(PersonalAreaCallback(view_purchases=True)))

    return builder.as_markup()


def view_favorites(products_array: list, width: int = 1) -> InlineKeyboardMarkup:
    """Избранное"""
    builder = InlineKeyboardBuilder()

    for (category_id, product_id, product_name,) in products_array:
        text = product_name
        callback_data = FavoritesCallback(product_id=product_id).pack()
        builder.button(text=text, callback_data=callback_data)

    builder.adjust(width)
    builder.row(_back_button(PersonalAreaCallback()))

    return builder.as_markup()


def view_cart(user_info_data: list, cart_item_data: list, width: int = 2) -> InlineKeyboardMarkup:
    """Корзина"""
    builder = InlineKeyboardBuilder()
    total_price = 0

    [user_id,
     user_name,
     joined,
     favorites_products,
     default_store_id] = user_info_data

    # Список товаров
    for (category_id,
         product_id,
         product_name,
         manufacturer_name,
         description,
         product_selected,
         product_price,
         number_in_cart,
         number_in_store,) in cart_item_data:

        if number_in_store == 0:
            product_selected = None

        price_product_cart_item = float(product_price) * number_in_cart
        if product_selected:
            total_price += price_product_cart_item

        product_btn = InlineKeyboardButton(text=product_name,
                                           callback_data=OrderingCartCallback(view_cart=True,
                                                                              product_id=product_id).pack())
        selected_btn_text = f"{price_product_cart_item} ₽ ({number_in_cart} шт.) {_smile_by_bool(product_selected)}"
        selected_btn = InlineKeyboardButton(text=selected_btn_text,
                                            callback_data=OrderingCartCallback(view_cart=True,
                                                                               product_id=product_id,
                                                                               product_selected=True).pack())
        builder.row(product_btn, selected_btn)

    builder.adjust(width)

    # Остальные кнопки
    total_price_btn_text = f"Итог: {total_price} ₽"
    if default_store_id is None:
        select_store_btn_text = "Выберите пунки выдачи заказа"
    else:
        [store_id, store_name, address] = Select.store_data_by_id(default_store_id)
        select_store_btn_text = f"{store_name} ({address})"
    ordering_btn_text = "Оформить заказ"

    total_price_btn = InlineKeyboardButton(text=total_price_btn_text,
                                           callback_data=OtherCallback(action="view", value="Итоговая стоимость").pack())
    back_btn = _back_button(PersonalAreaCallback())
    select_store_btn = InlineKeyboardButton(text=select_store_btn_text,
                                            callback_data=OrderingCartCallback(view_cart=True, select_store=True).pack())
    ordering_btn = InlineKeyboardButton(text=ordering_btn_text,
                                        callback_data=OrderingCartCallback(view_cart=True,
                                                                           ordering=True).pack())

    builder.row(total_price_btn)
    builder.row(select_store_btn)
    builder.row(back_btn, ordering_btn)

    return builder.as_markup()


def view_product_item_in_cart(product_item_in_cart_data: list) -> InlineKeyboardMarkup:
    """Карточка товара в корзине"""
    builder = InlineKeyboardBuilder()

    [category_id,
     product_id,
     product_name,
     manufacturer_name,
     description,
     product_selected,
     product_price,
     number_in_cart,
     number_in_store] = product_item_in_cart_data

    total_price = number_in_cart * product_price

    product_price_btn = InlineKeyboardButton(text=f"{product_price} ₽", callback_data="product_price")
    count_product_btn = InlineKeyboardButton(text=str(number_in_cart), callback_data="number_product")
    total_price_btn = InlineKeyboardButton(text=f"{total_price} ₽",
                                           callback_data=OtherCallback(action="view", value="Итоговая сумма").pack())
    minus_btn = InlineKeyboardButton(text="➖",
                                     callback_data=CounterProductItemCartCallback(product_id=product_id,
                                                                                  minus=True).pack())
    plus_btn = InlineKeyboardButton(text="➕",
                                    callback_data=CounterProductItemCartCallback(product_id=product_id,
                                                                                 plus=True).pack())
    back_btn = _back_button(PersonalAreaCallback(view_cart=True))
    delete_product_item_btn = InlineKeyboardButton(text="Удалить",
                                                   callback_data=OrderingCartCallback(view_cart=True,
                                                                                      product_id=product_id,
                                                                                      product_delete=True).pack())
    builder.row(product_price_btn, count_product_btn, total_price_btn)
    builder.row(minus_btn, plus_btn)
    builder.row(back_btn, delete_product_item_btn)

    return builder.as_markup()


def view_stores(stores_array: list,
                width: int = 1,
                length: int = 5) -> InlineKeyboardMarkup:
    """Выбор ПВЗ"""
    builder = InlineKeyboardBuilder()

    for (store_id, store_name, address, description) in stores_array:
        text = f"{store_name} ({address})"
        callback_data = OrderingCartCallback(view_cart=True, store_id=store_id).pack()
        builder.button(text=text, callback_data=callback_data)

    builder.adjust(width, length)

    back_btn = _back_button(PersonalAreaCallback(view_cart=True))
    builder.row(back_btn)

    return builder.as_markup()


def ordering(purchase_id: int) -> InlineKeyboardMarkup:
    """Оформление заказа"""
    builder = InlineKeyboardBuilder()

    payment_time = int((datetime.now().replace(tzinfo=None) - datetime.fromtimestamp(0)).total_seconds())

    builder.button(text="Оплатить", callback_data=OrderingCartCallback(payment=True,
                                                                       purchase_id=purchase_id,
                                                                       payment_time=payment_time).pack())

    builder.adjust(3)

    return builder.as_markup()
