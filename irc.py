import logging
import importlib
import socket
import collections
import re

def msgparse(rawmsg):
    IRCMsg = collections.namedtuple("IRCMsg", ["raw", "prefix", "command", "params", "trailing", "extra"])
    
    msgsplit = rawmsg.split(" :", 1) + [""] # Split into protocol information and trailing ("" if no trailing)
    msgparts = msgsplit[0].split(" ") # Split protocol information into [":" + prefix], command, [params*]
    trailing = msgsplit[1]
    
    prefix = ""
    command = ""
    params = []
    
    commandIndex = 0;
    if (msgparts[0].startswith(":")):
        # Prefix exists.
        prefix = msgparts[0][1:]
        commandIndex = 1
    command = msgparts[commandIndex]
    params = msgparts[commandIndex + 1:]
    
    return IRCMsg(rawmsg, prefix, command, params, trailing, dict())

class Bot:
    errmsg_invalidfunction = "Hmmm?"
    IRCMsgPred = collections.namedtuple("IRCMsgFunc", ["pred", "func"])
    
    def __init__(self, serv, port, nick, chans, plugins):
        self.serv = serv
        self.port = port
        self.nick = nick
        self.chans = chans
        self.plugins = plugins
        self.functiontemps = []
        self.functions = []
        self.cont = 0;
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        self.definefunctions()
        self.loadplugins()
        self.connectserv()
        self.cont = 1;
        self.loop(self.waitforwelcome)
        self.joinchans()
        self.cont = 1;
        self.loop(self.line)
    
    # Raw send function.
    def send(self, msg):
        logging.debug("Send: " + msg)
        self.sock.send(msg.encode("UTF-8"))
    
    # IRC functions.
    def irc_pong(self, trailing):
        self.send("PONG :" + trailing + "\n")

    def irc_sendmsg(self, target, msg):
        self.send("PRIVMSG " + target + " :" + msg + "\n")

    def irc_joinchan(self, chan):
        self.send("JOIN " + chan + "\n")

    def irc_quitserv(self, msg):
        self.send("QUIT :" + msg + "\n")
    
    #CTCP function.
    def ctcp_version(self, msg):
        self.send("VERSION DarqBot 0.0.0 Snapshot.")
    
    # Message parsing functions.
    def is_to_me(self, msg):
        return msg.command == "PRIVMSG" and (msg.params[0] == self.nick or msg.trailing.startswith(self.nick))
    
    def is_private(self, msg):
        return msg.command == "PRIVMSG" and (msg.params[0] == self.nick)
    
    def get_target(self, msg):
        if msg.params[0] and msg.params[0] == self.nick:
            # PM.
            return msg.prefix.split("!", 1)[0]
        else:
            # Channel message.
            return msg.params[0]
    
    def strip_nick(self, text):
        if text.startswith(self.nick):
            work = text[len(self.nick):]
            while not work[0].isalnum():
                work = work[1:]
            return work
        return text
    
    def get_source_nick(self, msg):
        return msg.prefix.split("!", 1)[0]

    # Bot functions.
    def say(self, msg, bot):
        logging.debug("Func: say.")
        text = self.strip_nick(msg.trailing)[4:]
        self.irc_sendmsg(self.get_target(msg), text)
    
    def cmd(self, msg, bot):
        logging.debug("Func: cmd.")
        text = self.strip_nick(msg.trailing)[4:]
        self.send(text + "\n")
    
    def joinchan(self, msg, bot):
        logging.debug("Func: joinchan.")
        text = self.strip_nick(msg.trailing)[5:]
        self.irc_joinchan(text)

    def quitserv(self, msg, bot):
        logging.debug("Func: quitserv.")
        text = self.strip_nick(msg.trailing)[5:]
        self.irc_quitserv(text)
        self.cont = 0;
    
    def nofunc(self, msg, bot):
        logging.debug("Func: nofunc.")
        self.irc_sendmsg(self.get_target(msg), Bot.errmsg_invalidfunction)

    # Lifecycle functions.
    def addfunctiontemp(self, pred, func):
         self.functiontemps.append(Bot.IRCMsgPred(pred, func))
    
    def addfunction(self, pred, func):
        self.functions.append(Bot.IRCMsgPred(pred, func))
    
    def definefunctions(self):
        say_patt = re.compile("^say .*$")
        self.addfunction(lambda msg: self.is_to_me(msg) and say_patt.match(self.strip_nick(msg.trailing)), self.say)
        # Admin or debug functions.
        # cmd_patt = re.compile("^cmd .*$")
        # self.addfunction(lambda msg: self.is_to_me(msg) and cmd_patt.match(self.strip_nick(msg.trailing)), self.cmd)
        # join_patt = re.compile("^join #.*$")
        # self.addfunction(lambda msg: self.is_to_me(msg) and join_patt.match(msg.trailing), self.joinchan)
        # quit_patt = re.compile("^quit( .*)?$")
        # self.addfunction(lambda msg: self.is_to_me(msg) and quit_patt.match(msg.trailing), self.quitserv)
    
    def loadplugins(self):
        for plugin in self.plugins:
            mod_name, cls_name = plugin.split(".")
            plugin = importlib.import_module("plugin." + mod_name)
            instance = getattr(plugin, cls_name)(self)
    
    def connectserv(self):
        self.sock.connect((self.serv, self.port))
        self.send("USER " + self.nick + " " + self.nick + " " + self.nick + " " + self.nick + "\n")
        self.send("NICK " + self.nick + "\n")
    
    def joinchans(self):
        for chan in self.chans:
            self.irc_joinchan(chan)
    
    def loop(self, func):
        buffer = "";
        while self.cont:
            raw = buffer + self.sock.recv(2048).decode()
            rawmsgs = raw.split("\r\n")
            for rawmsg in rawmsgs[:-1]:
                msg = msgparse(rawmsg)
                logging.debug("Recv: " + str(msg))
                func(msg)
            buffer = rawmsgs[-1]

    def waitforwelcome(self, msg) :
        if msg.command == "PING":
            self.irc_pong(msg.trailing)
            return
        
        if msg.command == "001":
            self.cont = 0;
            return

    def line(self, msg):
        if msg.command == "PING":
            self.irc_pong(msg.trailing)
            return
        
        # Temporary functions.
        i = 0
        n = len(self.functiontemps)
        while i < n:
            if self.functiontemps[i].pred(msg):
                self.functiontemps[i].func(msg, self)
                del self.functiontemps[i]
                return
        
        # Permanent functions.
        for msgfunc in self.functions:
            if msgfunc.pred(msg):
                msgfunc.func(msg, self)
                return
