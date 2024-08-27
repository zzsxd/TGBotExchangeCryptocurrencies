import pandas as pd
import json


class DbAct:
    def __init__(self, db, config, path_xlsx):
        super(DbAct, self).__init__()
        self.__db = db
        self.__config = config
        self.__fields = ['Имя', 'Фамилия', 'Никнейм']
        self.__dump_path_xlsx = path_xlsx

    def add_user(self, user_id, first_name, last_name, nick_name):
        if not self.user_is_existed(user_id):
            if user_id in self.__config.get_config()['admins']:
                is_admin = True
            else:
                is_admin = False
            self.__db.db_write(
                'INSERT INTO users (user_id, first_name, last_name, nick_name, system_data, is_admin) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                (user_id, first_name, last_name, nick_name, json.dumps({"index": None, "admin_action": None,
                                                                        "admin_exchange_direction": None,
                                                                        "user_currency_order": None,
                                                                        "quantity_user": None,
                                                                        "user_application_id": None,
                                                                        "destination_address": None,
                                                                        "admin_currency_name": None,
                                                                        "admin_currency_cost": None,
                                                                        "address_transaction": None,
                                                                        "user_first_exchange": None,
                                                                        "user_second_exchange": None,
                                                                        "admin_application_id": None,
                                                                        "reason_reject_admin": None,
                                                                        "admin_add_crypto_address": None,
                                                                        "crypto_min_cost": None,
                                                                        "backward_message": []}), is_admin))

    def add_group(self, group_id: int, chat_type: str):
        if not self.group_is_existed(group_id) and chat_type in ["supergroup"]:
            self.__db.db_write(
                'INSERT INTO groups (group_id, system_data) '
                'VALUES (?, ?)',
                (group_id, json.dumps({"index": None, "admin_transaction_address": None,
                                       "admin_cancel_reason": None})))

    def user_is_existed(self, user_id):
        data = self.__db.db_read('SELECT count(*) FROM users WHERE user_id = ?', (user_id,))
        if len(data) > 0:
            if data[0][0] > 0:
                status = True
            else:
                status = False
            return status

    def group_is_existed(self, group_id):
        data = self.__db.db_read('SELECT count(*) FROM groups WHERE group_id = ?', (group_id,))
        if len(data) > 0:
            if data[0][0] > 0:
                status = True
            else:
                status = False
            return status

    def user_is_admin(self, user_id):
        data = self.__db.db_read('SELECT is_admin FROM users WHERE user_id = ?', (user_id,))
        if len(data) > 0:
            if data[0][0] == 1:
                status = True
            else:
                status = False
            return status

    def set_user_system_key(self, user_id: int, key: str, value: any) -> None:
        system_data = self.get_user_system_data(user_id)
        if system_data is None:
            return None
        system_data = json.loads(system_data)
        system_data[key] = value
        self.__db.db_write('UPDATE users SET system_data = ? WHERE user_id = ?', (json.dumps(system_data), user_id))

    def get_user_system_key(self, user_id: int, key: str):
        system_data = self.get_user_system_data(user_id)
        if system_data is None:
            return None
        system_data = json.loads(system_data)
        if key not in system_data.keys():
            return None
        return system_data[key]

    def get_user_system_data(self, user_id: int):
        if not self.user_is_existed(user_id):
            return None
        return self.__db.db_read('SELECT system_data FROM users WHERE user_id = ?', (user_id,))[0][0]

    ########################################################################################################

    def set_group_system_key(self, user_id: int, key: str, value: any) -> None:
        system_data = self.get_group_system_data(user_id)
        if system_data is None:
            return None
        system_data = json.loads(system_data)
        system_data[key] = value
        self.__db.db_write('UPDATE groups SET system_data = ? WHERE group_id = ?', (json.dumps(system_data), user_id))

    def get_group_system_key(self, user_id: int, key: str):
        system_data = self.get_group_system_data(user_id)
        if system_data is None:
            return None
        system_data = json.loads(system_data)
        if key not in system_data.keys():
            return None
        return system_data[key]

    def get_group_system_data(self, user_id: int):
        if not self.group_is_existed(user_id):
            return None
        return self.__db.db_read('SELECT system_data FROM groups WHERE group_id = ?', (user_id,))[0][0]

    ########################################################################################################

    def add_exchange_rates(self, name: str, cost: float, min_cost: float, crypto_address: str, type: str):
        self.__db.db_write('INSERT INTO exchange_rates (name, cost, min_cost, crypto_address, type) VALUES (?, ?, ?, ?, ?)', (name, cost, min_cost, crypto_address, type))

    def get_exchange_rates(self, type: str):
        return self.__db.db_read('SELECT row_id, name, cost, min_cost, crypto_address FROM exchange_rates WHERE type = ?', (type, ))

    def get_exchange_rate(self, row_id: int) -> tuple:
        return self.__db.db_read('SELECT name, cost, min_cost, crypto_address FROM exchange_rates WHERE row_id = ?', (row_id,))[0]

    def get_exchange_rate_by_name(self, name: str) -> float:
        return self.__db.db_read('SELECT cost FROM exchange_rates WHERE name = ?', (name, ))[0][0]

    def del_exchange_rates(self, row_id: str):
        self.__db.db_write('DELETE FROM exchange_rates WHERE row_id = ?', (row_id, ))

    ########################################################################################################
        
    def update_topic_id(self, user_id, topic_id):
        self.__db.db_write('UPDATE users SET topic_id = ? WHERE user_id = ?', (topic_id, user_id))

    def get_user_id_from_topic(self, topic_id):
        data = self.__db.db_read("SELECT user_id FROM users WHERE topic_id = ?", (topic_id, ))
        if len(data) > 0:
            return data[0][0]

    def get_datas_from_application(self, row_id: int):
        return self.__db.db_read("SELECT user_id, address_transaction, source_currency, source_quantity, target_currency, target_quantity FROM applications WHERE row_id = ?", (row_id,))[0]

    def get_name_user(self, user_id: int):
        return self.__db.db_read('SELECT nick_name, first_name, last_name FROM users WHERE user_id = ?', (user_id, ))[0]
    
    def add_application(self, user_id: int, source_currency: str, source_quantity: float,
                        target_currency: str, target_quantity: float, destination_address: str) -> int:
        application_id = self.__db.db_write("INSERT INTO applications (user_id, source_currency, "
                                            "source_quantity, target_currency, target_quantity, "
                                            "destination_address, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                            (user_id, source_currency, source_quantity, target_currency,
                                             target_quantity, destination_address, False))
        if application_id is None:
            return False
        return application_id

    def get_application(self, row_id: int) -> tuple:
        return self.__db.db_read('SELECT target_quantity, destination_address FROM applications WHERE row_id = ?', (row_id, ))[0]

    def add_transaction_address(self, transaction_id: str, application_id: int):
        self.__db.db_write('UPDATE applications SET address_transaction = ? WHERE row_id = ?', (transaction_id, application_id,))

    def db_export_xlsx(self):
        d = {'Имя': [], 'Фамилия': [], 'Никнейм': []}
        users = self.__db.db_read('SELECT first_name, last_name, nick_name FROM users', ())
        if len(users) > 0:
            for user in users:
                for info in range(len(list(user))):
                    d[self.__fields[info]].append(user[info])
            df = pd.DataFrame(d)
            df.to_excel(self.__config.get_config()['xlsx_path'], sheet_name='Пользователи', index=False)
