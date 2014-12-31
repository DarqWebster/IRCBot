import irc
import config

bot = irc.Bot(config.serv, config.port, config.nick, config.chans, config.plugins)
bot.run()
