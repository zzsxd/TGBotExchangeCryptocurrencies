import telebot
import os
import platform
from threading import Lock
from config_parser import ConfigParser
from frontend import Bot_inline_btns
from backend import DbAct
from db import DB

config_name = 'secrets.json'


def verify_user_text(user_input: str) -> bool:
    if user_input is not None and user_input != '':
        return True
    return False


def verify_user_value(user_input: str) -> bool:
    if not verify_user_text(user_input):
        return False
    try:
        int(user_input)
        return True
    except ValueError:
        return False


def current_btc_price():
    return 2_000_000

def main():
    @bot.message_handler(commands=['start', 'admin', 'buy', 'sell', 'exchange'])
    def start(message):
        command = message.text.replace('/', '')
        user_id = message.from_user.id
        buttons = Bot_inline_btns()
        db_actions.add_user(user_id, message.from_user.first_name, message.from_user.last_name,
                            f'@{message.from_user.username}')
        if command == 'start':
            bot.send_message(user_id,
                             '<b>Привет! 👋</b>\n\n'
                             '🤖Я бот для <u>Приобритения, продажи и обмена криптовалют</u> ✅',
                             parse_mode='HTML')
        # elif command == 'buy':
        #     buy_buttons = db_actions.get_exchange_rates("buy")
        #     bot.send_message(user_id, 'Здесь вы можете купить криптовалюту по выгодному курсу без регистрации!\n\n'
        #                               'Выберите направление обмена:',
        #                      reply_markup=buttons.buy_crypto_btns(buy_buttons))
        # elif command == 'sell':
        #     sell_buttons = db_actions.get_exchange_rates("sell")
        #     bot.send_message(user_id, 'Здесь вы можете продать криптовалюту по выгодному курсу без регистрации!\n\n'
        #                               'Выберите направление обмена:',
        #                      reply_markup=buttons.sell_crypto_btns(sell_buttons))
        # elif command == 'exchange':
        #     exchange_buttons = db_actions.get_exchange_rates("exchange")
        #     bot.send_message(user_id, 'Здесь вы можете обменять криптовалюту по выгодному курсу без регистрации!\n\n'
        #                               'Выберите направление обмена:',
        #                      reply_markup=buttons.exchange_crypto_btns(exchange_buttons))
        elif db_actions.user_is_admin(user_id):
            if command == 'admin':
                bot.send_message(user_id, 'Вы успешно зашли в админ-панель!',
                                 reply_markup=buttons.admin_btns())

    @bot.callback_query_handler(func=lambda call: True)
    def callback(call):
        user_id = call.message.chat.id
        buttons = Bot_inline_btns()
        if db_actions.user_is_existed(user_id):
            if db_actions.user_is_admin(user_id):
                if call.data == 'add_exchange_rate':
                    db_actions.set_user_system_key(user_id, "admin_action", "add")
                    bot.send_message(user_id, 'Выберите направление для которого хотите добавить курс обмена',
                                     reply_markup=buttons.select_exchange_direction())
                elif call.data == 'del_exchange_rate':
                    db_actions.set_user_system_key(user_id, "admin_action", "del")
                    bot.send_message(user_id, 'Выберите направление для которого хотите удалить курс обмена',
                                     reply_markup=buttons.select_exchange_direction())
                elif call.data[:6] == 'select':
                    direction = call.data[7:]
                    action = db_actions.get_user_system_key(user_id, "admin_action")
                    if action == "del":
                        direction_data = db_actions.get_exchange_rates(type=direction)
                        bot.send_message(user_id, "Выберите что удалить",
                                         reply_markup=buttons.direction_buttons(direction_data, admin=True))
                    elif action == "add":
                        db_actions.set_user_system_key(user_id, "admin_exchange_direction", direction)
                        db_actions.set_user_system_key(user_id, "index", 0)
                        bot.send_message(user_id, "Введите новый курс обмена")
                elif call.data[:17] == 'del_exchange_rate':
                    db_actions.del_exchange_rates(row_id=call.data[17:])
                    bot.send_message(user_id, "Операция успешно завершена")
                elif call.data == "change_ratio":
                    db_actions.set_user_system_key(user_id, "index", 1)
                    bot.send_message(user_id, f"Введите коэффициент курса для "
                                              f"пользователей относительно текущего курса BTC = {current_btc_price()}")

            # elif call.data == 'addexchange':
            #     temp_user_data.temp_data(user_id)[user_id][0] = 2
            #     bot.send_message(user_id, 'Введите название нового направления обмена!')
            # elif call.data == 'delbuy':
            #     temp_user_data.temp_data(user_id)[user_id][0] = 3
            #     buy_btns = db_actions.get_buy_btns()
            #     bot.send_message(user_id, 'Выберите категорию для удаления',
            #                      reply_markup=buttons.buy_crypto_btns(buy_btns))
            # elif call.data[:3] == 'buy' and code == 3:
            #     db_actions.del_buy_btns(call.data[3:])
            #     temp_user_data.temp_data(user_id)[user_id][0] = None
            #     bot.send_message(user_id, 'Категория удалена успешно!')
            # elif call.data == 'delsell':
            #     temp_user_data.temp_data(user_id)[user_id][0] = 4
            #     sell_btns = db_actions.get_sell_btns()
            #     bot.send_message(user_id, 'Выберите категорию для удаления',
            #                      reply_markup=buttons.sell_crypto_btns(sell_btns))
            # elif call.data[:4] == 'sell' and code == 4:
            #     db_actions.del_sell_btns(call.data[4:])
            #     temp_user_data.temp_data(user_id)[user_id][0] = None
            #     bot.send_message(user_id, 'Категория удалена успешно!')
            # elif call.data == 'delexchange':
            #     temp_user_data.temp_data(user_id)[user_id][0] = 5
            #     exchange_btns = db_actions.get_exchange_btns()
            #     bot.send_message(user_id, 'Выберите категорию для удаления',
            #                      reply_markup=buttons.exchange_crypto_btns(exchange_btns))
            # elif call.data[:8] == 'exchange' and code == 5:
            #     db_actions.del_exchange_btns(call.data[8:])
            #     temp_user_data.temp_data(user_id)[user_id][0] = None
            #     bot.send_message(user_id, 'Категория удалена успешно!')
            # elif call.data == 'export':
            #     db_actions.db_export_xlsx()
            #     bot.send_document(user_id, open(config.get_config()['xlsx_path'], 'rb'))
            #     os.remove(config.get_config()['xlsx_path'])
            # elif call.data[:3] == 'buy':
            #     bot.send_message(user_id, 'Создание заявки на покупку!\n\n'
            #                               f'Заполните заявку для покупки {call.id}\n\n'
            #                               f'Цена за 1 {call.data} - bebra',
            #                      reply_markup=buttons.buy_request_btns())
            # elif call.data == 'continue':
            #     bot.send_message(user_id, 'Проверьте, что все данные указаны\n\n'
            #                               'Вы покупаете 0,001 ВТС за 13454 МИР. руб.\n\n'
            #                                 'Средства будут переведены на адрес\n\n'
            #                               'BTC: 7884293kfkkfsfsidfisfllfsisaffs\n\n'
            #                               'Для совершения операции отправьте 13454 р. на номер 4536 6363 6262 6636, карта '
            #                               'МИР Евгений Алексеевич К.\n\n'
            #                               'После оплаты нажмите "Я оплатил."\n\n'
            #                               'Средства поступят втечение 20 минут.',
            #                                 reply_markup=buttons.buy_btns())

    @bot.message_handler(content_types=['text', 'photo'])
    def text_message(message):
        user_input = message.text
        user_id = message.chat.id
        buttons = Bot_inline_btns()
        code = db_actions.get_user_system_key(user_id, "index")
        if db_actions.user_is_existed(user_id):
            if db_actions.user_is_admin(user_id):
                if code == 0:
                    if verify_user_text(user_input):
                        direction = db_actions.get_user_system_key(user_id, "admin_exchange_direction")
                        db_actions.add_exchange_rates(user_input, direction)
                        bot.send_message(user_id, "Операция успешно совершена")
                    else:
                        db_actions.set_user_system_key(user_id, "index", None)
                        bot.send_message(user_id, "Это не текст")
                elif code == 1:
                    if verify_user_value(user_input):
                        config.set_min_btc(current_btc_price() * user_input)
                    else:
                        db_actions.set_user_system_key(user_id, "index", None)
                        bot.send_message(user_id, "Это не число")

    bot.polling(none_stop=True)


if '__main__' == __name__:
    os_type = platform.system()
    work_dir = os.path.dirname(os.path.realpath(__file__))
    config = ConfigParser(f'{work_dir}/{config_name}', os_type)
    db = DB(config.get_config()['db_file_name'], Lock())
    db_actions = DbAct(db, config, config.get_config()['xlsx_path'])
    bot = telebot.TeleBot(config.get_config()['tg_api'])
    main()
