import sqlite3


class BotDB:

    def __init__(self):
        self.connection = sqlite3.connect('casino.db', check_same_thread=False)
        self.cursor = self.connection.cursor()

    def user_exists(self, chat_id):
        """Проверка наличия пользователя в БД"""
        result = self.cursor.execute('SELECT chat_id FROM users WHERE chat_id = ?', (chat_id,))
        return bool(len(result.fetchall()))

    def add_user(self, chat_id):
        """Добавление пользователя в БД"""
        self.cursor.execute('INSERT INTO users (chat_id, balance) VALUES (?, ?)', (chat_id, 0))
        return self.connection.commit()

    def get_balance(self, chat_id):
        """Проверка баланса"""
        result = self.cursor.execute('SELECT balance FROM users WHERE chat_id=?', (chat_id,))
        return result.fetchone()[0]

    def add(self, chat_id, amount):
        """Пополнение баланса"""
        self.cursor.execute('UPDATE users SET balance=balance+? WHERE chat_id=?', (amount, chat_id))
        return self.connection.commit()

    def withdraw(self, chat_id, amount):
        """Снятие с баланса"""
        self.cursor.execute('UPDATE users SET balance=balance-? WHERE chat_id=?', (amount, chat_id))
        return self.connection.commit()

    def close(self):
        """Закрываем соединение с БД"""
        self.connection.close()
