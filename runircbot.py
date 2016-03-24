import logging
import irc
import config

logging.basicConfig(level=logging.DEBUG)
bot = irc.Bot(config.serv, config.port, config.nick, config.chans, config.plugins)
bot.run()
