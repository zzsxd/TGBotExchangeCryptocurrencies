from telebot import types


class Bot_inline_btns:
    def __init__(self):
        super(Bot_inline_btns, self).__init__()
        self.__markup = types.InlineKeyboardMarkup(row_width=1)

    def admin_btns(self):
        one = types.InlineKeyboardButton('Создать направление покупки', callback_data='addbuy')
        two = types.InlineKeyboardButton('Создать направление продажи', callback_data='addsell')
        three = types.InlineKeyboardButton('Создать направление обмена', callback_data='addexchange')
        four = types.InlineKeyboardButton('Удалить направление покупки', callback_data='delbuy')
        five = types.InlineKeyboardButton('Удалить направление продажи', callback_data='delsell')
        six = types.InlineKeyboardButton('Удалить направление обмена', callback_data='delexchange')
        seven = types.InlineKeyboardButton('Экспортировать пользователей', callback_data='export')
        self.__markup.add(one, two, three, four, five, six, seven)
        return self.__markup

    def buy_crypto_btns(self, buy_btns):
        for i in buy_btns:
            btn = types.InlineKeyboardButton(i[1], callback_data=f'buy{i[0]}')
            self.__markup.add(btn)
        return self.__markup

    def sell_crypto_btns(self, sell_btns):
        for i in sell_btns:
            btn = types.InlineKeyboardButton(i[1], callback_data=f'sell{i[0]}')
            self.__markup.add(btn)
        return self.__markup

    def exchange_crypto_btns(self, exchange_btns):
        for i in exchange_btns:
            btn = types.InlineKeyboardButton(i[1], callback_data=f'exchange{i[0]}')
            self.__markup.add(btn)
        return self.__markup

    def buy_request_btns(self):
        one = types.InlineKeyboardButton('Количество', callback_data='quantity')
        two = types.InlineKeyboardButton('Адрес', callback_data='address')
        three = types.InlineKeyboardButton('Продолжить', callback_data='continue')
        four = types.InlineKeyboardButton('Назад', callback_data='back')
        self.__markup.add(one, two, three, four)
        return self.__markup

    def buy_btns(self):
        one = types.InlineKeyboardButton('Я оплатил', callback_data='Ibuy')
        two = types.InlineKeyboardButton('Назад', callback_data='back')
        self.__markup.add(one, two)