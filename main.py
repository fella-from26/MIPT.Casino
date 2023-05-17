import random
import time

from dotenv import load_dotenv
import telebot
from telebot.types import (InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove)
from moviepy.editor import *

from bandit import Bandit
from blackjack import Blackjack
import messages
import db


# создаю бота, скрывая токен
load_dotenv()
bot = telebot.TeleBot(os.getenv('TOKEN'))
BotDB = db.BotDB()

# данные
bandit_game = Bandit()  # общий для всех пользователей, так как копится общий джекпот
chat_data = dict()  # словарь с данными для чатов


def set_cancel_keyboard(chat_id, text):
    """Функция для отправки клавиатуры с кнопкой для отмены ввода"""

    cancel_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    button_start = KeyboardButton(text="отмена")
    cancel_keyboard.add(button_start)

    bot.send_message(chat_id=chat_id, text=text, reply_markup=cancel_keyboard)


def set_default_keyboard(chat_id, text):
    """Функция для отправки клавиатуры с кнопками базовых действий:"""

    default_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    button_start = KeyboardButton(text="выбрать игру")
    button_balance = KeyboardButton(text="узнать баланс")
    button_deposit = KeyboardButton(text="пополнить баланс")
    default_keyboard.add(button_start)
    default_keyboard.add(button_balance, button_deposit)

    bot.send_message(chat_id=chat_id, text=text, reply_markup=default_keyboard)


def get_chat_data(key):
    """Функция для безопасного обращения к данным чата"""

    if chat_data.get(key) is None:
        chat_data[key] = {'start_message': None, 'blackjack_table': None, "roulette": None}

    return chat_data[key]


@bot.message_handler(commands=['start'])
def start_message(message):
    """Обработчик команды /start и отправки сообщений с выбором игр"""

    # добавляю пользователя в БД
    key = message.chat.id
    if not BotDB.user_exists(key):
        BotDB.add_user(key)

    # удаляю предыдущее сообщение с выбором игр, тем самым поддерживая его единственность:
    if get_chat_data(key)['start_message'] is not None:
        bot.delete_message(chat_id=message.chat.id, message_id=chat_data[key]['start_message'].id)

    # Отправляю клавиатуру для действий:
    set_default_keyboard(message.chat.id, messages.intro)

    # Создаю клавиатуру с выбором игр:
    keyboard = InlineKeyboardMarkup()
    button_game1 = InlineKeyboardButton(text="🎰", callback_data="start - bandit")
    button_game2 = InlineKeyboardButton(text="🃏", callback_data="start - blackjack")
    button_game3 = InlineKeyboardButton(text="🟥⬛️", callback_data="start - roulette")
    keyboard.add(button_game1, button_game2, button_game3)

    # Отправляю сообщение с выбором игр, сохраняя
    get_chat_data(key)['start_message'] = bot.send_message(chat_id=message.chat.id, text=messages.games,
                                                           reply_markup=keyboard)


