import re
import random

class Dice:
    name_regexps = {"name"}
    errmsg_invalidrollmsg = "I can't roll that..."
    
    def __init__(self, bot):
        base_patt = re.compile(r"^roll [0-9]+d[0-9]+$");
        bot.addfunction(lambda msg: bot.is_to_me(msg) and base_patt.match(bot.strip_nick(msg.trailing)), self.roll_msg)
        name_patt = re.compile(r"^roll [0-9]+d(" + "|".join(name_regexp for name_regexp in Dice.name_regexps) + ")$");
        bot.addfunction(lambda msg: bot.is_to_me(msg) and not bot.is_private(msg) and name_patt.match(bot.strip_nick(msg.trailing)), self.roll_name_msg)
        bot.addfunction(lambda msg: msg.command == "PRIVMSG" and msg.params[0] == bot.nick and name_patt.match(msg.trailing), lambda msg, bot: bot.irc_sendmsg(bot.get_target(msg), "Well, you're the only one here..."))

    def roll_msg(self, msg, bot):
        text = bot.strip_nick(msg.trailing)[5:]
        dice = text.split("d")
        bot.irc_sendmsg(bot.get_target(msg), str(self.roll(int(dice[0]), int(dice[1]))))

    def roll(self, dice, side):
        tot = 0
        for d in range(dice):
            tot = tot + random.randint(1, side)
        return tot
    
    def roll_name_msg(self, msg, bot):
        chan = msg.params[0]
        text = bot.strip_nick(msg.trailing)[5:]
        dice = int(text.split("d")[0])
        function = bot.addfunctiontemp(lambda name_msg: name_msg.command == "353" and name_msg.params[-1] == chan, self.get_names_res(dice, bot.get_target(msg)))
        bot.send("NAMES " + chan + "\n")
    
    def random_name_msg():
        pass
    
    def get_names_res(self, dice, target):
        def get_names(msg, bot):
            # All names, response has a space at the end.
            names = msg.trailing.strip().split(" ")
            # Remove the self.
            names.remove(bot.nick)
            # Shuffle for randomness with no repetitions.
            random.shuffle(names)
            # Join on commas, but replace last comma with and. No Oxford comma I'm afraid.
            result = " and ".join(", ".join(names[:dice]).rsplit(", ", 1))
            # And return.
            bot.irc_sendmsg(target, result)
        return get_names
