

def get_coordinate_button_by_callback_data(keyboard, callback_data_value: str) -> list:
    """Поиск кнопки по callback_data"""
    row_ind = 0
    btn_ind = 0
    for row in keyboard:
        for btn in row:
            if btn['callback_data'] == callback_data_value:
                return [row_ind, btn_ind]
            btn_ind += 1
        row_ind += 1
        btn_ind = 0

    return [0, 0]

