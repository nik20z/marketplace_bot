from typing import Union
from typing import KeysView

# My Modules
from bot.database.connect import cursor, connection


extensions_create_names = ('pg_trgm',)

table_create_queries = {
    "store": """
        CREATE TABLE IF NOT EXISTS store (
                    store_id serial PRIMARY KEY,
                    store_name text NOT NULL,
                    address text NOT NULL,
                    description text NOT NULL DEFAULT '');""",

    "telegram": """
        CREATE TABLE IF NOT EXISTS telegram (
                    user_id bigint PRIMARY KEY,
                    user_name text NOT NULL,
                    joined date,
                    favorites_products bigint[] NOT NULL DEFAULT '{}',
                    default_store_id int,
                    FOREIGN KEY (default_store_id) REFERENCES store (store_id));""",

    "category": """
        CREATE TABLE IF NOT EXISTS category (
                    category_id serial PRIMARY KEY,
                    category_name text NOT NULL);""",
    
    "manufacturer": """
        CREATE TABLE IF NOT EXISTS manufacturer (
                    manufacturer_id serial PRIMARY KEY,
                    manufacturer_name text NOT NULL);""",

    "product": """
        CREATE TABLE IF NOT EXISTS product (
                    product_id bigserial PRIMARY KEY,
                    product_name text NOT NULL,
                    manufacturer_id integer NOT NULL,
                    category_id integer NOT NULL,
                    description text NOT NULL DEFAULT '',
                    FOREIGN KEY (category_id) REFERENCES category (category_id),
                    FOREIGN KEY (manufacturer_id) REFERENCES manufacturer (manufacturer_id));""",

    "price_change": """
        CREATE TABLE IF NOT EXISTS price_change (
                    product_id bigserial,
                    date_price_change timestamp with time zone NOT NULL,
                    new_price numeric(12, 2) NOT NULL,
                    CONSTRAINT POSITIVE_PRICE CHECK (new_price > 0)),
                    FOREIGN KEY (product_id) REFERENCES product (product_id));""",

    "delivery": """
        CREATE TABLE IF NOT EXISTS delivery (
                    product_id bigserial,
                    delivery_date timestamp with time zone NOT NULL,
                    product_count integer NOT NULL,
                    condition_ boolean NOT NULL DEFAULT False, 
                    FOREIGN KEY (product_id) REFERENCES product (product_id));""",

    "purchase": """
        CREATE TABLE IF NOT EXISTS purchase (
                    purchase_id bigserial NOT NULL,
                    user_id bigint,
                    store_id smallint,
                    purchase_date timestamp without time zone NOT NULL,
                    payment_status boolean DEFAULT False,
                    CONSTRAINT PK_PURCHASE PRIMARY KEY (purchase_id),
                    FOREIGN KEY (user_id) REFERENCES telegram (user_id),
                    FOREIGN KEY (store_id) REFERENCES store (store_id));""",

    "purchase_item": """
        CREATE TABLE IF NOT EXISTS purchase_item (
                    purchase_id bigint,
                    product_id bigint,
                    product_count integer NOT NULL,
                    product_price NUMERIC(12,2) NOT NULL,
                    CONSTRAINT PK_PURCHASE_ITEM PRIMARY KEY (purchase_id, product_id),
                    CONSTRAINT POSITIVE_COUNT CHECK (product_count > 0),
                    CONSTRAINT POSITIVE_PRICE CHECK (product_price > 0),
                    FOREIGN KEY (purchase_id) REFERENCES purchase (purchase_id),
                    FOREIGN KEY (product_id) REFERENCES product (product_id));""",

    "cart_item": """
        CREATE TABLE IF NOT EXISTS cart_item (
                    user_id bigint,
                    product_id bigint,
                    product_count integer NOT NULL,
                    product_selected boolean NOT NULL DEFAULT True,
                    CONSTRAINT PK_CART_ITEM PRIMARY KEY (user_id, product_id),
                    CONSTRAINT POSITIVE_COUNT CHECK (product_count > 0),
                    FOREIGN KEY (user_id) REFERENCES telegram (user_id),
                    FOREIGN KEY (product_id) REFERENCES product (product_id));"""
}


view_create_queries = {}


