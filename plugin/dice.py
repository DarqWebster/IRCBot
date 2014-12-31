import random

class Dice:
    def __init__(self):
        self.functions = {"roll":self.roll_str}

    def roll_str(self, msg):
        dice = msg.split("d")
        return str(self.roll(int(dice[0]), int(dice[1])))

    def roll(self, dice, side):
        tot = 0
        for d in range(dice):
            tot = tot + random.randint(1, side)
        return tot

def getinstance():
    return Dice()
