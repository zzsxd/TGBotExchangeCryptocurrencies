import pandas as pd


class TempUserData:
    def __init__(self):
        super(TempUserData, self).__init__()
        self.__user_data = {}

    def temp_data(self, user_id):
        if user_id not in self.__user_data.keys():
            self.__user_data.update({user_id: [None, None, None, None, None, None, None, None]})
        return self.__user_data


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
                'INSERT INTO users (user_id, first_name, last_name, nick_name, is_admin) VALUES (?, ?, ?, ?, ?)',
                (user_id, first_name, last_name, nick_name, is_admin))

    def user_is_existed(self, user_id):
        data = self.__db.db_read('SELECT count(*) FROM users WHERE user_id = ?', (user_id,))
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

    def get_user_id(self):
        return self.__db.db_read('SELECT user_id FROM users', ())

    def add_new_buy(self, name):
        self.__db.db_write('INSERT INTO buy (name) VALUES (?)', (name, ))

    def get_buy_btns(self):
        return self.__db.db_read('SELECT row_id, name FROM buy', ())

    def del_buy_btns(self, row_id):
        self.__db.db_write('DELETE FROM buy WHERE row_id = ?', (row_id, ))

    def add_new_sell(self, name):
        self.__db.db_write('INSERT INTO sell (name) VALUES (?)', (name, ))

    def get_sell_btns(self):
        return self.__db.db_read('SELECT row_id, name FROM sell', ())

    def del_sell_btns(self, row_id):
        self.__db.db_write('DELETE FROM sell WHERE row_id = ?', (row_id, ))

    def add_new_exchange(self, name):
        self.__db.db_write('INSERT INTO exchange (name) VALUES (?)', (name, ))

    def get_exchange_btns(self):
        return self.__db.db_read('SELECT row_id, name FROM exchange', ())

    def del_exchange_btns(self, row_id):
        self.__db.db_write('DELETE FROM exchange WHERE row_id = ?', (row_id, ))

    def db_export_xlsx(self):
        d = {'Имя': [], 'Фамилия': [], 'Никнейм': []}
        users = self.__db.db_read('SELECT first_name, last_name, nick_name FROM users', ())
        if len(users) > 0:
            for user in users:
                for info in range(len(list(user))):
                    d[self.__fields[info]].append(user[info])
            df = pd.DataFrame(d)
            df.to_excel(self.__config.get_config()['xlsx_path'], sheet_name='Пользователи', index=False)
