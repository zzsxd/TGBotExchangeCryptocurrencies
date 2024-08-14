import telebot
import os
import platform
import cryptocompare
import coinaddrvalidator
from datetime import datetime
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


def verify_user_float(user_input: str) -> bool:
    if not verify_user_text(user_input):
        return False
    try:
        float(user_input)
        return True
    except ValueError:
        return False


def validate_crypto_wallet(coin, address):
    try:
        y = coinaddrvalidator.validate(coin, address)
        if y.valid:
            return True
        else:
            return False
    except:
        return False


def validate_mir(card_number):

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

    try:
        if len(card_number) != 16:
            return False

        if not card_number.startswith('2'):
            return False

        return luhn_checksum(card_number) == 0
    except:
        return False


def get_current_time():
    return datetime.now().strftime("%d:%m:%Y, %H:%M")


def current_crypto_price(currency_symbol):
    try:
        price = cryptocompare.get_price(currency_symbol, currency='RUB')
        return price[currency_symbol]['RUB']
    except Exception as e:
        return False


def main():
    @bot.message_handler(commands=['start', 'admin', 'buy', 'sell', 'exchange'])
    def start(message):
        command = message.text.replace('/', '')
        user_id = message.from_user.id
        buttons = Bot_inline_btns()
        db_actions.add_user(user_id, message.from_user.first_name, message.from_user.last_name,
                            f'@{message.from_user.username}')
        # db_actions.add_user_id(user_id)
        if command == 'start':
            bot.send_message(user_id,
                             '<b>Привет! 👋</b>\n\n'
                             '🤖Я бот для <u>Приобритения, продажи и обмена криптовалют</u> ✅\n\n'
                             '/buy - покупка\n\n'
                             '/sell - продажа\n\n'
                             '/exchange - обмен',
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
                elif call.data == 'export':
                    db_actions.db_export_xlsx()
                    bot.send_document(user_id, open(config.get_config()['xlsx_path'], 'rb'))
                    os.remove(config.get_config()['xlsx_path'])
            if call.data[:9] == 'first_buy':
                db_actions.set_user_system_key(user_id, "user_currency_order", call.data[9:])
                exchange_currency = db_actions.get_exchange_rate(call.data[9:])

                bot.send_message(user_id, 'Создание заявки на покупку!\n\n'
                                          f'Заполните заявку для покупки {exchange_currency[0]}\n\n'
                                          f'Цена за 1 {exchange_currency[0]} - {exchange_currency[1]}',
                                 reply_markup=buttons.buy_request_btns())
            elif call.data == 'buy_quantity':
                db_actions.set_user_system_key(user_id, "index", 3)
                bot.send_message(user_id, 'Введите количество желаемой крипты')
            elif call.data == 'buy_address':
                db_actions.set_user_system_key(user_id, "index", 4)
                bot.send_message(user_id, 'Введите адрес кошелька')
            elif call.data == 'buy_continue':
                if db_actions.get_user_system_key(user_id, "quantity_user") is None:
                    bot.send_message(user_id, 'Вы не указали количество получаемой крипты!')

                elif db_actions.get_user_system_key(user_id, "destination_address") is None:
                    bot.send_message(user_id, 'Вы не указали адрес кошелька для получения!')
                else:
                    # Создание заявки для транзакции
                    application_id = db_actions.add_application(user_id=user_id,
                                                                quantity=db_actions.get_user_system_key(user_id, "quantity_user"),
                                                                destination_address=db_actions.get_user_system_key(user_id, "destination_address"))
                    if application_id:
                        # Получение названия выбранной крипты и ее стоимости 0 - currency, 1 - cost
                        exchange_currency = db_actions.get_exchange_rate(
                            db_actions.get_user_system_key(user_id, "user_currency_order"))
                        rub_cost = db_actions.get_user_system_key(user_id, "quantity_user") * exchange_currency[1]

                        db_actions.set_user_system_key(user_id, "user_application_id", application_id)

                        bot.send_message(user_id, 'Проверьте, что все данные указаны верно!\n\n'
                                                  f'Номер заявки: {application_id}\n\n'
                                                  f'Вы покупаете {db_actions.get_user_system_key(user_id, "quantity_user")} ВТС за {rub_cost} МИР. руб.\n'
                                                  f'Средства будут переведены на адрес '
                                                  f'{exchange_currency[0]}: {db_actions.get_user_system_key(user_id, "destination_address")}\n\n'
                                                  f'Для совершения операции отправьте {rub_cost} р.\n'
                                                  f'на номер <code>4536 6363 6262 6636</code>, карта МИР Евгений Алексеевич К.\n\n'
                                                  f'После оплаты нажмите кнопку: "Я оплатил"\n'
                                                  f'Средства поступят в течении 20 минут', parse_mode='HTML',
                                         reply_markup=buttons.buy_btns())
                    else:
                        bot.send_message(user_id, "...")
            elif call.data == 'ibuy':
                application_id = db_actions.get_user_system_key(user_id, "user_application_id")
                user_data = db_actions.get_name_user(user_id)
                application = db_actions.get_application(application_id)
                time_now = get_current_time()
                topic_id = telebot.TeleBot.create_forum_topic(bot, chat_id=config.get_config()['group_id'],
                                                              name=f'{user_data[1]} '
                                                                   f'{user_data[2]} ПОКУПКА',
                                                              icon_color=0x6FB9F0).message_thread_id
                db_actions.update_topic_id(user_id, topic_id)
                bot.send_message(chat_id=config.get_config()['group_id'], message_thread_id=topic_id,
                                 text=f'Номер заявки: {application_id}\n\n'
                                      f'Время заявки: {time_now}\n'
                                      f'Пользователь: {user_data[0]}\n'
                                      f'Направление обмена "тут типа в какую крипту переводим"\n'
                                      f'Количество крипты: {application[0]}\n'
                                      f'Адрес кошелька: <code>{application[1]}</code>', parse_mode='HTML')
                bot.send_message(user_id, 'Ваша заявка принята в работу, ожидайте!')

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
                        crypto_price = current_crypto_price(user_input)
                        if crypto_price:
                            db_actions.set_user_system_key(user_id, "admin_currency_name", user_input)
                            db_actions.set_user_system_key(user_id, "index", 1)
                            bot.send_message(user_id, f"Введите коэффициент курса для "
                                                      f"пользователей относительно текущего курса {user_input} = {crypto_price} р")
                        else:
                            bot.send_message(user_id, "Такой крипты нет, иди бананы жуй")
                    else:
                        bot.send_message(user_id, "Это не текст")
                elif code == 1:
                    if verify_user_float(user_input):
                        db_actions.set_user_system_key(user_id, "admin_currency_cost", float(user_input))
                        db_actions.set_user_system_key(user_id, "index", 2)
                        bot.send_message(user_id, "Введите минимально возможную стоимость для пользователей")
                    else:
                        bot.send_message(user_id, "Это не число")
                elif code == 2:
                    if verify_user_float(user_input):
                        direction = db_actions.get_user_system_key(user_id, "admin_exchange_direction")
                        coin_name = db_actions.get_user_system_key(user_id, "admin_currency_name")
                        coin_cost = db_actions.get_user_system_key(user_id, "admin_currency_cost")
                        db_actions.add_exchange_rates(coin_name, current_crypto_price(coin_name) * float(coin_cost),
                                                      float(user_input), direction)
                        db_actions.set_user_system_key(user_id, "index", None)
                        bot.send_message(user_id, "Операция успешно совершена")
                    else:
                        bot.send_message(user_id, "Это не число")
            if code == 3:
                if verify_user_float(user_input):
                    currency_id = db_actions.get_user_system_key(user_id, "user_currency_order")
                    min_cost = db_actions.get_exchange_rate(currency_id)[2]
                    if float(user_input) >= min_cost:
                        exchange_currency = db_actions.get_exchange_rate(currency_id)
                        db_actions.set_user_system_key(user_id, "quantity_user", float(user_input))
                        db_actions.set_user_system_key(user_id, "index", None)
                        bot.send_message(user_id, f'Вы получите {user_input} {exchange_currency[0]}')
                    else:
                        bot.send_message(user_id, f"Введенная вами сумма ({user_input}) меньше минимальной ({min_cost})")
                else:
                    bot.send_message(user_id, 'Неправильный ввод!')
            elif code == 4:
                if verify_user_text(user_input):
                    currency_id = db_actions.get_user_system_key(user_id, "user_currency_order")
                    exchange_currency = db_actions.get_exchange_rate(currency_id)
                    if validate_crypto_wallet(exchange_currency[0], user_input):
                        db_actions.set_user_system_key(user_id, "index", None)
                        db_actions.set_user_system_key(user_id, "destination_address", user_input)
                        bot.send_message(user_id, 'Кошелек подтвержден!')
                    else:
                        bot.send_message(user_id, 'Кошелек неверен!')
                else:
                    bot.send_message(user_id, 'Неправильный ввод!')

    bot.polling(none_stop=True)


if '__main__' == __name__:
    os_type = platform.system()
    work_dir = os.path.dirname(os.path.realpath(__file__))
    config = ConfigParser(f'{work_dir}/{config_name}', os_type)
    db = DB(config.get_config()['db_file_name'], Lock())
    db_actions = DbAct(db, config, config.get_config()['xlsx_path'])
    bot = telebot.TeleBot(config.get_config()['tg_api'])
    main()
