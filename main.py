import telebot
import os
import platform
import cryptocompare
import random
import coinaddrvalidator
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


def validate_btc(address):
    y = coinaddrvalidator.validate('btc', address)
    if y.valid:
        return True
    else:
        return False


def get_bitcoin_price_in_rub():
    price = cryptocompare.get_price('BTC', currency='RUB')
    return price['BTC']['RUB']


def validate_mir(card_number):
    if len(card_number) != 16:
        return False

    if not card_number.startswith('2'):
        return False

    def luhn_checksum(card_number):
        def digits_of(n):
            return [int(d) for d in str(n)]

        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10

    return luhn_checksum(card_number) == 0


def current_btc_price():
    return 2_000_000

def create_topic():
    topic_id = telebot.TeleBot.create_forum_topic(bot, chat_id=config.get_config()['group_id'],
                                                  name=f'{message.from_user.first_name} '
                                                       f'{message.from_user.last_name} ПОПОЛНЕНИЕ БАЛАНСА',
                                                  icon_color=0x6FB9F0).message_thread_id
    bot.forward_message(chat_id=config.get_config()['group_id'], from_chat_id=message.chat.id, message_id=message.id,
                        message_thread_id=topic_id)
    db_actions.update_topic_id(user_id, topic_id)
    bot.send_message(chat_id=config.get_config()['group_id'], message_thread_id=topic_id, text='Получена оплата!✅\n'
                                                                                               'Проверьте информацию и '
                                                                                               'подтвердите!')
    bot.send_message(user_id, 'Ваша заявка принята, ожидайте!')


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
        elif command == 'buy':
            buy_buttons = db_actions.get_exchange_rates("buy")
            bot.send_message(user_id, 'Здесь вы можете купить криптовалюту по выгодному курсу без регистрации!\n\n'
                                      'Выберите направление обмена:',
                             reply_markup=buttons.buy_crypto_btns(buy_buttons))
        elif command == 'sell':
            sell_buttons = db_actions.get_exchange_rates("sell")
            bot.send_message(user_id, 'Здесь вы можете продать криптовалюту по выгодному курсу без регистрации!\n\n'
                                      'Выберите направление обмена:',
                             reply_markup=buttons.sell_crypto_btns(sell_buttons))
        elif command == 'exchange':
            exchange_buttons = db_actions.get_exchange_rates("exchange")
            bot.send_message(user_id, 'Здесь вы можете обменять криптовалюту по выгодному курсу без регистрации!\n\n'
                                      'Выберите направление обмена:',
                             reply_markup=buttons.exchange_crypto_btns(exchange_buttons))
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
                    bot.send_message(user_id, 'Выберите направление для которого хотите добавить новый курс',
                                     reply_markup=buttons.select_exchange_direction())
                elif call.data == 'del_exchange_rate':
                    db_actions.set_user_system_key(user_id, "admin_action", "del")
                    bot.send_message(user_id, 'Выберите направление для которого вы хотите удалить курс',
                                     reply_markup=buttons.select_exchange_direction())
                elif call.data[:6] == 'select':
                    direction = call.data[7:]
                    action = db_actions.get_user_system_key(user_id, "admin_action")
                    if action == "del":
                        direction_data = db_actions.get_exchange_rates(type=direction)
                        bot.send_message(user_id, "Выберите направление для удаления",
                                         reply_markup=buttons.direction_buttons(direction_data, admin=True))
                    elif action == "add":
                        db_actions.set_user_system_key(user_id, "admin_exchange_direction", direction)
                        db_actions.set_user_system_key(user_id, "index", 0)
                        bot.send_message(user_id, "Введите новый курс обмена")
                elif call.data[:17] == 'del_exchange_rate':
                    db_actions.del_exchange_rates(row_id=call.data[17:])
                    bot.send_message(user_id, "Направление успешно удалено")
                elif call.data == "change_ratio":
                    db_actions.set_user_system_key(user_id, "index", 1)
                    bot.send_message(user_id, f"Введите коэффициент курса для "
                                              f"пользователей относительно текущего курса BTC = {current_btc_price()}")
                elif call.data == 'export':
                    db_actions.db_export_xlsx()
                    bot.send_document(user_id, open(config.get_config()['xlsx_path'], 'rb'))
                    os.remove(config.get_config()['xlsx_path'])
            if call.data[:3] == 'buy':
                bot.send_message(user_id, 'Создание заявки на покупку!\n\n'
                                          f'Заполните заявку для покупки {call.id}\n\n'
                                          f'Цена за 1 {call.data} - bebra',
                                 reply_markup=buttons.buy_request_btns())
            elif call.data == 'quantity':
                db_actions.set_user_system_key(user_id, "index", 2)
                bot.send_message(user_id, 'Введите количество желаемой крипты')
            elif call.data == 'address':
                db_actions.set_user_system_key(user_id, "index", 3)
                bot.send_message(user_id, 'Введите адрес кошелька')
            elif call.data == 'continue':
                number_application = random.randint(000000, 999999)
                bot.send_message(user_id, 'Проверьте, что все данные указаны верно!\n\n'
                                          f'Номер заявки: {number_application}\n\n'
                                          f'Вы покупаете 0,001 ВТС за 13454 МИР. руб.'
                                          f'Средства будут переведены на адрес\n\n'
                                          f'BTC: <code>7884293kfkkfsfsidfisfllfsisaffs</code>\n\n'
                                          f'Для совершения операции отправьте 13454 р.\n'
                                          f'на номер <code>4536 6363 6262 6636</code>, карта МИР Евгений Алексеевич К.'
                                          f'После оплаты нажмите Я оплатил.\n'
                            f'Средства поступят в течении 20 минут', parse_mode='HTML', reply_markup=buttons.buy_btns())
            elif call.data == 'ibuy':
                pass

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
            if code == 2:
                if verify_user_value(user_input):
                    db_actions.set_user_system_key(user_id, "buy", user_input)
                    bot.send_message(user_id, f'Вы получите {user_input} крипты')
            elif code == 3:
                if verify_user_text(user_input):
                    valid = validate_btc(user_input)
                    if valid:
                        db_actions.set_user_system_key(user_id, "address", user_input)
                        bot.send_message(user_id, 'Успешно!')
                    else:
                        bot.send_message(user_id, 'Кошелек неверен!')

    bot.polling(none_stop=True)


if '__main__' == __name__:
    os_type = platform.system()
    work_dir = os.path.dirname(os.path.realpath(__file__))
    config = ConfigParser(f'{work_dir}/{config_name}', os_type)
    db = DB(config.get_config()['db_file_name'], Lock())
    db_actions = DbAct(db, config, config.get_config()['xlsx_path'])
    bot = telebot.TeleBot(config.get_config()['tg_api'])
    main()
