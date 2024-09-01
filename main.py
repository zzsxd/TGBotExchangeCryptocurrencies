import telebot
import os
import re
import platform
import cryptocompare
import coinaddrvalidator
import pytz
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
        patterns = {
            'BTC': r'^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}$',
            'USDT': r'^T[1-9A-HJ-NP-Za-km-z]{33}$',
            'BCH': r'^([13CH][a-zA-HJ-NP-Z0-9]{25,39}|q[0-9a-z]{41})$',
            'DASH': r'^X[1-9A-HJ-NP-Za-km-z]{33}$',
            'DOGE': r'^(D|A|9)[1-9A-HJ-NP-Za-km-z]{33}$',
            'ETH': r'^0x[a-fA-F0-9]{40}$',
            'LTC': r'^[LM3][a-km-zA-HJ-NP-Z1-9]{26,33}$',
            'BNB': r'^(bnb1)[0-9a-z]{38}$',
            'SOL': r'^[1-9A-HJ-NP-Za-km-z]{32,44}$',
            'TONCOIN': r'^EQ[A-Za-z0-9_-]{47}$',
        }

        pattern = patterns.get(coin.upper())
        if pattern and re.match(pattern, address):
            return True
        else:
            return False
    except:
        return False


def clear_local_states(user_id):
    db_actions.set_user_system_key(user_id, "quantity_user", None)
    db_actions.set_user_system_key(user_id, "destination_address", None)


def validate_mir(card_number):
    def luhn_checksum(card_number):
        def digits_of(n):
            return [int(d) for d in str(n)]

        digits = digits_of(card_number.replace(' ', ''))
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10 == 0 or checksum % 10 == 1 or checksum % 10 == 2 or checksum % 10 == 3 or checksum % 10 == 4 or checksum % 10 == 5 or checksum % 10 == 6 or checksum % 10 == 7 or checksum % 10 == 8 or checksum % 10 == 9

    try:
        # Удаление пробелов из номера карты
        card_number = card_number.replace(' ', '')

        # Проверка длины номера карты
        if len(card_number) != 16:
            return False

        # Проверка префикса номера карты
        if not card_number.startswith('220'):
            return False

        # Проверка по алгоритму Луна
        return luhn_checksum(card_number)
    except:
        return False


def get_current_time():
    moscow_tz = pytz.timezone('Europe/Moscow')
    moscow_time = datetime.now(moscow_tz)
    return moscow_time.strftime("%d.%m.%Y, %H:%M")


def current_crypto_price(currency_symbol):
    try:
        price = cryptocompare.get_price(currency_symbol, currency='RUB')
        return price[currency_symbol]['RUB']
    except Exception as e:
        return False


def back_method(user_id, command):
    if command == '<back>':
        try:
            message_ids = db_actions.get_user_system_key(user_id, "backward_message")
            db_actions.set_user_system_key(user_id, "backward_message", message_ids[:-1])
            message_id = message_ids[-1]
            bot.delete_message(user_id, message_id)
            return False
        except Exception as e:
            return True
    return True


def send_message(user_id, args, buttons=None, parse_mode=None):
    message_id = None

    if buttons is None and parse_mode is None:
        message_id = bot.send_message(*args).message_id
    elif buttons is not None and parse_mode is None:
        message_id = bot.send_message(*args, reply_markup=buttons).message_id
    elif buttons is None and parse_mode is not None:
        message_id = bot.send_message(*args, parse_mode=parse_mode).message_id
    elif buttons is not None and parse_mode is not None:
        message_id = bot.send_message(*args, parse_mode=parse_mode, reply_markup=buttons).message_id

    message_ids = db_actions.get_user_system_key(user_id, "backward_message")
    message_ids.append(message_id)
    db_actions.set_user_system_key(user_id, "backward_message", message_ids)


def calculate_exchange_price(give_currency, give_quantity, get_currency):
    give_currency_price = db_actions.get_exchange_rate_by_name(give_currency)
    get_currency_price = db_actions.get_exchange_rate_by_name(get_currency)
    return round(((float(give_quantity) * float(give_currency_price)) / float(get_currency_price)), 2)


