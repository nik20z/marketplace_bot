from os import environ
from typing import Final


class Keys:
    TG_TOKEN: Final = environ.get('TG_TOKEN', '0987654321:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
    TG_BOT_ID: Final = environ.get('TG_BOT_ID', '0987654321')


class DataBase:
    SETTINGS: Final = environ.get('SETTINGS', {'user': "postgres",
                                               'password': "0987654321",
                                               'host': "localhost",
                                               'port': 5432,
                                               'database': "marketplace"})

