import asyncio

from aiogram import F
from aiogram import Router
from aiogram.methods import DeleteMessage
from aiogram.filters import Text
from aiogram.filters import Command
from aiogram.types import Update
from aiogram.types import Message
from aiogram.types import CallbackQuery

import configparser

from typing import Union

from datetime import datetime

# My Modules
from bot.database import Select
from bot.database import Insert
from bot.database import Update
from bot.database import Delete

from bot.tg_module.functions import get_coordinate_button_by_callback_data

from bot.tg_module.handlers.functions import CatalogCallback
from bot.tg_module.handlers.functions import CounterProductItemCartCallback
from bot.tg_module.handlers.functions import PurchasesCallback
from bot.tg_module.handlers.functions import PersonalAreaCallback
from bot.tg_module.handlers.functions import FavoritesCallback
from bot.tg_module.handlers.functions import OrderingCartCallback
from bot.tg_module.handlers.functions import InteractionProduct
from bot.tg_module.handlers.functions import OtherCallback

from bot.tg_module.handlers.functions import get_index_product
from bot.tg_module.handlers.functions import get_array_slice
from bot.tg_module.handlers.functions import get_current_and_number_list
from bot.tg_module.handlers.functions import get_purchase_item_text

from bot.tg_module.keyboards import Reply
from bot.tg_module.keyboards import Inline

config = configparser.ConfigParser()
config.read("config.ini")

DEFAULT_PAYMENT_TIME = int(config['MAIN']['DEFAULT_PAYMENT_TIME'])

router = Router()


# ____________________ NEW USER ____________________

@router.message(lambda msg: Select.user_info(user_id=msg.chat.id) is None)
async def new_user(message: Message) -> None:
    """Новый пользователь"""
    user_id = message.chat.id
    joined = message.date

    if user_id > 0:
        user_name = message.chat.first_name
        text = "Приветствие для пользователя (^_^)"

    else:
        user_name = message.chat.title
        text = "Извини, но бот не работает в беседах:("

    keyboard = Reply.default()

    new_user_data = (user_id, user_name, joined)
    Insert.new_user(new_user_data)

    await message.answer(text=text, reply_markup=keyboard)


# ____________________ PERSONAL AREA ____________________

@router.message(Text(text="личный кабинет", ignore_case=True))
async def personal_area(message: Message, edit_message: bool = False) -> None:
    """Личный кабинет"""
    user_id = message.chat.id
    user_message_id = message.message_id

    text = "<b>Личный кабинет</b>"
    keyboard = Inline.personal_area()

    if edit_message:
        await message.edit_text(text, reply_markup=keyboard)

    else:
        await message.answer(text, reply_markup=keyboard)
        await DeleteMessage(chat_id=user_id, message_id=user_message_id)


@router.callback_query(PersonalAreaCallback.filter(F.view_purchases))
async def view_purchases(callback: CallbackQuery) -> None:
    """Просмотр покупок"""
    user_id = callback.message.chat.id

    purchases_array = Select.user_purchases_array(user_id)

    text = "<b>Список покупок/заказов</b>"
    keyboard = Inline.view_purchases(purchases_array)
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(PurchasesCallback.filter(F.purchase_id))
async def view_purchase_item(callback: CallbackQuery, callback_data: PurchasesCallback) -> None:
    """Показать информацию о конкретной покупке"""
    user_id = callback.message.chat.id
    purchase_id = callback_data.purchase_id

    purchase_data = Select.user_purchases_array(user_id, purchases_id_array=purchase_id)[0]

    [purchase_id,
     store_id,
     purchase_date,
     payment_status] = purchase_data

    store_data = Select.store_data_by_id(store_id)
    cart_item_data = Select.purchase_products_data(purchase_id)

    text = get_purchase_item_text(purchase_id, store_data, cart_item_data, payment_status=payment_status)
    keyboard = Inline.view_purchase_item()

    await callback.message.edit_text(text=text, reply_markup=keyboard)


@router.callback_query(PersonalAreaCallback.filter(F.view_favorites & ~F.product_id))
async def view_favorites(callback: CallbackQuery) -> None:
    """Просмотр избранного"""
    user_id = callback.message.chat.id

    favorites_products_array = Select.favorites_products_array(user_id)
    products_array = Select.products_array(products_id_array=favorites_products_array)

    text = "<b>Список избранного</b>"
    keyboard = Inline.view_favorites(products_array)
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(FavoritesCallback.filter(F.product_id))
async def view_product_item_in_favorites(callback: CallbackQuery, callback_data: FavoritesCallback):
    """Показать карточку товара из списка Избранное"""
    await view_product_item(callback, callback_data)