def main():
    @bot.message_handler(commands=['start', 'admin', 'buy', 'sell'])  # 'exchange'
    def start(message):
        command = message.text.replace('/', '')
        user_id = message.from_user.id
        group_id = message.chat.id
        chat_type = message.chat.type
        buttons = Bot_inline_btns()
        db_actions.add_user(user_id, message.from_user.first_name, message.from_user.last_name,
                            f'@{message.from_user.username}')
        db_actions.add_group(group_id, chat_type)
        if command == 'start':
            bot.send_message(user_id,
                             '<b>Привет! 👋</b>\n\n'
                             '🤖Я бот для <u>приобритения, продажи и обмена криптовалют</u> ✅\n\n'
                             '/buy - 💰 покупка криптовалюты 💰\n\n'
                             '/sell - 💸 продажа криптовалюты 💸\n\n',
                             parse_mode='HTML')
            # /exchange - 🤑 обмен криптовалюты 🤑
        elif command == 'buy':
            buy_buttons = db_actions.get_exchange_rates("buy")
            send_message(user_id, [user_id,
                                   '💰Здесь Вы можете <u>купить криптовалюту</u> по выгодному курсу <b><u>без регистрации!</u></b>💰\n\n'
                                   'Выберите направление покупки:'], buttons=buttons.buy_crypto_btns(buy_buttons),
                         parse_mode='HTML')
        elif command == 'sell':
            sell_buttons = db_actions.get_exchange_rates("sell")
            send_message(user_id, [user_id,
                                   '💸Здесь Вы можете <u>продать криптовалюту</u> по выгодному курсу <b><u>без регистрации!</u></b>💸\n\n'
                                   'Выберите направление продажи:'], buttons=buttons.sell_crypto_btns(sell_buttons),
                         parse_mode='HTML')
        # elif command == 'exchange':
        #     exchange_buttons = db_actions.get_exchange_rates("exchange")
        #     send_message(user_id, [user_id, '🤑Здесь Вы можете <u>обменять криптовалюту</u> по выгодному курсу <b><u>без регистрации!</u></b>🤑\n\n'
        #                               'Выберите какую криптовалюту менять:'], buttons=buttons.exchange_crypto_btns(exchange_buttons), parse_mode='HTML')
        elif db_actions.user_is_admin(user_id):
            if command == 'admin':
                bot.send_message(user_id, '✅ Вы успешно зашли в админ-панель! ✅',
                                 reply_markup=buttons.admin_btns())

    @bot.callback_query_handler(func=lambda call: True)
    def callback(call):
        user_id = call.message.chat.id
        buttons = Bot_inline_btns()
        if db_actions.user_is_existed(user_id):
            if db_actions.user_is_admin(user_id):

                ############################################### ADMIN #################################################

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
                    bot.send_message(user_id, "✅ Направление успешно удалено ✅")
                elif call.data == 'export':
                    db_actions.db_export_xlsx()
                    bot.send_document(user_id, open(config.get_config()['xlsx_path'], 'rb'))
                    os.remove(config.get_config()['xlsx_path'])

            ################################################## BUY ####################################################

            if call.data[:9] == 'first_buy':
                if back_method(user_id, call.data[9:]):
                    clear_local_states(user_id)
                    db_actions.set_user_system_key(user_id, "user_currency_order", call.data[9:])
                    exchange_currency = db_actions.get_exchange_rate(call.data[9:])
                    send_message(user_id, [user_id, f'Заполните заявку для покупки {exchange_currency[0]}\n\n'
                                                    f'Цена за 1 {exchange_currency[0]} - {round(exchange_currency[1], 2)}₽'],
                                 buttons=buttons.buy_request_btns())
            elif call.data == 'start':
                bot.send_message(user_id,
                                 '<b>Привет, хочешь совершить еще обмен? 👋</b>\n\n'
                                 '<u>выбирай команду снизу!</u> ✅\n\n'
                                 '/buy - 💰 покупка криптовалюты 💰\n\n'
                                 '/sell - 💸 продажа криптовалюты 💸\n\n',
                                 parse_mode='HTML')
            elif call.data == 'buy_quantity':
                db_actions.set_user_system_key(user_id, "index", 3)
                bot.send_message(user_id, '💸Введите количество криптовалюты на покупку 💸')
            elif call.data == 'buy_address':
                db_actions.set_user_system_key(user_id, "index", 4)
                bot.send_message(user_id, '💳 Введите адрес кошелька 💳')
            elif call.data[:12] == 'buy_continue':
                if back_method(user_id, call.data[12:]):
                    # 1 - Количество которую меняем 2 - адрес кошелька назначения 3 - Количество которое получаем
                    quantity_first = db_actions.get_user_system_key(user_id, "quantity_user")
                    dest_address = db_actions.get_user_system_key(user_id, "destination_address")

                    if quantity_first is None:
                        bot.send_message(user_id, '❌ Вы не указали количество продаваемой криптовалюты! ❌')

                    elif dest_address is None:
                        bot.send_message(user_id, '❌ Вы не указали номер карты для получения! ❌')
                    else:
                        # Получение названия выбранной крипты и ее стоимости 0 - currency, 1 - cost
                        crypto_data = db_actions.get_exchange_rate(
                            db_actions.get_user_system_key(user_id, "user_currency_order"))
                        quantity_second = db_actions.get_user_system_key(user_id, "quantity_user") * crypto_data[1]
                        first_crypto = crypto_data[0]
                        # Создание заявки для транзакции
                        application_id = db_actions.add_application(user_id=user_id,
                                                                    source_currency="RUB",
                                                                    source_quantity=quantity_second,
                                                                    target_currency=first_crypto,
                                                                    target_quantity=quantity_first,
                                                                    destination_address=dest_address)
                        if application_id:

                            db_actions.set_user_system_key(user_id, "user_application_id", application_id)

                            send_message(user_id, [user_id, 'Проверьте, что все данные указаны верно!\n\n'
                                                            f'Номер заявки: {application_id}\n\n'
                                                            f'Вы покупаете {quantity_first} {first_crypto} за {round(quantity_second, 2)} ₽\n'
                                                            f'Средства будут переведены на адрес: '
                                                            f'{first_crypto}: {dest_address}\n\n'
                                                            f'Для совершения операции отправьте {quantity_second} ₽ '
                                                            f'на номер\n💳💳💳💳💳💳💳💳\n'
                                                            '<code>4536 6363 6262 6636</code>\n'
                                                            '💳💳💳💳💳💳💳💳\nкарта МИР Евгений Алексеевич К.\n\n'
                                                            f'После оплаты нажмите кнопку: "Я оплатил"\n'
                                                            f'Средства поступят в течении 20 минут'], parse_mode="HTML",
                                         buttons=buttons.buy_btns())
                        else:
                            bot.send_message(user_id, "❌ Ошибка ❌")
            elif call.data[:3] == 'buy':
                if back_method(user_id, call.data[3:]):
                    exchange_currency = db_actions.get_exchange_rate(
                        db_actions.get_user_system_key(user_id, "user_currency_order"))
                    rub_cost = db_actions.get_user_system_key(user_id, "quantity_user") * exchange_currency[1]
                    application_id = db_actions.get_user_system_key(user_id, "user_application_id")
                    user_data = db_actions.get_name_user(user_id)
                    application = db_actions.get_application(application_id)
                    time_now = get_current_time()
                    topic_id = telebot.TeleBot.create_forum_topic(bot, chat_id=config.get_config()['group_id'],
                                                                  name=f'{user_data[1]} '
                                                                       f'{user_data[2]} ПОКУПКА {exchange_currency[0]}',
                                                                  icon_color=0x6FB9F0).message_thread_id
                    db_actions.update_topic_id(user_id, topic_id)
                    bot.send_message(chat_id=config.get_config()['group_id'], message_thread_id=topic_id,
                                     text=f'Номер заявки: {application_id}\n'
                                          f'Время заявки: {time_now} МСК\n\n'
                                          f'Пользователь: {user_data[0]}\n'
                                          f'Направление обмена: Карта -> {exchange_currency[0]}\n'
                                          f'Сумма покупки: {round(rub_cost, 2)}₽\n'
                                          f'Количество {exchange_currency[0]} на покупку: {application[0]} {exchange_currency[0]}\n'
                                          f'Адрес кошелька: <code>{application[1]}</code>',
                                     parse_mode='HTML', reply_markup=buttons.topic_btns(application_id))
                    bot.send_message(user_id, '⏳ Ваша заявка принята в работу, ожидайте! ⏳')

            ################################################## SELL ####################################################

            elif call.data[:10] == 'first_sell':
                if back_method(user_id, call.data[10:]):
                    clear_local_states(user_id)
                    db_actions.set_user_system_key(user_id, "user_currency_order", call.data[10:])
                    exchange_currency = db_actions.get_exchange_rate(call.data[10:])
                    send_message(user_id, [user_id, f'Заполните заявку для продажи {exchange_currency[0]}\n\n'
                                                    f'Цена за 1 {exchange_currency[0]} - {round(exchange_currency[1], 2)}₽'],
                                 buttons=buttons.sell_request_btns())
            elif call.data == 'sell_quantity':
                db_actions.set_user_system_key(user_id, "index", 6)
                bot.send_message(user_id, 'Введите количество криптовалюты на продажу')
            elif call.data == 'sell_address':
                db_actions.set_user_system_key(user_id, "index", 7)
                bot.send_message(user_id, 'Введите номер карты (МИР)')
            elif call.data[:13] == 'sell_continue':
                if back_method(user_id, call.data[13:]):
                    # 1 - Количество которую меняем 2 - адрес кошелька назначения 3 - Количество которое получаем
                    quantity_first = db_actions.get_user_system_key(user_id, "quantity_user")
                    dest_address = db_actions.get_user_system_key(user_id, "destination_address")

                    if quantity_first is None:
                        bot.send_message(user_id, '❌ Вы не указали количество продаваемой криптовалюты! ❌')

                    elif dest_address is None:
                        bot.send_message(user_id, '❌ Вы не указали номер карты для получения! ❌')
                    else:
                        # Получение названия выбранной крипты и ее стоимости 0 - currency, 1 - cost
                        crypto_data = db_actions.get_exchange_rate(
                            db_actions.get_user_system_key(user_id, "user_currency_order"))
                        quantity_second = db_actions.get_user_system_key(user_id, "quantity_user") * crypto_data[1]
                        first_crypto = crypto_data[0]
                        crypto_address = crypto_data[3]
                        # Создание заявки для транзакции
                        application_id = db_actions.add_application(user_id=user_id,
                                                                    source_currency=first_crypto,
                                                                    source_quantity=quantity_first,
                                                                    target_currency="RUB",
                                                                    target_quantity=quantity_second,
                                                                    destination_address=dest_address)
                        if application_id:
                            db_actions.set_user_system_key(user_id, "user_application_id", application_id)
                            send_message(user_id, [user_id, 'Проверьте, что все данные указаны верно!\n\n'
                                                            f'Номер заявки: {application_id}\n\n'
                                                            f'Вы продаете {quantity_first} {first_crypto} за {round(quantity_second, 2)} ₽\n'
                                                            f'Средства будут переведены на карту: '
                                                            f'{dest_address}\n\n'
                                                            f'Для совершения операции отправьте {quantity_first} {first_crypto} '
                                                            f'на адрес\n💳💳💳💳💳💳💳💳💳\n'
                                                            f'<code>{crypto_address}</code>\n'
                                                            '💳💳💳💳💳💳💳💳💳\n'
                                                            f'После оплаты нажмите кнопку: "Я оплатил"\n'
                                                            f'Средства поступят после первого подтвеждения сети'],
                                         buttons=buttons.sell_btns(), parse_mode='HTML')
                        else:
                            bot.send_message(user_id, "❌ Ошибка ❌")
            elif call.data[:4] == 'sell':
                if back_method(user_id, call.data[4:]):
                    quantity_first = db_actions.get_user_system_key(user_id, "quantity_user")
                    exchange_currency = db_actions.get_exchange_rate(
                        db_actions.get_user_system_key(user_id, "user_currency_order"))
                    rub_cost = db_actions.get_user_system_key(user_id, "quantity_user") * exchange_currency[1]
                    application_id = db_actions.get_user_system_key(user_id, "user_application_id")
                    user_data = db_actions.get_name_user(user_id)
                    application = db_actions.get_application(application_id)
                    time_now = get_current_time()
                    topic_id = telebot.TeleBot.create_forum_topic(bot, chat_id=config.get_config()['group_id'],
                                                                  name=f'{user_data[1]} '
                                                                       f'{user_data[2]} ПРОДАЖА {exchange_currency[0]}',
                                                                  icon_color=0x6FB9F0).message_thread_id
                    db_actions.update_topic_id(user_id, topic_id)
                    bot.send_message(chat_id=config.get_config()['group_id'], message_thread_id=topic_id,
                                     text=f'Номер заявки: {application_id}\n'
                                          f'Время заявки: {time_now} МСК\n\n'
                                          f'Пользователь: {user_data[0]}\n'
                                          f'Направление обмена: {exchange_currency[0]} -> КАРТА\n'
                                          f'Сумма продажи: {round(rub_cost, 2)}₽\n'
                                          f'Количество {exchange_currency[0]} на продажу: {quantity_first} {exchange_currency[0]}\n'
                                          f'Номер карты: <code>{application[1]}</code>',
                                     parse_mode='HTML', reply_markup=buttons.sell_topic_btns(application_id))
                    bot.send_message(user_id, '⏳ Ваша заявка принята в работу, ожидайте! ⏳')

            ############################################### EXCHANGE ##################################################

            elif call.data[:14] == 'first_exchange':
                if back_method(user_id, call.data[14:]):
                    clear_local_states(user_id)
                    db_actions.set_user_system_key(user_id, "user_first_exchange", call.data[14:])
                    exchange_buttons = db_actions.get_exchange_rates("exchange")
                    send_message(user_id, [user_id, f'Выберите на какую криптовалюту менять'],
                                 buttons=buttons.exchange_btns(exchange_buttons, call.data[14:]))
            elif call.data[:16] == 'request_exchange':
                if back_method(user_id, call.data[16:]):
                    db_actions.set_user_system_key(user_id, "user_second_exchange", call.data[16:])

                    first_currency_id = db_actions.get_user_system_key(user_id, "user_first_exchange")
                    second_currency_id = db_actions.get_user_system_key(user_id, "user_second_exchange")

                    first_currency_data = db_actions.get_exchange_rate(first_currency_id)
                    second_currency_data = db_actions.get_exchange_rate(second_currency_id)
                    send_message(user_id, [user_id,
                                           f'Заполните заявку для обмена {first_currency_data[0]} на {second_currency_data[0]}\n\n'],
                                 buttons=buttons.exchange_request_btns())
            elif call.data == 'exchange_quantity':
                db_actions.set_user_system_key(user_id, "index", 8)
                bot.send_message(user_id, 'Введите количество криптовалюты на обмен')
            elif call.data == 'exchange_address':
                db_actions.set_user_system_key(user_id, "index", 9)
                bot.send_message(user_id, '💳 Введите адрес кошелька 💳')
            elif call.data[:17] == 'exchange_continue':
                if back_method(user_id, call.data[17:]):
                    # 1 - крипта на продажу 2 - крипта для получения
                    first_crypto = \
                        db_actions.get_exchange_rate(
                            db_actions.get_user_system_key(user_id, "user_first_exchange"))[0]
                    second_crypto = \
                        db_actions.get_exchange_rate(
                            db_actions.get_user_system_key(user_id, "user_second_exchange"))[0]
                    crypto_address = db_actions.get_exchange_rate(db_actions.get_user_system_key(user_id, "user_second_exchange"))[3]

                    # 1 - Количество которую меняем 2 - адрес кошелька назначения 3 - Количество которое получаем
                    quantity_first = db_actions.get_user_system_key(user_id, "quantity_user")
                    dest_address = db_actions.get_user_system_key(user_id, "destination_address")

                    if quantity_first is None:
                        bot.send_message(user_id, f'❌ Вы не указали количество {first_crypto}! ❌')

                    elif dest_address is None:
                        bot.send_message(user_id, f'❌ Вы не указали адрес {second_crypto} для получения! ❌')
                    else:
                        quantity_second = calculate_exchange_price(first_crypto, quantity_first, second_crypto)
                        # Создание заявки для транзакции
                        application_id = db_actions.add_application(user_id=user_id,
                                                                    source_currency=first_crypto,
                                                                    source_quantity=quantity_first,
                                                                    target_currency=second_crypto,
                                                                    target_quantity=quantity_second,
                                                                    destination_address=dest_address)
                        if application_id:
                            db_actions.set_user_system_key(user_id, "user_application_id", application_id)
                            send_message(user_id, [user_id, 'Проверьте, что все данные указаны верно!\n\n'
                                                            f'Номер заявки: {application_id}\n\n'
                                                            f'Вы меняете {quantity_first} {first_crypto} за {quantity_second} {second_crypto}\n'
                                                            f'Средства будут переведены на кошелек: '
                                                            f'{dest_address}\n\n'
                                                            f'Для совершения операции отправьте {quantity_first} {first_crypto} '
                                                            f'на адрес\n💳💳💳💳💳💳💳💳💳\n'
                                                            f'<code>{crypto_address}</code>\n'
                                                            '💳💳💳💳💳💳💳💳💳\n'
                                                            f'После оплаты нажмите кнопку: "Я оплатил"\n'
                                                            f'Средства поступят после первого подтвеждения сети'],
                                         buttons=buttons.exchange(), parse_mode='HTML')
                        else:
                            bot.send_message(user_id, "❌ Ошибка ❌")
            elif call.data[:8] == 'exchange':
                if back_method(user_id, call.data[8:]):
                    # 1 - крипта на продажу 2 - крипта для получения
                    first_crypto = \
                    db_actions.get_exchange_rate(db_actions.get_user_system_key(user_id, "user_first_exchange"))[0]
                    second_crypto = \
                    db_actions.get_exchange_rate(db_actions.get_user_system_key(user_id, "user_second_exchange"))[0]

                    # 1 - Количество которую меняем 2 - адрес кошелька назначения 3 - Количество которое получаем
                    quantity_first = db_actions.get_user_system_key(user_id, "quantity_user")
                    quantity_second = calculate_exchange_price(first_crypto, quantity_first, second_crypto)
                    exchange_currency = db_actions.get_exchange_rate(
                        db_actions.get_user_system_key(user_id, "user_currency_order"))
                    application_id = db_actions.get_user_system_key(user_id, "user_application_id")
                    user_data = db_actions.get_name_user(user_id)
                    application = db_actions.get_application(application_id)
                    time_now = get_current_time()
                    topic_id = telebot.TeleBot.create_forum_topic(bot, chat_id=config.get_config()['group_id'],
                                                                  name=f'{user_data[1]} '
                                                                       f'{user_data[2]} ОБМЕН {exchange_currency[0]}',
                                                                  icon_color=0x6FB9F0).message_thread_id
                    db_actions.update_topic_id(user_id, topic_id)
                    bot.send_message(chat_id=config.get_config()['group_id'], message_thread_id=topic_id,
                                     text=f'Номер заявки: {application_id}\n'
                                          f'Время заявки: {time_now} МСК\n\n'
                                          f'Пользователь: {user_data[0]}\n'
                                          f'Направление обмена: {first_crypto} -> {second_crypto}\n'
                                          f'Количество {first_crypto} на обмен: {quantity_first} {first_crypto}\n'
                                          f'Количество {second_crypto} на получение: {quantity_second} {second_crypto}\n'
                                          f'Адрес кошелька: <code>{application[1]}</code>',
                                     parse_mode='HTML', reply_markup=buttons.topic_btns(application_id))
                    bot.send_message(user_id, '⏳ Ваша заявка принята в работу, ожидайте! ⏳')

        ############################################### ADMIN_APPLICATIONS #########################################################

        elif db_actions.group_is_existed(user_id):
            if call.data[:7] == 'confirm':
                print('123')
                application_id = call.data[7:]
                bot.send_message(chat_id=config.get_config()['group_id'],
                                 message_thread_id=call.message.reply_to_message.message_thread_id,
                                 text='Введите адрес транзакции')
                ## все ключи воркают только исползуй "set_group_system_key" и "get_group_system_key"
                db_actions.set_group_system_key(user_id, "index", 0)
                db_actions.set_group_system_key(user_id, "admin_application_id", application_id)
            elif call.data[:12] == 'sell_confirm':
                application_id = call.data[12:]
                user_datas = db_actions.get_datas_from_application(application_id)
                bot.send_message(chat_id=user_datas[0],
                                 text=f'Номер заявки: {application_id}\n'
                                      f'Статус: Выполнено\n'
                                      f'Время совершения операции МСК: {get_current_time()}\n'
                                      f'Вы продали {user_datas[5]} {user_datas[4]} за {round(user_datas[3], 2)} {user_datas[2]}\n'
                                      f'Спасибо за пользование нашим сервисом!',
                                 reply_markup=buttons.new_application_btns(),
                                 parse_mode='HTML')
                bot.send_message(chat_id=config.get_config()['group_id'],
                                 message_thread_id=call.message.reply_to_message.message_thread_id,
                                 text='Заявка успешно закрыта!')
            elif call.data == 'close_application':
                application_id = db_actions.get_group_system_key(user_id, "admin_application_id")
                user_datas = db_actions.get_datas_from_application(application_id)
                bot.send_message(chat_id=user_datas[0],
                                 text=f'Номер заявки: {application_id}\n'
                                      f'Статус: Выполнено\n'
                                      f'Время совершения операции МСК: {get_current_time()}\n'
                                      f'Вы купили {user_datas[5]} {user_datas[4]} за {round(user_datas[3], 2)} {user_datas[2]}\n'
                                      f'Адрес транзакции: <code>{user_datas[1]}</code>\n\n'
                                      f'Спасибо за пользование нашим сервисом!',
                                 reply_markup=buttons.new_application_btns(),
                                 parse_mode='HTML')
                bot.send_message(chat_id=config.get_config()['group_id'],
                                 message_thread_id=call.message.reply_to_message.message_thread_id,
                                 text='Заявка успешно закрыта!')
            elif call.data[:6] == 'reject':
                application_id = call.data[6:]
                db_actions.set_group_system_key(user_id, "admin_application_id", application_id)
                db_actions.set_group_system_key(user_id, "index", 1)
                bot.send_message(chat_id=config.get_config()['group_id'],
                                 message_thread_id=call.message.reply_to_message.message_thread_id,
                                 text='Введите причину отмены!')
            elif call.data == 'close_reject_application':
                application_id = db_actions.get_group_system_key(user_id, "admin_application_id")
                reason_reject = db_actions.get_group_system_key(user_id, "reason_reject_admin")
                user_datas = db_actions.get_datas_from_application(application_id)
                bot.send_message(chat_id=user_datas[0],
                                 text=f'Номер заявки: {application_id}\n'
                                      f'Статус: Отклонено\n'
                                      f'Время отклонения по МСК: {get_current_time()}\n'
                                      f'Причина отмены: {reason_reject}', reply_markup=buttons.new_application_btns())
                bot.send_message(chat_id=config.get_config()['group_id'],
                                 message_thread_id=call.message.reply_to_message.message_thread_id,
                                 text='Заявка успешно отклонена!')

    @bot.message_handler(content_types=['text', 'photo'])
    def text_message(message):
        user_input = message.text
        user_id = message.chat.id
        buttons = Bot_inline_btns()
        code = db_actions.get_user_system_key(user_id, "index")
        group_code = db_actions.get_group_system_key(user_id, "index")
        if db_actions.user_is_existed(user_id):
            if db_actions.user_is_admin(user_id):
                if code == 0:
                    if verify_user_text(user_input):
                        crypto_price = current_crypto_price(user_input)
                        if crypto_price:
                            db_actions.set_user_system_key(user_id, "admin_currency_name", user_input)
                            db_actions.set_user_system_key(user_id, "index", 1)
                            bot.send_message(user_id, f"Введите наценку для "
                                                      f"пользователей относительно текущего курса {user_input} = {crypto_price}₽\n\n"
                                                      f"(>1.0 для прибавления в цене / <1.0 для убавления в цене)")
                        else:
                            bot.send_message(user_id, "❌ Введенная криптовалюта не найдена ❌")
                    else:
                        bot.send_message(user_id, "❌ Это не текст ❌")
                elif code == 1:
                    if verify_user_float(user_input):
                        db_actions.set_user_system_key(user_id, "admin_currency_cost", float(user_input))
                        db_actions.set_user_system_key(user_id, "index", 2)
                        bot.send_message(user_id,
                                         "Сколько пользователь может минимально купить (продать/обменять)?\n\n")
                    else:
                        bot.send_message(user_id, "❌ Это не число ❌")
                elif code == 2:
                    if verify_user_float(user_input):
                        db_actions.set_user_system_key(user_id, "crypto_min_cost", float(user_input))
                        coin_name = db_actions.get_user_system_key(user_id, "admin_currency_name")
                        db_actions.set_user_system_key(user_id, "index", 10)
                        bot.send_message(user_id, f'Введите адрес кошелька для выбранной криптовалюты: {coin_name}')
                    else:
                        bot.send_message(user_id, "❌ Это не число ❌")
                elif code == 10:
                    if verify_user_text(user_input):
                        direction = db_actions.get_user_system_key(user_id, "admin_exchange_direction")
                        coin_name = db_actions.get_user_system_key(user_id, "admin_currency_name")
                        coin_cost = db_actions.get_user_system_key(user_id, "admin_currency_cost")
                        min_cost = db_actions.get_user_system_key(user_id, "crypto_min_cost")
                        db_actions.add_exchange_rates(coin_name, current_crypto_price(coin_name) * float(coin_cost),
                                                      min_cost, str(user_input), direction)
                        db_actions.set_user_system_key(user_id, "index", None)
                        bot.send_message(user_id, "✅ Операция успешно совершена ✅")
                    else:
                        bot.send_message(user_id, "❌ Это не адрес ❌")
            if code == 3:
                if verify_user_float(user_input):
                    currency_id = db_actions.get_user_system_key(user_id, "user_currency_order")
                    min_cost = db_actions.get_exchange_rate(currency_id)[2]
                    if float(user_input) >= min_cost:
                        exchange_currency = db_actions.get_exchange_rate(currency_id)
                        db_actions.set_user_system_key(user_id, "quantity_user", float(user_input))
                        db_actions.set_user_system_key(user_id, "index", None)
                        bot.send_message(user_id, f'💰 Вы получите {user_input} {exchange_currency[0]} 💰')
                        if db_actions.get_user_system_key(user_id, "destination_address") is None:
                            db_actions.set_user_system_key(user_id, "index", 4)
                            bot.send_message(user_id, '💳 Введите адрес кошелька 💳')
                    else:
                        bot.send_message(user_id,
                                         f"❌ Введенная вами сумма ({user_input}) меньше минимальной ({min_cost}) ❌")
                else:
                    bot.send_message(user_id, '❌ Неправильный ввод! ❌')
            elif code == 4:
                if verify_user_text(user_input):
                    currency_id = db_actions.get_user_system_key(user_id, "user_currency_order")
                    exchange_currency = db_actions.get_exchange_rate(currency_id)
                    if validate_crypto_wallet(exchange_currency[0], user_input):
                        db_actions.set_user_system_key(user_id, "index", None)
                        db_actions.set_user_system_key(user_id, "destination_address", user_input)
                        bot.send_message(user_id, '✅ Кошелек подтвержден! ✅', reply_markup=buttons.next_buy_btn())
                        if db_actions.get_user_system_key(user_id, "quantity_user") is None:
                            db_actions.set_user_system_key(user_id, "index", 3)
                            bot.send_message(user_id, '💸Введите количество криптовалюты на покупку 💸')
                    else:
                        bot.send_message(user_id, '❌ Введенный кошелек неправильный! ❌')
                else:
                    bot.send_message(user_id, '❌ Неправильный ввод! ❌')
            elif code == 6:
                if verify_user_float(user_input):
                    currency_id = db_actions.get_user_system_key(user_id, "user_currency_order")
                    min_cost = db_actions.get_exchange_rate(currency_id)[2]
                    if float(user_input) >= min_cost:
                        exchange_currency = db_actions.get_exchange_rate(currency_id)
                        db_actions.set_user_system_key(user_id, "quantity_user", float(user_input))
                        db_actions.set_user_system_key(user_id, "index", None)
                        user_get_cost = float(user_input) * float(exchange_currency[1])
                        bot.send_message(user_id,
                                         f'💰 За {user_input} {exchange_currency[0]} вы получите {round(user_get_cost, 2)}₽ 💰', reply_markup=buttons.sell_next_bnt())
                        if db_actions.get_user_system_key(user_id, "destination_address") is None:
                            db_actions.set_user_system_key(user_id, "index", 7)
                            bot.send_message(user_id, '💳 Введите номер карты 💳')
                    else:
                        bot.send_message(user_id,
                                         f"❌ Введенная вами сумма ({user_input}) меньше минимальной ({min_cost}) ❌")
                else:
                    bot.send_message(user_id, '❌ Неправильный ввод! ❌')
            elif code == 7:
                if verify_user_text(user_input):
                    if validate_mir(user_input):
                        db_actions.set_user_system_key(user_id, "index", None)
                        db_actions.set_user_system_key(user_id, "destination_address", user_input)
                        bot.send_message(user_id, '✅ Карта подтверждена! ✅', reply_markup=buttons.sell_next_bnt())
                        if db_actions.get_user_system_key(user_id, "quantity_user") is None:
                            db_actions.set_user_system_key(user_id, "index", 6)
                            bot.send_message(user_id, '💸Введите количество криптовалюты на продажу 💸')
                    else:
                        bot.send_message(user_id, '❌ Введенная карта неверна! ❌\n\n'
                                                  '(Только карты МИР\n'
                                                  'Пример: 2200 1234 5678 9010)')
                else:
                    bot.send_message(user_id, '❌ Неправильный ввод! ❌')
            elif code == 8:
                if verify_user_float(user_input):
                    currency_id = db_actions.get_user_system_key(user_id, "user_currency_order")
                    min_cost = db_actions.get_exchange_rate(currency_id)[2]
                    first_crypto = \
                    db_actions.get_exchange_rate(db_actions.get_user_system_key(user_id, "user_first_exchange"))[0]
                    second_crypto = \
                    db_actions.get_exchange_rate(db_actions.get_user_system_key(user_id, "user_second_exchange"))[0]
                    quantity_first = db_actions.get_user_system_key(user_id, "quantity_user")
                    quantity_second = calculate_exchange_price(first_crypto, quantity_first, second_crypto)
                    if float(user_input) >= min_cost:
                        db_actions.set_user_system_key(user_id, "quantity_user", float(user_input))
                        db_actions.set_user_system_key(user_id, "index", None)
                        bot.send_message(user_id,
                                         f'💰За {user_input} {first_crypto} вы получите {quantity_second} {second_crypto} 💰')
                        if db_actions.get_user_system_key(user_id, "destination_address") is None:
                            db_actions.set_user_system_key(user_id, "index", 9)
                            bot.send_message(user_id, '💳 Введите адрес кошелька 💳')
                    else:
                        bot.send_message(user_id,
                                         f"❌ Введенная вами сумма ({user_input}) меньше минимальной ({min_cost}) ❌")
                else:
                    bot.send_message(user_id, '❌ Неправильный ввод! ❌')
            elif code == 9:
                first_crypto = \
                db_actions.get_exchange_rate(db_actions.get_user_system_key(user_id, "user_first_exchange"))[0]
                if verify_user_text(user_input):
                    if validate_crypto_wallet(first_crypto, user_input):
                        db_actions.set_user_system_key(user_id, "index", None)
                        db_actions.set_user_system_key(user_id, "destination_address", user_input)
                        bot.send_message(user_id, '✅ Кошелек подтвержден! ✅')
                        if db_actions.get_user_system_key(user_id, "quantity_user") is None:
                            db_actions.set_user_system_key(user_id, "index", 8)
                            bot.send_message(user_id, '💸Введите количество криптовалюты на обмен 💸')
                    else:
                        bot.send_message(user_id, '❌ Введенный кошелек неправильный! ❌')
                else:
                    bot.send_message(user_id, '❌ Неправильный ввод! ❌')
        elif db_actions.group_is_existed(user_id):
            if group_code == 0:
                if verify_user_text(user_input):
                    application_id = db_actions.get_group_system_key(user_id, "admin_application_id")
                    db_actions.add_transaction_address(user_input, application_id)
                    bot.send_message(chat_id=config.get_config()['group_id'],
                                     message_thread_id=message.reply_to_message.message_thread_id,
                                     text='✅ Адрес транзакции успешно подтвержден ✅',
                                     reply_markup=buttons.close_request_btns())
                else:
                    bot.send_message(chat_id=config.get_config()['group_id'],
                                     message_thread_id=message.reply_to_message.message_thread_id,
                                     text='❌ Неправильный ввод! ❌')
            elif group_code == 1:
                if verify_user_text(user_input):
                    db_actions.set_group_system_key(user_id, "reason_reject_admin", user_input)
                    bot.send_message(chat_id=config.get_config()['group_id'],
                                     message_thread_id=message.reply_to_message.message_thread_id,
                                     text='✅ Причина отмены указана! ✅', reply_markup=buttons.close_application_btns())

    bot.polling(none_stop=True)


if '__main__' == __name__:
    os_type = platform.system()
    work_dir = os.path.dirname(os.path.realpath(__file__))
    config = ConfigParser(f'{work_dir}/{config_name}', os_type)
    db = DB(config.get_config()['db_file_name'], Lock())
    db_actions = DbAct(db, config, config.get_config()['xlsx_path'])
    bot = telebot.TeleBot(config.get_config()['tg_api'])
    main()
