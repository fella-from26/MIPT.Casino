import random

random.seed()


# игра (один экземпляр на всех игроков)
class Bandit:
    def __init__(self):
        self.jackpot = random.randint(10000, 1000000)  # симулирую джекпот
        self.symbols = ('🍒', '🍎', '🍋', '💎', '💰', '7️⃣')

    def spin(self, bet):
        a, b, c = random.choice(self.symbols), random.choice(self.symbols), random.choice(self.symbols)
        combination = f"{a} {b} {c}"

        if a == b == c == self.symbols[0]:
            return combination, bet
        elif a == b == c == self.symbols[1]:
            return combination, bet * 3
        elif a == b == c == self.symbols[2]:
            return combination, bet * 5
        elif a == b == c == self.symbols[3]:
            return combination, bet * 10
        elif a == b == c == self.symbols[4]:
            return combination, bet * 100
        elif a == b == c == self.symbols[5]:
            temp = self.jackpot
            self.jackpot = 0
            return combination, bet + temp
        
        self.jackpot += bet
        return combination, 0