@router.callback_query(
    PersonalAreaCallback.filter(~(F.view_cart | F.view_purchases | F.view_favorites) & ~F.product_id))
async def personal_area_callback(callback: CallbackQuery) -> None:
    """Вывести список категорий"""
    await personal_area(callback.message, edit_message=True)


# ____________________ ORDERING CART ____________________

@router.callback_query(PersonalAreaCallback.filter(F.view_cart & ~F.product_id))
async def view_cart(callback: CallbackQuery) -> None:
    """Просмотр корзины"""
    user_id = callback.message.chat.id

    user_info_data = Select.user_info(user_id)
    cart_item_data = Select.cart_item_data(user_id)

    text = "<b>Корзина</b>"
    keyboard = Inline.view_cart(user_info_data, cart_item_data)
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(OrderingCartCallback.filter(F.product_id & ~F.product_selected & ~F.product_delete))
async def view_product_item_in_cart(callback: CallbackQuery,
                                    callback_data: Union[OrderingCartCallback, CounterProductItemCartCallback]) -> None:
    """Карточка товара из корзины"""
    user_id = callback.message.chat.id
    product_id = callback_data.product_id

    product_item_in_cart_data = Select.cart_item_data(user_id, product_id=product_id)

    [category_id,
     product_id,
     product_name,
     manufacturer_name,
     description,
     product_count,
     product_selected,
     product_price,
     number_in_store] = product_item_in_cart_data

    text = f"<b>{product_name}</b> ({manufacturer_name})\n" \
           f"{description}\n" \
           f"В наличии <code>{number_in_store}</code> шт."
    keyboard = Inline.view_product_item_in_cart(product_item_in_cart_data)
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(OrderingCartCallback.filter(F.product_selected))
async def product_item_selected(callback: CallbackQuery, callback_data: OrderingCartCallback) -> None:
    """Изменяем состояние товара в корзине"""
    user_id = callback.message.chat.id
    product_id = callback_data.product_id

    if Select.number_in_store(product_id) == 0:
        await callback.answer('Ошибка в количестве товаров!')

    else:
        Update.cart_item_product_selected(user_id, product_id)
        await view_cart(callback)


@router.callback_query(OrderingCartCallback.filter(F.product_delete))
async def product_item_delete(callback: CallbackQuery, callback_data: OrderingCartCallback) -> None:
    """Удалить товар из корзины"""
    user_id = callback.message.chat.id
    product_id = callback_data.product_id
    Delete.product_item_in_cart(user_id, products_id_array=product_id)
    await view_cart(callback)


@router.callback_query(CounterProductItemCartCallback.filter(F.minus | F.plus))
async def counter_product_item_in_cart(callback: CallbackQuery, callback_data: CounterProductItemCartCallback) -> None:
    """Счётчик для карточки товара из корзины"""
    user_id = callback.message.chat.id
    product_id = callback_data.product_id

    mode = "minus" if callback_data.minus else "plus"

    current_keyboard = callback.message.reply_markup.dict()
    [row_ind, btn_ind] = get_coordinate_button_by_callback_data(current_keyboard['inline_keyboard'], "number_product")
    current_number_product = int(current_keyboard['inline_keyboard'][row_ind][btn_ind]['text'])

    number_product = Update.count_product_item_cart(user_id, product_id, mode)

    if number_product != current_number_product:
        await view_product_item_in_cart(callback, callback_data)
    else:
        await callback.answer("Количество товаров не изменить")


@router.callback_query(OrderingCartCallback.filter(F.select_store))
async def select_store(callback: CallbackQuery) -> None:
    """Выбор ПВЗ"""
    stores_array = Select.stores_array()

    text = "Выберите пункт выдачи заказа"
    keyboard = Inline.view_stores(stores_array)

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(OrderingCartCallback.filter(F.store_id & ~F.ordering))
async def save_selected_store(callback: CallbackQuery, callback_data: OrderingCartCallback) -> None:
    """Пользователь выбрал магазин - возвращаемся в корзину"""
    user_id = callback.message.chat.id
    store_id = callback_data.store_id

    Update.user_info(user_id, "default_store_id", store_id)

    await view_cart(callback)


