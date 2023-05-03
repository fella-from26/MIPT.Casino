import time


import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


import messages
from bandit import Bandit
from blackjack import Blackjack


# создаю бота
bot = telebot.TeleBot("6259702528:AAE4CsmMuuhdDgc0ibwgpMH8nWoRGrE_w90")
# игры и балансы
bandit_game = Bandit()  # общий для всех пользователей, так как копится общий джекпот
blackjack_games = dict()  # словарь (id чата: игра, запущенная в нём)
balances = dict()  # словарь (id чата: баланс)


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_message(message):
    # Создаю клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton(text="🎰", callback_data="start - bandit")
    button2 = InlineKeyboardButton(text="🃏", callback_data="start - blackjack_single")
    button3 = InlineKeyboardButton(text="🃏🃏🃏", callback_data="start - blackjack_multi")
    keyboard.add(button1, button2, button3)

    # Отправляю сообщение с клавиатурой
    bot.send_message(chat_id=message.chat.id, text=messages.games, reply_markup=keyboard)


# Обработчик команды /deposit
@bot.message_handler(commands=['deposit'])
def deposit(message):
    bot.send_message(message.chat.id, "Введите сумму:")
    bot.register_next_step_handler(message, input_money, "deposit")


# Обработчик команды /balance
@bot.message_handler(commands=['balance'])
def balance(message):
    try:
        bot.send_message(message.chat.id, f"Ваш баланс: {balances[message.chat.id]}.")
    except KeyError:
        balances[message.chat.id] = 0
        bot.send_message(message.chat.id, f"Ваш баланс: {0}.")


