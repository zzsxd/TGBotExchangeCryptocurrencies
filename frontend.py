from telebot import types


class Bot_inline_btns:
    def __init__(self):
        super(Bot_inline_btns, self).__init__()
        self.__markup = types.InlineKeyboardMarkup(row_width=1)

    def admin_btns(self):
        one = types.InlineKeyboardButton('Создать направление', callback_data='add_exchange_rate')
        two = types.InlineKeyboardButton('Удалить направление', callback_data='del_exchange_rate')
        seven = types.InlineKeyboardButton('Экспортировать пользователей', callback_data='export')
        self.__markup.add(one, two, seven)
        return self.__markup

    def select_exchange_direction(self):
        one = types.InlineKeyboardButton('Направление покупки', callback_data='select_buy')
        two = types.InlineKeyboardButton('Направление продажи', callback_data='select_sell')
        seven = types.InlineKeyboardButton('Направление обмена', callback_data='select_exchange')
        self.__markup.add(one, two, seven)
        return self.__markup

    def direction_buttons(self, data: tuple, admin: bool = False):
        markup = types.InlineKeyboardMarkup(row_width=1)
        for i in data:
            if not admin:
                callback_data = f"choose_exchange_rate{i[0]}"
            else:
                callback_data = f"del_exchange_rate{i[0]}"
            one = types.InlineKeyboardButton(i[1], callback_data=callback_data)
            markup.add(one)
        return markup

    def buy_crypto_btns(self, buy_btns):
        for i in buy_btns:
            btn = types.InlineKeyboardButton(i[1], callback_data=f'first_buy{i[0]}')
            self.__markup.add(btn)
        btn = types.InlineKeyboardButton("Назад", callback_data=f'first_buy<back>')
        self.__markup.add(btn)
        return self.__markup

    def buy_request_btns(self):
        one = types.InlineKeyboardButton('Количество', callback_data='buy_quantity')
        two = types.InlineKeyboardButton('Адрес кошелька', callback_data='buy_address')
        three = types.InlineKeyboardButton('Продолжить', callback_data='buy_continue')
        four = types.InlineKeyboardButton('Назад', callback_data='buy_continue<back>')
        self.__markup.add(one, two, three, four)
        return self.__markup

    def buy_btns(self):
        one = types.InlineKeyboardButton('Я оплатил', callback_data='buy')
        two = types.InlineKeyboardButton('Назад', callback_data='buy<back>')
        self.__markup.add(one, two)
        return self.__markup

    def sell_crypto_btns(self, sell_btns):
        for i in sell_btns:
            btn = types.InlineKeyboardButton(i[1], callback_data=f'first_sell{i[0]}')
            self.__markup.add(btn)
        btn = types.InlineKeyboardButton("Назад", callback_data=f'first_sell<back>')
        self.__markup.add(btn)
        return self.__markup

    def sell_request_btns(self):
        one = types.InlineKeyboardButton('Количество', callback_data='sell_quantity')
        two = types.InlineKeyboardButton('Номер карты', callback_data='sell_address')
        three = types.InlineKeyboardButton('Продолжить', callback_data='sell_continue')
        four = types.InlineKeyboardButton('Назад', callback_data='sell_continue<back>')
        self.__markup.add(one, two, three, four)
        return self.__markup


    def sell_btns(self):
        one = types.InlineKeyboardButton('Я оплатил', callback_data='sell')
        two = types.InlineKeyboardButton('Назад', callback_data='sell<back>')
        self.__markup.add(one, two)
        return self.__markup

    def exchange_crypto_btns(self, exchange_btns):
        for i in exchange_btns:
            btn = types.InlineKeyboardButton(i[1], callback_data=f'first_exchange{i[0]}')
            self.__markup.add(btn)
        btn = types.InlineKeyboardButton("Назад", callback_data=f'first_exchange<back>')
        self.__markup.add(btn)
        return self.__markup

    def exchange_btns(self, exchange_btns, exclude_id=None):
        for i in exchange_btns:
            if str(i[0]) != exclude_id:
                btn = types.InlineKeyboardButton(i[1], callback_data=f'request_exchange{i[0]}')
                self.__markup.add(btn)
        btn = types.InlineKeyboardButton("Назад", callback_data=f'request_exchange<back>')
        self.__markup.add(btn)
        return self.__markup

    def exchange_request_btns(self):
        one = types.InlineKeyboardButton('Количество', callback_data='exchange_quantity')
        two = types.InlineKeyboardButton('Адрес кошелька', callback_data='exchange_address')
        three = types.InlineKeyboardButton('Продолжить', callback_data='exchange_continue')
        four = types.InlineKeyboardButton('Назад', callback_data='exchange_continue<back>')
        self.__markup.add(one, two, three, four)
        return self.__markup

    def exchange(self):
        one = types.InlineKeyboardButton('Я оплатил', callback_data='exchange')
        two = types.InlineKeyboardButton('Назад', callback_data='exchange<back>')
        self.__markup.add(one, two)
        return self.__markup
    def topic_btns(self, application_id):
        one = types.InlineKeyboardButton('Выполнить заявку', callback_data=f'application_confirm{application_id}')
        two = types.InlineKeyboardButton('Отклонить заявку', callback_data=f'application_reject{application_id}')
        self.__markup.add(one, two)
        return self.__markup
