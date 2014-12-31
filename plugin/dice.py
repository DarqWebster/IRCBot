import re
import random

class Dice:
    errmsg_invalidrollmsg = "I can't roll that..."
    
    def __init__(self):
        self.functions = {"roll":self.roll_str}
        self.msgregexp = re.compile(r"^[0-9]+d[0-9]+$")

    def roll_str(self, msg):
        if not self.msgregexp.match(msg):
            return Dice.errmsg_invalidrollmsg
        dice = msg.split("d")
        return str(self.roll(int(dice[0]), int(dice[1])))

    def roll(self, dice, side):
        tot = 0
        for d in range(dice):
            tot = tot + random.randint(1, side)
        return tot

def getinstance():
    return Dice()
