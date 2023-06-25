import random

random.seed()


def correct_form(n):
    """Корректная форма слова 'очки'"""
    if (n <= 4) or (22 <= n <= 24):
        return "очка"
    elif (n == 21) or (n == 31):
        return "очко"
    else:
        return "очков"


class Croupier:

    def __init__(self):
        self.cards = list()
        self.score = 0
        self.has_blackjack = False


class Player:

    def __init__(self, bet):
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


class Blackjack:

    def __init__(self, bet):
        self.deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K', 'A'] * 4
        random.shuffle(self.deck)

        self.player = Player(bet)
        self.croupier = Croupier()

    def get_current_state(self):
        """Функция для отображения карт игрока и крупье"""
        message = f"у крупье {', '.join(map(str, self.croupier.cards))} ({self.croupier.score} {correct_form(self.croupier.score)})\n"

        player = self.player
        message += f"у вас {', '.join(map(str, player.cards))} ({player.score} {correct_form(player.score)})\n"
        return message

    @staticmethod
    def count_score(card, player):
        """Функция для подсчёта очков от выпавшей карты"""
        if type(card) is int:
            return card
        elif card == "A":
            if player.score <= 10:
                return 11
            else:
                return 1
        else:
            return 10

    def croupier_first(self):
        """Функция для выдачи первой карты крупье"""
        card = self.deck.pop()
        self.croupier.score += self.count_score(card, self.croupier)
        self.croupier.cards.append(card)

    def croupier_finish(self):
        """Функция, имитирующая добор крупье"""
        while self.croupier.score < 17:
            card = self.deck.pop()
            self.croupier.score += self.count_score(card, self.croupier)
            self.croupier.cards.append(card)

    def hit(self, player):
        """Функция для выдачи карты игроку"""
        player.is_thinking = False
        card = self.deck.pop()
        player.cards.append(card)
        player.score += self.count_score(card, player)
        if player.score > 21:
            player.lost()

    def deal(self):
        """Функция для первой раздачи (всем игрокам - по две карты, крупье - одну)"""
        self.croupier_first()

        card1, card2 = self.deck.pop(), self.deck.pop()

        self.player.score += self.count_score(card1, self.player)
        self.player.score += self.count_score(card2, self.player)
        self.player.cards.extend((card1, card2))

        if self.player.score == 21:
            self.player.has_blackjack = True
            self.player.status = "blackjack"