function_create_queries = {
    "number_in_cart": """
        CREATE OR REPLACE FUNCTION number_in_cart(user_id_arg bigint, product_id_arg bigint)
        RETURNS int
        LANGUAGE plpgsql
        AS
        $$
        DECLARE
            number_in_cart_value integer;
        BEGIN
            SELECT SUM(product_count)
            INTO number_in_cart_value
            FROM cart_item 
            WHERE user_id = user_id_arg AND product_id = product_id_arg;
            
            RETURN COALESCE(number_in_cart_value, 0);
        END;
        $$;
        """,

    "number_in_store": """
        CREATE OR REPLACE FUNCTION number_in_store(product_id_arg bigint)
        RETURNS int
        LANGUAGE plpgsql
        AS
        $$
        DECLARE
            number_product_delivery_value integer;
            number_product_purchase_value integer;
            number_product_value integer;
        BEGIN
            SELECT SUM(product_count)
            INTO number_product_delivery_value
            FROM delivery 
            WHERE product_id = product_id_arg AND condition_;
            
            SELECT SUM(product_count)
            INTO number_product_purchase_value
            FROM purchase_item 
            LEFT JOIN purchase ON purchase_item.purchase_id = purchase.purchase_id
            WHERE product_id = product_id_arg
            AND (purchase.payment_status 
                OR (current_timestamp::timestamp - purchase.purchase_date::timestamp) < '5 minute');
            
            number_product_delivery_value = COALESCE(number_product_delivery_value, 0);
            number_product_purchase_value = COALESCE(number_product_purchase_value, 0);
            number_product_value = number_product_delivery_value - number_product_purchase_value;
            
            RETURN COALESCE(number_product_value, 0);
        END;
        $$;
        """,

    "free_number_product": """
        CREATE OR REPLACE FUNCTION free_number_product(user_id_arg bigint, product_id_arg bigint)
        RETURNS int
        LANGUAGE plpgsql
        AS
        $$
        DECLARE
            product_number_value integer;
            number_in_cart_value integer;
        BEGIN
            SELECT number_in_store(product_id_arg) INTO product_number_value;
            SELECT number_in_cart(user_id_arg, product_id_arg) INTO number_in_cart_value;
            
            RETURN product_number_value - number_in_cart_value;
        END;
        $$;
        """,

    "price_product": """
        CREATE OR REPLACE FUNCTION price_product(product_id_arg bigint)
        RETURNS numeric
        LANGUAGE plpgsql
        AS
        $$
        DECLARE
            price_product_value numeric;
        BEGIN
            SELECT new_price
            INTO price_product_value
            FROM price_change 
            WHERE product_id = product_id_arg
            ORDER BY date_price_change DESC
            LIMIT 1;
            
            RETURN COALESCE(price_product_value, 0.0);
        END;
        $$;
        """
}


def create_extension(extension_name: Union[str, list, tuple] = None) -> None:
    """Добавляем расширения"""
    if extension_name is None:
        create_extension(extension_name=extensions_create_names)
    else:
        if type(extension_name) is str:
            extension_name = [extension_name]

        for x in extension_name:
            cursor.execute(f"CREATE EXTENSION IF NOT EXISTS {x};")
            connection.commit()


def create_table(table_name: Union[str, list, tuple, KeysView] = None) -> None:
    """Создаём таблицу"""
    if table_name is None:
        create_table(table_name=table_create_queries.keys())
    else:
        if type(table_name) is str:
            table_name = [table_name]

        for x in table_name:
            cursor.execute(table_create_queries.get(x, None))
            connection.commit()


def create_view(view_name: Union[str, list, tuple, KeysView] = None) -> None:
    """Создаём представление"""
    if view_name is None:
        create_view(view_name=view_create_queries.keys())
    else:
        if type(view_name) is str:
            view_name = [view_name]

        for x in view_name:
            cursor.execute(view_create_queries.get(x, None))
            connection.commit()


def create_functions(function_name: Union[str, list, tuple, KeysView] = None) -> None:
    """Создаём функции"""
    if function_name is None:
        create_functions(function_name=function_create_queries.keys())
    else:
        if type(function_name) is str:
            function_name = [function_name]

        for x in function_name:
            cursor.execute(function_create_queries.get(x, None))
            connection.commit()


def delete_from_table(table_name: Union[str, list, tuple, KeysView] = None) -> None:
    """Удаляем все данные из таблицы"""
    if table_name is not None:
        if type(table_name) is str:
            table_name = [table_name]

        for x in table_name:
            cursor.execute(f"DELETE FROM {x};")
            connection.commit()


def drop_table(table_name: Union[str, list, tuple, KeysView] = None, cascade_state: bool = False) -> None:
    """Удаляем таблицу"""
    if table_name is not None:
        if type(table_name) is str:
            table_name = [table_name]

        for x in table_name:
            cascade = "CASCADE" if cascade_state else ""
            cursor.execute(f"DROP TABLE IF EXISTS {x} {cascade};")
            connection.commit()


def add_column(table_name: str,
               column_name: str,
               data_type: str,
               constraint: str = "") -> None:
    """Добавить новую колонку"""
    query = """ALTER TABLE {0} 
               ADD COLUMN IF NOT EXISTS {1} {2} {3};
               """.format(table_name, column_name, data_type, constraint)
    cursor.execute(query)
    connection.commit()
