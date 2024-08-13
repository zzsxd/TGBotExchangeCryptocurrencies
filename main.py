import telebot
import os
import platform
from threading import Lock
from config_parser import ConfigParser
from frontend import Bot_inline_btns
from backend import TempUserData, DbAct
from db import DB

config_name = ('secrets.json')


def main():
    @bot.message_handler(commands=['start', 'admin', 'buy', 'sell', 'exchange'])
    def start(message):
        command = message.text.replace('/', '')
        user_id = message.from_user.id
        buttons = Bot_inline_btns()
        buy_btns = db_actions.get_buy_btns()
        sell_btns = db_actions.get_sell_btns()
        exchange_btns = db_actions.get_exchange_btns()
        db_actions.add_user(user_id, message.from_user.first_name, message.from_user.last_name,
                            f'@{message.from_user.username}')
        if command == 'start':
            bot.send_message(user_id,
                             '<b>Привет! 👋</b>\n\n'
                             '🤖Я бот для <u>Приобритения, продажи и обмена криптовалют</u> ✅',
                             parse_mode='HTML')
        elif command == 'buy':
            bot.send_message(user_id, 'Здесь вы можете купить криптовалюту по выгодному курсу без регистрации!\n\n'
                                      'Выберите направление обмена:',
                             reply_markup=buttons.buy_crypto_btns(buy_btns))
        elif command == 'sell':
            bot.send_message(user_id, 'Здесь вы можете продать криптовалюту по выгодному курсу без регистрации!\n\n'
                                      'Выберите направление обмена:',
                             reply_markup=buttons.sell_crypto_btns(sell_btns))
        elif command == 'exchange':
            bot.send_message(user_id, 'Здесь вы можете обменять криптовалюту по выгодному курсу без регистрации!\n\n'
                                      'Выберите направление обмена:',
                             reply_markup=buttons.exchange_crypto_btns(exchange_btns))
        elif db_actions.user_is_admin(user_id):
            if command == 'admin':
                bot.send_message(user_id, 'Вы успешно зашли в админ-панель!',
                                 reply_markup=buttons.admin_btns())

    @bot.callback_query_handler(func=lambda call: True)
    def callback(call):
        user_id = call.message.chat.id
        buttons = Bot_inline_btns()
        code = temp_user_data.temp_data(user_id)[user_id][0]
        if db_actions.user_is_existed(user_id):
            if call.data == 'addbuy':
                temp_user_data.temp_data(user_id)[user_id][0] = 0
                bot.send_message(user_id, 'Введите название нового направления покупки!')
            elif call.data == 'addsell':
                temp_user_data.temp_data(user_id)[user_id][0] = 1
                bot.send_message(user_id, 'Введите название нового направления продажи!')
            elif call.data == 'addexchange':
                temp_user_data.temp_data(user_id)[user_id][0] = 2
                bot.send_message(user_id, 'Введите название нового направления обмена!')
            elif call.data == 'delbuy':
                temp_user_data.temp_data(user_id)[user_id][0] = 3
                buy_btns = db_actions.get_buy_btns()
                bot.send_message(user_id, 'Выберите категорию для удаления',
                                 reply_markup=buttons.buy_crypto_btns(buy_btns))
            elif call.data[:3] == 'buy' and code == 3:
                db_actions.del_buy_btns(call.data[3:])
                temp_user_data.temp_data(user_id)[user_id][0] = None
                bot.send_message(user_id, 'Категория удалена успешно!')
            elif call.data == 'delsell':
                temp_user_data.temp_data(user_id)[user_id][0] = 4
                sell_btns = db_actions.get_sell_btns()
                bot.send_message(user_id, 'Выберите категорию для удаления',
                                 reply_markup=buttons.sell_crypto_btns(sell_btns))
            elif call.data[:4] == 'sell' and code == 4:
                db_actions.del_sell_btns(call.data[4:])
                temp_user_data.temp_data(user_id)[user_id][0] = None
                bot.send_message(user_id, 'Категория удалена успешно!')
            elif call.data == 'delexchange':
                temp_user_data.temp_data(user_id)[user_id][0] = 5
                exchange_btns = db_actions.get_exchange_btns()
                bot.send_message(user_id, 'Выберите категорию для удаления',
                                 reply_markup=buttons.exchange_crypto_btns(exchange_btns))
            elif call.data[:8] == 'exchange' and code == 5:
                print('123')
                db_actions.del_exchange_btns(call.data[8:])
                temp_user_data.temp_data(user_id)[user_id][0] = None
                bot.send_message(user_id, 'Категория удалена успешно!')
            elif call.data == 'export':
                db_actions.db_export_xlsx()
                bot.send_document(user_id, open(config.get_config()['xlsx_path'], 'rb'))
                os.remove(config.get_config()['xlsx_path'])
            elif call.data[:3] == 'buy':
                bot.send_message(user_id, 'Создание заявки на покупку!\n\n'
                                          f'Заполните заявку для покупки {call.id}\n\n'
                                          f'Цена за 1 {call.data} - bebra',
                                 reply_markup=buttons.buy_request_btns())

    @bot.message_handler(content_types=['text', 'photo'])
    def text_message(message):
        user_input = message.text
        user_id = message.chat.id
        buttons = Bot_inline_btns()
        code = temp_user_data.temp_data(user_id)[user_id][0]
        match code:
            case 0:
                if user_input is not None:
                    db_actions.add_new_buy(user_input)
                    temp_user_data.temp_data(user_id)[user_id][0] = None
                    bot.send_message(user_id, 'Новое направление покупки создано!')
                else:
                    bot.send_message(user_id, 'Это не текст!')
            case 1:
                if user_input is not None:
                    db_actions.add_new_sell(user_input)
                    temp_user_data.temp_data(user_id)[user_id][0] = None
                    bot.send_message(user_id, 'Новое направление продажи создано!')
                else:
                    bot.send_message(user_id, 'Это не текст!')
            case 2:
                if user_input is not None:
                    db_actions.add_new_exchange(user_input)
                    temp_user_data.temp_data(user_id)[user_id][0] = None
                    bot.send_message(user_id, 'Новое направление обмена создано!')
                else:
                    bot.send_message(user_id, 'Это не текст!')

    bot.polling(none_stop=True)


if '__main__' == __name__:
    os_type = platform.system()
    work_dir = os.path.dirname(os.path.realpath(__file__))
    config = ConfigParser(f'{work_dir}/{config_name}', os_type)
    temp_user_data = TempUserData()
    db = DB(config.get_config()['db_file_name'], Lock())
    db_actions = DbAct(db, config, config.get_config()['xlsx_path'])
    bot = telebot.TeleBot(config.get_config()['tg_api'])
    main()