@bot.message_handler(content_types=['text'])
def handle_text(message):
    """Обработчик отправленного текста"""

    if message.text == "выбрать игру":
        start_message(message)

    elif message.text == "пополнить баланс":
        set_cancel_keyboard(message.chat.id, "Введите сумму:")
        bot.register_next_step_handler(message, input_money, "deposit")

    elif message.text == "узнать баланс":
        bot.send_message(message.chat.id, f"Ваш баланс: {BotDB.get_balance(message.chat.id)}.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("start"))
def callback_query(call):
    """Обработчик нажатия кнопок из сообщения с выбором игр"""

    # решение проблемы с множественным запуском игр:
    key = call.message.chat.id
    if get_chat_data(key)['start_message'] is not None:
        if call.message.message_id != get_chat_data(key)['start_message'].id:
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            return

    # убираю кнопки из сообщения и перестаю считать его стартовым:
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    get_chat_data(key)['start_message'] = None

    # обрабатываю callback data:
    if call.data.endswith("blackjack"):
        bot.edit_message_text(text="Блэкджэк! Погнали!", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        init_game(call.message, "blackjack")

    elif call.data.endswith("roulette"):
        bot.edit_message_text(text="Рулетка! Погнали!", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        init_game(call.message, "roulette")

    elif call.data.endswith("bandit"):
        bot.edit_message_text(text="Однорукий Бандит! Погнали!", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        init_game(call.message, "bandit")


@bot.callback_query_handler(func=lambda call: call.data.startswith("bandit"))
def callback_query(call):
    """Обработчик нажатия кнопок из 'Однорукого Бандита'"""

    # убираю кнопки из сообщения
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)

    # обрабатываю callback data:
    if call.data.endswith("yes"):
        bot.edit_message_text(text="Сыграете снова?\n- Да.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        init_game(call.message, "bandit")

    elif call.data.endswith("no"):
        bot.edit_message_text(text="Сыграете снова?\n- Нет.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        start_message(call.message)

    elif call.data.endswith("same"):
        bot.edit_message_text(text="Сыграете снова?\n- Да, с той же ставкой.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        spin(call.message, int(call.data.split('#')[0].split('-')[1]))


@bot.callback_query_handler(func=lambda call: call.data.startswith("blackjack"))
def callback_query(call):
    """Обработчик нажатия кнопок из блэкджека"""

    # удаляю кнопки из сообщения:
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)

    # фиксирую стол и пользователя, отправившего сообщение:
    key = call.message.chat.id
    game = get_chat_data(key)['blackjack_table']
    player = game.player

    # обрабатываю callback data:
    if call.data.endswith("hit"):
        bot.edit_message_text(text="Ваш ход.\n- Ещё!", chat_id=call.message.chat.id, message_id=call.message.message_id)
        game.hit(player)  # даю карту нужному игроку из нужной игры

    elif call.data.endswith("stop"):
        bot.edit_message_text(text="Ваш ход.\n- Себе.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        player.stop()  # игрок заканчивает набор

    elif call.data.endswith("no risk"):
        bot.edit_message_text(text=f"{messages.decision} забрать.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        player.take()  # игрок забирает блэкджек 1 к 1

    elif call.data.endswith("risk"):
        bot.edit_message_text(text=f"{messages.decision} играть дальше.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        player.wait()  # игрок ждёт вскрытия диллера

    elif call.data.endswith("yes"):
        bot.edit_message_text(text="Сыграете снова?\n- Да.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        init_game(call.message, "blackjack")

    elif call.data.endswith("no"):
        bot.edit_message_text(text="Сыграете снова?\n- Нет.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        start_message(call.message)

    elif call.data.endswith("same"):
        bot.edit_message_text(text="Сыграете снова?\n- Да.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        blackjack(call.message, int(call.data.split('#')[0].split('-')[1]))


@bot.callback_query_handler(func=lambda call: call.data.startswith("roulette"))
def callback_query(call):
    """Обработчик нажатия кнопок из рулетки"""

    # убираю кнопки из сообщения
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)

    # обрабатываю callback data:
    if call.data.endswith("low"):
        bot.edit_message_text(text="Ваш ход.\n- Малые.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        get_chat_data(call.message.chat.id)['roulette'] = "low"

    elif call.data.endswith("high"):
        bot.edit_message_text(text="Ваш ход.\n- Большие.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        get_chat_data(call.message.chat.id)['roulette'] = "high"

    elif call.data.endswith("red"):
        bot.edit_message_text(text="На что ставите?\n- Красное.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        get_chat_data(call.message.chat.id)['roulette'] = "red"

    elif call.data.endswith("black"):
        bot.edit_message_text(text="На что ставите?\n- Чёрное.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        get_chat_data(call.message.chat.id)['roulette'] = "black"

    elif call.data.endswith("even"):
        bot.edit_message_text(text="На что ставите?\n- Чёт.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        get_chat_data(call.message.chat.id)['roulette'] = "even"

    elif call.data.endswith("odd"):
        bot.edit_message_text(text="На что ставите?\n- Нечет.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        get_chat_data(call.message.chat.id)['roulette'] = "odd"

    elif call.data.endswith("zero"):
        bot.edit_message_text(text="На что ставите?\n- Зеро.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        get_chat_data(call.message.chat.id)['roulette'] = "zero"

    elif call.data.endswith("yes"):
        bot.edit_message_text(text="Сыграете снова?\n- Да.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        init_game(call.message, "roulette")

    elif call.data.endswith("no"):
        bot.edit_message_text(text="Сыграете снова?\n- Нет.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        start_message(call.message)

    elif call.data.endswith("same"):
        bot.edit_message_text(text="Сыграете снова?\n- Да, с той же ставкой.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        roulette(call.message, int(call.data.split('#')[0].split('-')[1]))


def init_game(message, game_name):
    """Инициализация игр"""

    if BotDB.get_balance(message.chat.id) == 0:
        bot.send_message(message.chat.id, "Не погнали... Для начала пополните баланс.")
    else:
        set_cancel_keyboard(message.chat.id, f"Баланс: {BotDB.get_balance(message.chat.id)}.\n\nВведите ставку:")
        bot.register_next_step_handler(message, input_money, game_name)


def input_money(message, target):
    """Функция для считывания ставки, введённой пользователем"""

    chat_id = message.chat.id

    # проверка корректного ввода и отлов отмены ввода:
    if message.text[0] == '0':
        bot.send_message(chat_id, "Пожалуйста, введите натуральное число без ведущих нулей.")
        bot.register_next_step_handler(message, input_money, target)
        return

    try:
        amount = int(message.text)
        if amount <= 0:
            bot.send_message(chat_id, "Пожалуйста, введите натуральное число без ведущих нулей.")
            bot.register_next_step_handler(message, input_money, target)
            return
    except ValueError:
        if message.text == "отмена":
            set_default_keyboard(chat_id, "🙄")
            return

        bot.send_message(chat_id, "Пожалуйста, введите натуральное число без ведущих нулей.")
        bot.register_next_step_handler(message, input_money, target)
        return

    # обрабатываю цель ввода:
    balance = BotDB.get_balance(chat_id)
    key = chat_id

    if target == "bandit":
        if amount > balance:
            bot.send_message(chat_id, "Недостаточно средств. Попробуйте снова.")
            bot.register_next_step_handler(message, input_money, target)
        else:
            bot.send_message(chat_id=chat_id, text=f"Ваша ставка: {amount}.", reply_markup=ReplyKeyboardRemove())
            spin(message, amount)

    elif target == "blackjack":
        if amount > balance:
            bot.send_message(chat_id, "Недостаточно средств. Попробуйте снова.")
            bot.register_next_step_handler(message, input_money, target)
        else:
            bot.send_message(chat_id=chat_id, text=f"Ваша ставка: {amount}.", reply_markup=ReplyKeyboardRemove())
            blackjack(message, amount)

    elif target == "roulette":
        if amount > balance:
            bot.send_message(chat_id, "Недостаточно средств. Попробуйте снова.")
            bot.register_next_step_handler(message, input_money, target)
        else:
            bot.send_message(chat_id=chat_id, text=f"Ваша ставка: {amount}.", reply_markup=ReplyKeyboardRemove())
            roulette(message, amount)

    elif target == "deposit":
        BotDB.add(key, amount)
        set_default_keyboard(chat_id, f"Баланс пополнен на {amount}.")


def play_again(message, game_name, bet):
    """Функция, отправляющее предложение сыграть снова"""
    key = message.chat.id
    if BotDB.get_balance(message.chat.id) == 0:
        bot.send_message(message.chat.id, "Чтобы играть дальше, пополните баланс.")
        start_message(message)
    else:
        keyboard = InlineKeyboardMarkup()
        button1 = InlineKeyboardButton(text="нет", callback_data=f"{game_name} - no")
        button2 = InlineKeyboardButton(text="новая ставка", callback_data=f"{game_name} - yes")
        button3 = InlineKeyboardButton(text="та же ставка", callback_data=f"{game_name} - {bet}#same")
        keyboard.add(button1)
        keyboard.add(button2, button3)

        bot.send_message(chat_id=message.chat.id, text=f"Баланс: {BotDB.get_balance(key)}")
        bot.send_message(chat_id=message.chat.id, text="Сыграете снова?", reply_markup=keyboard)


def roulette(message, bet):
    """Запуск рулетки"""

    BotDB.withdraw(message.chat.id, bet)

    keyboard = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton(text="малые", callback_data="roulette - low")
    button2 = InlineKeyboardButton(text="большие", callback_data="roulette - high")
    button3 = InlineKeyboardButton(text="красное", callback_data="roulette - red")
    button4 = InlineKeyboardButton(text="чёрное", callback_data="roulette - black")
    button5 = InlineKeyboardButton(text="чёт", callback_data="roulette - even")
    button6 = InlineKeyboardButton(text="нечет", callback_data="roulette - odd")
    button7 = InlineKeyboardButton(text="зеро", callback_data="roulette - zero")
    keyboard.add(button7)
    keyboard.add(button1, button2)
    keyboard.add(button3, button4)
    keyboard.add(button5, button6)
    bot.send_message(chat_id=message.chat.id, text="На что ставите?", reply_markup=keyboard)

    answer = get_chat_data(message.chat.id)['roulette']
    while answer is None:
        time.sleep(1)
        answer = get_chat_data(message.chat.id)['roulette']
    result = random.randint(0, 36)
    bot.send_animation(chat_id=message.chat.id, animation=open(f"roulette/{result}.mp4", 'rb'))
    time.sleep(4)
    bot.send_message(chat_id=message.chat.id, text=f"{result}")
    if answer == "low" and result <= 18:
        bot.send_message(message.chat.id, f"Ставка прошла!")
        bot.send_message(message.chat.id, f"Ваш выигрыш: {bet * 2}!")
        BotDB.add(message.chat.id, bet * 2)
    elif answer == "high" and result > 18:
        bot.send_message(message.chat.id, f"Ставка прошла!")
        bot.send_message(message.chat.id, f"Ваш выигрыш: {bet * 2}!")
        BotDB.add(message.chat.id, bet * 2)
    elif answer == "red" and result in (32, 19, 21, 25, 34, 27, 36, 30, 23, 5, 16, 1, 14, 9, 18, 7, 12, 3):
        bot.send_message(message.chat.id, f"Ставка прошла!")
        bot.send_message(message.chat.id, f"Ваш выигрыш: {bet * 2}!")
        BotDB.add(message.chat.id, bet * 2)
    elif answer == "black" and result not in (32, 19, 21, 25, 34, 27, 36, 30, 23, 5, 16, 1, 14, 9, 18, 7, 12, 3, 0):
        bot.send_message(message.chat.id, f"Ставка прошла!")
        bot.send_message(message.chat.id, f"Ваш выигрыш: {bet * 2}!")
        BotDB.add(message.chat.id, bet * 2)
    elif answer == "even" and result % 2 == 0 and result != 0:
        bot.send_message(message.chat.id, f"Ставка прошла!")
        bot.send_message(message.chat.id, f"Ваш выигрыш: {bet * 2}!")
        BotDB.add(message.chat.id, bet * 2)
    elif answer == "odd" and result % 2 == 1:
        bot.send_message(message.chat.id, f"Ставка прошла!")
        bot.send_message(message.chat.id, f"Ваш выигрыш: {bet * 2}!")
        BotDB.add(message.chat.id, bet * 2)
    elif answer == "zero" and result == 0:
        bot.send_message(message.chat.id, f"Ставка прошла!")
        bot.send_message(message.chat.id, f"Ваш выигрыш: {bet * 10}!")
        BotDB.add(message.chat.id, bet * 10)
    else:
        bot.send_message(message.chat.id, f"Вы проиграли.")

    get_chat_data(message.chat.id)['roulette'] = None
    play_again(message, "roulette", bet)


def spin(message, bet):
    """Запуск 'Однорукого Бандита'"""

    BotDB.withdraw(message.chat.id, bet)
    combination, win = bandit_game.spin(bet)

    if win != 0:
        bot.send_message(message.chat.id, f"{combination}")
        if combination == "7️⃣ 7️⃣ 7️⃣":
            bot.send_message(message.chat.id, f"Джекпот: {win}!")
        else:
            bot.send_message(message.chat.id, f"Ваш выигрыш: {win}!")
        BotDB.add(message.chat.id, win)
    else:
        bot.send_message(message.chat.id, f"{combination}")
        bot.send_message(message.chat.id, f"Вы проиграли.")

    play_again(message, "bandit", bet)


def blackjack(message, bet):
    """Запуск блэкджека на одного"""

    # фиксирую стол и игрока:
    key = message.chat.id
    game = Blackjack(bet)
    get_chat_data(key)['blackjack_table'] = game
    player = game.player
    croupier = game.croupier

    BotDB.withdraw(message.chat.id, bet)  # уменьшаю баланс

    # начинаю раздачу:
    game.deal()
    bot.send_message(chat_id=message.chat.id, text=game.get_current_state())
    # обрабатываю действия игрока:
    while player.status == "in_game":
        action(message)
        player.is_thinking = True
        while player.is_thinking:
            time.sleep(1)
        if player.status != "stop":
            bot.send_message(chat_id=message.chat.id, text=game.get_current_state())

    # обрабатываю результаты (просто много if-ов, можно не вникать):
    if player.status == "lose":  # перебор у игрока
        bot.send_message(message.chat.id, f"Вы проиграли.")
        play_again(message, "blackjack", bet)

    elif player.has_blackjack:  # блэкджек у игрока
        if croupier.score < 10:  # точно нет блэкджека у крупье
            bot.send_message(message.chat.id, f"Блэкджек! Вы победили!")
            bot.send_message(message.chat.id, f"Ваш выигрыш: {(player.bet * 5 + 1) // 2}!")
            BotDB.add(message.chat.id, (player.bet * 5 + 1) // 2)
            play_again(message, "blackjack", bet)
        else:  # возможный блэкджек у крупье
            # обрабатываю решение игрока:
            choice(message)
            player.is_thinking = True
            while player.is_thinking:
                time.sleep(1)

            if player.status == "take":
                bot.send_message(message.chat.id, f"Ваш выигрыш: {player.bet * 2}!")
                BotDB.add(message.chat.id, player.bet * 2)
                play_again(message, "blackjack", bet)
            elif player.status == "wait":
                game.croupier_finish()
                bot.send_message(chat_id=message.chat.id, text=game.get_current_state())

                if croupier.has_blackjack:
                    bot.send_message(message.chat.id, f"Вы остались при своём: {player.bet}.")
                    BotDB.add(message.chat.id, player.bet)
                    play_again(message, "blackjack", bet)
                else:
                    bot.send_message(message.chat.id, f"Вы победили!")
                    bot.send_message(message.chat.id, f"Ваш выигрыш: {(player.bet * 5 + 1) // 2}!")
                    BotDB.add(message.chat.id, (player.bet * 5 + 1) // 2)
                    play_again(message, "blackjack", bet)

    else:  # остальные случаи: когда у игрока просто набор карт без перебора, и крупье начинает свой добор
        game.croupier_finish()
        bot.send_message(chat_id=message.chat.id, text=game.get_current_state())
        if croupier.has_blackjack:
            bot.send_message(message.chat.id, f"Вы проиграли - у крупье блэкджек.")
            play_again(message, "blackjack", bet)
        elif (croupier.score < player.score) or (croupier.score > 21):
            bot.send_message(message.chat.id, f"Вы победили!")
            bot.send_message(message.chat.id, f"Ваш выигрыш: {player.bet * 2}!")
            BotDB.add(message.chat.id, player.bet * 2)
            play_again(message, "blackjack", bet)
        elif croupier.score == player.score:
            bot.send_message(message.chat.id, f"Ничья")
            bot.send_message(message.chat.id, f"Вы остались при своём: {player.bet}.")
            BotDB.add(message.chat.id, player.bet)
            play_again(message, "blackjack", bet)
        else:
            bot.send_message(message.chat.id, f"Вы проиграли.")
            play_again(message, "blackjack", bet)


def action(message):
    """Функция для отправки клавиатуры с выбором действия при наборе карт игроком"""

    keyboard = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton(text="взять карту", callback_data="blackjack - hit")
    button2 = InlineKeyboardButton(text="остановиться", callback_data="blackjack - stop")
    keyboard.add(button1, button2)
    bot.send_message(chat_id=message.chat.id, text="Ваш ход.", reply_markup=keyboard)


def choice(message):
    """Функция для отправки клавиатуры с выбором действия при блэкджеке у игрока"""

    keyboard = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton(text="забрать сейчас", callback_data="blackjack - no risk")
    button2 = InlineKeyboardButton(text="играть дальше", callback_data="blackjack - risk")
    keyboard.add(button1, button2)
    bot.send_message(chat_id=message.chat.id, text=messages.decision, reply_markup=keyboard)


# запускаю бота
bot.polling()