# обработчики нажатия кнопок:
# start
@bot.callback_query_handler(func=lambda call: call.data.startswith("start"))
def callback_query(call):
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)

    if call.data.endswith("blackjack_single"):
        bot.edit_message_text(text="Блэкджэк! Погнали!", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        init_blackjack_single(call.message)
    elif call.data.endswith("blackjack_multi"):
        bot.edit_message_text(text="Многопользовательский вариант ещё в разработке...", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        start_message(call.message)
    elif call.data.endswith("bandit"):
        bot.edit_message_text(text="Однорукий Бандит! Погнали!", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        init_bandit(call.message)


# bandit
@bot.callback_query_handler(func=lambda call: call.data.startswith("bandit"))
def callback_query(call):
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)

    if call.data.endswith("yes"):
        bot.edit_message_text(text="Сыграете снова? -Да.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        init_bandit(call.message)
    elif call.data.endswith("no"):
        bot.edit_message_text(text="Сыграете снова? -Нет.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        start_message(call.message)


# blackjack_single
@bot.callback_query_handler(func=lambda call: call.data.startswith("blackjack_single"))
def callback_query(call):
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)

    # выбираю игру и игрока:
    key = call.message.chat.id
    game = blackjack_games[key]
    player = game.players[0]

    if call.data.endswith("hit"):
        bot.edit_message_text(text="Вы взяли карту.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        game.hit(player)  # даю карту нужному игроку из нужной игры

    elif call.data.endswith("stop"):
        bot.edit_message_text(text="Вы остановились.", chat_id=call.message.chat.id, message_id=call.message.message_id)
        player.stop()  # игрок заканчивает набор

    elif call.data.endswith("yes"):
        bot.edit_message_text(text="Сыграете снова? -Да.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        init_blackjack_single(call.message)

    elif call.data.endswith("no"):
        bot.edit_message_text(text="Сыграете снова? -Нет.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        start_message(call.message)

    elif call.data.endswith("no risk"):
        bot.edit_message_text(text=f"{messages.decision} забрать.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        player.take()
    elif call.data.endswith("risk"):
        bot.edit_message_text(text=f"{messages.decision} играть дальше.", chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        player.wait()


# инициализация "Однорукого Бандита"
def init_bandit(message):
    bot.send_message(message.chat.id, "Введите ставку:")
    bot.register_next_step_handler(message, input_money, "bandit")


# инициализация блэкджэка на одного
def init_blackjack_single(message):
    bot.send_message(message.chat.id, "Введите ставку:")
    bot.register_next_step_handler(message, input_money, "blackjack_single")


# функция для считывания ставки, введённой пользователем
def input_money(message, target):
    if message.text[0] == '0':
        bot.send_message(message.chat.id, "Пожалуйста, введите натуральное число без ведущих нулей.")
        bot.register_next_step_handler(message, input_money, target)
        return

    try:  # пробую считать введённую сумму
        amount = int(message.text)
        if amount <= 0:
            bot.send_message(message.chat.id, "Пожалуйста, введите натуральное число.")
            bot.register_next_step_handler(message, input_money, target)
            return

        try:  # пробую обратиться к балансу и создаю его, если он ещё не создан
            if target == "bandit":
                if amount > balances[message.chat.id]:
                    bot.send_message(message.chat.id, "Недостаточно средств.")
                else:
                    bot.send_message(message.chat.id, f"Ваша ставка: {amount}.")
                    balances[message.chat.id] -= amount
                    spin(message, amount)

            elif target == "blackjack_single":
                if amount > balances[message.chat.id]:
                    bot.send_message(message.chat.id, "Недостаточно средств.")
                else:
                    balances[message.chat.id] -= amount
                    blackjack_single(message, amount)

            elif target == "deposit":
                balances[message.chat.id] += amount  # пополняю баланс пользователя
                bot.send_message(message.chat.id, f"Баланс пополнен на {amount}.")

        except KeyError:
            if target == "deposit":
                balances[message.chat.id] = amount  # создаю баланс пользователя
                bot.send_message(message.chat.id, f"Баланс пополнен на {amount}.")
            else:
                balances[message.chat.id] = 0
                bot.send_message(message.chat.id, "Недостаточно средств.")

    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите натуральное число.")
        bot.register_next_step_handler(message, input_money, target)


# функция, отправляющее предложение сыграть снова
def play_again(message, game_name):
    keyboard = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton(text="да", callback_data=game_name + " - yes")
    button2 = InlineKeyboardButton(text="нет", callback_data=game_name + " - no")
    keyboard.add(button1, button2)
    bot.send_message(chat_id=message.chat.id, text="Сыграете снова?", reply_markup=keyboard)


# вращение "Однорукого Бандита"
def spin(message, bet):
    combination, win = bandit_game.spin(bet)
    if win != 0:
        bot.send_message(message.chat.id, f"{combination}")
        bot.send_message(message.chat.id, f"Ваш выигрыш: {win}!")
        balances[message.chat.id] += win
    else:
        bot.send_message(message.chat.id, f"{combination}")
        bot.send_message(message.chat.id, f"Вы проиграли.")

    play_again(message, "bandit")


# раздача блэкджека на одного
def blackjack_single(message, bet):
    # выбираю игру и игрока:
    key = message.chat.id
    game = Blackjack([(key, bet)])
    blackjack_games[key] = game
    player = game.players[0]
    croupier = game.croupier

    # начинаю раздачу:
    game.deal()
    bot.send_message(chat_id=message.chat.id, text=game.get_current_state())
    while player.status == "in_game":  # обрабатываю действия игрока
        action(message)
        player.is_thinking = True
        while player.is_thinking:
            time.sleep(1)
        if player.status != "stop":
            bot.send_message(chat_id=message.chat.id, text=game.get_current_state())

    # обрабатываю результаты (много if-ов, можно не вникать)
    if player.status == "lose":  # перебор у игрока
        bot.send_message(message.chat.id, f"Вы проиграли.")
        play_again(message, "blackjack_single")

    elif player.has_blackjack:  # блэкджек у игрока
        if croupier.score < 10:  # точно нет блэкджека у крупье
            bot.send_message(message.chat.id, f"Блэкджек! Вы победили!")
            bot.send_message(message.chat.id, f"Ваш выигрыш: {(player.bet * 5 + 1) // 2}!")
            balances[message.chat.id] += (player.bet * 5 + 1) // 2
            play_again(message, "blackjack_single")
        else:  # возможный блэкджек у крупье
            # обрабатываю решение игрока:
            choice(message)
            player.is_thinking = True
            while player.is_thinking:
                time.sleep(1)

            if player.status == "take":
                bot.send_message(message.chat.id, f"Ваш выигрыш: {player.bet * 2}!")
                balances[message.chat.id] += player.bet * 2
                play_again(message, "blackjack_single")
            elif player.status == "wait":
                game.croupier_finish()
                bot.send_message(chat_id=message.chat.id, text=game.get_current_state())

                if croupier.has_blackjack:
                    bot.send_message(message.chat.id, f"Вы остались при своём: {player.bet}.")
                    balances[message.chat.id] += player.bet
                    play_again(message, "blackjack_single")
                else:
                    bot.send_message(message.chat.id, f"Вы победили!")
                    bot.send_message(message.chat.id, f"Ваш выигрыш: {(player.bet * 5 + 1) // 2}!")
                    balances[message.chat.id] += (player.bet * 5 + 1) // 2
                    play_again(message, "blackjack_single")

    else:  # случай, когда у игрока просто набор карт и крупье начинает набирать
        game.croupier_finish()
        bot.send_message(chat_id=message.chat.id, text=game.get_current_state())
        if croupier.has_blackjack:
            bot.send_message(message.chat.id, f"Вы проиграли - у крупье блэкджек.")
            play_again(message, "blackjack_single")
        elif (croupier.score < player.score) or (croupier.score > 21):
            bot.send_message(message.chat.id, f"Вы победили!")
            bot.send_message(message.chat.id, f"Ваш выигрыш: {player.bet * 2}!")
            balances[message.chat.id] += player.bet * 2
            play_again(message, "blackjack_single")
        elif croupier.score == player.score:
            bot.send_message(message.chat.id, f"Ничья")
            bot.send_message(message.chat.id, f"Вы остались при своём: {player.bet}.")
            balances[message.chat.id] += player.bet
            play_again(message, "blackjack_single")
        else:
            bot.send_message(message.chat.id, f"Вы проиграли.")
            play_again(message, "blackjack_single")


# функция для отправки клавиатуры с выбором действия при наборе карт игроком
def action(message):
    keyboard = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton(text="взять карту", callback_data="blackjack_single - hit")
    button2 = InlineKeyboardButton(text="остановиться", callback_data="blackjack_single - stop")
    keyboard.add(button1, button2)
    bot.send_message(chat_id=message.chat.id, text="Действие:", reply_markup=keyboard)


# функция для отправки клавиатуры с выбором действия при блэкджеке у игрока
def choice(message):
    keyboard = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton(text="забрать сейчас", callback_data="blackjack_single - no risk")
    button2 = InlineKeyboardButton(text="играть дальше", callback_data="blackjack_single - risk")
    keyboard.add(button1, button2)
    bot.send_message(chat_id=message.chat.id, text=messages.decision, reply_markup=keyboard)


# запускаю бота
bot.polling()
