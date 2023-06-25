import random

random.seed()


class Bandit:

    def __init__(self):
        self.jackpot = random.randint(10000, 1000000)  # симулирую джекпот
        self.symbols = ('🍒', '🍎', '🍋', '💎', '💰', '7️⃣')

    def spin(self, bet):
        """Запуск бандита"""
        attempts = 2
        a, b, c = random.choice(self.symbols), random.choice(self.symbols), random.choice(self.symbols)
        while (not a == b == c) and (attempts > 0):
            a, b, c = random.choice(self.symbols), random.choice(self.symbols), random.choice(self.symbols)
            attempts -= 1

        combination = f"{a} {b} {c}"

        if a == b == c == self.symbols[0]:
            return combination, bet * 3
        elif a == b == c == self.symbols[1]:
            return combination, bet * 5
        elif a == b == c == self.symbols[2]:
            return combination, bet * 10
        elif a == b == c == self.symbols[3]:
            return combination, bet * 50
        elif a == b == c == self.symbols[4]:
            return combination, bet * 100
        elif a == b == c == self.symbols[5]:
            temp = self.jackpot
            self.jackpot = 0
            return combination, bet + temp
        
        self.jackpot += bet
        return combination, 0