@router.callback_query(OrderingCartCallback.filter(F.ordering))
async def ordering(callback: CallbackQuery,
                   return_in_view_cart_if_error: bool = False) -> None:
    """Окно оформления заказа"""
    user_id = callback.message.chat.id
    message_id = callback.message.message_id

    default_store_id = Select.user_info_by_column_name(user_id, 'default_store_id')

    if default_store_id is None:
        if return_in_view_cart_if_error:
            """Возвращаемся в корзину при ошибке"""
            await view_cart(callback)

        await callback.answer("Не выбран пункт выдачи заказа!")

    else:
        store_data = Select.store_data_by_id(default_store_id)
        [store_id, store_name, address] = store_data

        cart_item_data = Select.cart_item_data(user_id, product_selected=True)
        purchase_id = Insert.create_purchase(user_id, store_id, cart_item_data)
        Delete.product_item_in_cart(user_id, only_product_selected=True)

        if cart_item_data:
            """Если корзина не пуста (считаем только выделенные товары)"""
            text = get_purchase_item_text(purchase_id, store_data, cart_item_data)

            keyboard = Inline.ordering(purchase_id)
            await callback.message.edit_text(text, reply_markup=keyboard)

            await asyncio.sleep(DEFAULT_PAYMENT_TIME)

            if not Select.check_payment_purchase(purchase_id):
                await callback.message.delete_reply_markup()

        else:
            if return_in_view_cart_if_error:
                """Возвращаемся в корзину при ошибке"""
                await view_cart(callback)

            await callback.answer("Ваша корзина пуста или вы не выбрали товары")


@router.callback_query(OrderingCartCallback.filter(F.payment))
async def payment(callback: CallbackQuery, callback_data: OrderingCartCallback) -> None:
    """Оплата заказа"""
    user_id = callback.message.chat.id
    purchase_id = callback_data.purchase_id

    current_time = datetime.now().replace(tzinfo=None)
    diff_time_seconds = (current_time - datetime.fromtimestamp(callback_data.payment_time)).total_seconds()

    if diff_time_seconds > DEFAULT_PAYMENT_TIME:
        """Если истекло время бронирования заказа, то возвращаемся в корзину"""
        await callback.answer("Истекло время оплаты!")
        await callback.message.delete_reply_markup()

    else:
        Update.payment_status(purchase_id)
        purchase_data = Select.user_purchases_array(user_id, purchases_id_array=purchase_id)[0]

        [purchase_id,
         store_id,
         purchase_date,
         payment_status] = purchase_data
        store_data = Select.store_data_by_id(store_id)

        cart_item_data = Select.purchase_products_data(purchase_id)

        text = get_purchase_item_text(purchase_id, store_data, cart_item_data, payment_status=payment_status)
        await callback.message.edit_text(text=text)


# ____________________ CATALOG ____________________

@router.message(Text(text="каталог", ignore_case=True))
async def view_categories(message: Message, edit_message: bool = False) -> None:
    """Вывести список категорий"""
    user_id = message.chat.id
    user_message_id = message.message_id

    categories_array = Select.categories()

    text = "<b>Выберите категорию</b>"
    keyboard = Inline.view_categories(categories_array)

    if edit_message:
        await message.edit_text(text, reply_markup=keyboard)

    else:
        await message.answer(text, reply_markup=keyboard)
        await DeleteMessage(chat_id=user_id, message_id=user_message_id)


@router.callback_query(CatalogCallback.filter(~F.category_id))
async def view_categories_callback(callback: CallbackQuery) -> None:
    """Вывести список категорий"""
    await view_categories(callback.message, edit_message=True)


@router.callback_query(CatalogCallback.filter(
    (F.category_id & ~F.product_id & F.paging_direction == "empty") | (F.paging_direction != "empty")))
