import random

random.seed()


# функция для отображения корректной формы слова "очки"
def correct_form(n):
    if (n <= 4) or (22 <= n <= 24):
        return "очка"
    elif (n == 21) or (n == 31):
        return "очко"
    else:
        return "очков"


# класс игрока
class Croupier:  # крупье
    def __init__(self):
        self.cards = list()
        self.score = 0
        self.has_blackjack = False


# класс игрока
class Player:
    def __init__(self, chat_id, bet):
        self.id = chat_id  # на будущее
        self.cards = list()
        self.score = 0
        self.bet = bet
        self.has_blackjack = False
        self.is_thinking = False

        self.status = "in_game"

    def lost(self):
        self.status = "lose"

    def stop(self):
        self.is_thinking = False
        self.status = "stop"

    def take(self):
        self.is_thinking = False
        self.status = "take"

    def wait(self):
        self.is_thinking = False
        self.status = "wait"


# игра (каждый экземпляр - одна раздача)
class Blackjack:
    def __init__(self, users: list):
        self.deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K', 'A'] * 4
        random.shuffle(self.deck)

        self.players = list()
        for user in users:
            self.players.append(Player(user[0], user[1]))
        self.croupier = Croupier()

    # функция, имитирующая отображение стола
    def get_current_state(self):
        message = f"у крупье {', '.join(map(str, self.croupier.cards))} ({self.croupier.score} {correct_form(self.croupier.score)})\n"

        if len(self.players) == 1:  # один игрок
            player = self.players[0]
            message += f"у вас {', '.join(map(str, player.cards))} ({player.score} {correct_form(player.score)})\n"
            return message

        else:
            for player in self.players:
                message += f"у {player.id} {', '.join(map(str, player.cards))} ({player.score} {correct_form(player.score)})\n"
            return message

    # функция для подсчёта очков от выпавшей карты
    @staticmethod
    def count_score(card, player):
        if type(card) is int:
            return card
        elif card == "A":
            if player.score <= 10:
                return 11
            else:
                return 1
        else:
            return 10

    # функция для выдачи первой карты крупье
    def croupier_first(self):
        card = self.deck.pop()
        self.croupier.score += self.count_score(card, self.croupier)
        self.croupier.cards.append(card)

    # функция, имитирующая добор крупье
    def croupier_finish(self):
        while self.croupier.score < 17:
            card = self.deck.pop()
            self.croupier.score += self.count_score(card, self.croupier)
            self.croupier.cards.append(card)

    # функция для выдачи карты игроку
    def hit(self, player):
        player.is_thinking = False
        card = self.deck.pop()
        player.cards.append(card)
        player.score += self.count_score(card, player)
        if player.score > 21:
            player.lost()

    # функция для первой раздачи (всем игрокам - по две карты, крупье - одну)
    def deal(self):
        self.croupier_first()

        for player in self.players:
            card1, card2 = self.deck.pop(), self.deck.pop()

            player.score += self.count_score(card1, player)
            player.score += self.count_score(card2, player)
            player.cards.extend((card1, card2))

            if player.score == 21:
                player.has_blackjack = True
                player.status = "blackjack"