async def view_products_by_category(callback: CallbackQuery, callback_data: CatalogCallback) -> None:
    """Вывести список товаров для выбранной категории"""
    default_limit = 5
    add_paging_btn = True

    category_id = callback_data.category_id
    current_product_id = callback_data.product_id
    paging_direction = callback_data.paging_direction

    category_name = Select.category_name_by_id(category_id)
    products_array = Select.products_array(category_id=category_id, limit='ALL')

    # Вычисляем индекс крайнего элемента листа (мини-списка)
    ind = 0
    if paging_direction != "empty":
        ind = get_index_product(products_array, current_product_id)

    # Получаем номер текущего листа и общее количество листов
    [current_list, number_list] = get_current_and_number_list(products_array, ind, paging_direction, default_limit)

    # Получаем массив нужных товаров
    products_array = get_array_slice(products_array, ind, default_limit, mode=paging_direction)

    # Если лист 1, то не добавлять кнопки
    if number_list == 1:
        add_paging_btn = False

    text = f"[{current_list}/{number_list}] {category_name}"
    keyboard = Inline.view_products_by_category(products_array, add_paging_btn=add_paging_btn)
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(CatalogCallback.filter(F.product_id))
async def view_product_item(callback: CallbackQuery,
                            callback_data: Union[CatalogCallback, FavoritesCallback, InteractionProduct]) -> None:
    """Карточка товара"""
    user_id = callback.message.chat.id
    product_id = callback_data.product_id

    product_item_data = Select.product_item_data(user_id, product_id)

    [category_id,
     product_id,
     product_name,
     manufacturer_name,
     description,
     is_favorite,
     price_product,
     number_in_cart,
     number_in_store] = product_item_data

    text = f"<b>{product_name}</b> ({manufacturer_name})\n" \
           f"{description}\n" \
           f"В наличии: <code>{number_in_store}</code> шт."
    keyboard = Inline.view_product_item(product_item_data, callback_data)
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(InteractionProduct.filter(F.add_in_favorites))
async def add_in_favorites(callback: CallbackQuery, callback_data: InteractionProduct) -> None:
    """Добавить товар в избранное"""
    user_id = callback.message.chat.id
    product_id = callback_data.product_id

    is_favorite = Update.add_in_favorites(user_id, product_id)
    keyboard = Inline.add_in_favorites(callback, callback_data, is_favorite)

    await callback.message.edit_reply_markup(reply_markup=keyboard)


@router.callback_query(InteractionProduct.filter(F.add_in_cart))
async def add_in_cart(callback: CallbackQuery, callback_data: InteractionProduct) -> None:
    """Добавить товар в корзину"""
    user_id = callback.message.chat.id
    product_id = callback_data.product_id

    number_in_store = Select.number_in_store(product_id)
    free_number_product = Select.free_number_product(user_id, product_id)

    if number_in_store:
        """Если товар есть на складе"""

        if free_number_product:
            """Если есть свободные позиции (которые юзер не добавил в корзину)"""
            cart_item_data = (user_id, product_id, 1)
            Insert.cart_item(cart_item_data)

            await callback.answer("Товар добавлен в корзину (^_^)")

            await view_product_item(callback, callback_data)

        else:
            await callback.answer("В вашей корзине максимальное количество товаров!")

    else:
        await callback.answer("Товар закончился:(")


# ____________________ OTHER ____________________

@router.message(Command("start"))
async def start(message: Message) -> None:
    """Start Bot"""
    await message.answer("Привет (^_^)", reply_markup=Reply.default())


@router.message(Command("personal_area"))
async def personal_area_command(message: Message) -> None:
    """Личный кабинет пользователя"""
    await personal_area(message)


@router.message(Command("help"))
async def help_message(message: Message) -> None:
    """Вывести help-сообщение"""
    await message.answer("help-message")


@router.message(Command("show_keyboard"))
async def show_keyboard(message: Message) -> None:
    """Отобразить стандартную клавиатуру по команде"""
    user_id = message.chat.id
    user_message_id = message.message_id

    text = "Добавлены стандартные кнопки"
    keyboard = Reply.default()

    await message.answer(text, reply_markup=keyboard)
    await DeleteMessage(chat_id=user_id, message_id=user_message_id)


@router.callback_query(OtherCallback.filter(F.action == "view"))
async def close_window(callback: CallbackQuery, callback_data: OtherCallback) -> None:
    """Заглушка на 'пустые' кнопки"""
    await callback.answer(callback_data.value)


@router.callback_query(OtherCallback.filter(F.action == "close"))
async def close_window(callback: CallbackQuery) -> None:
    """Закрыть окно (удалить сообщение)"""
    await callback.message.delete()

'''
@router.errors()
async def catching_exceptions(event: Update):
    """Ловим ошибки/исключения"""
    print(event.exception)
'''
