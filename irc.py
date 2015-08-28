import logging
import importlib
import socket
import collections

def msgparse(rawmsg):
    IRCMsg = collections.namedtuple("IRCMsg", ["prefix", "command", "params", "trailing"])
    
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
    
    return IRCMsg(prefix, command, params, trailing)

class Bot:
    errmsg_invalidfunction = "Hmmm?"
    
    def __init__(self, serv, port, nick, chans, plugins):
        self.serv = serv
        self.port = port
        self.nick = nick
        self.chans = chans
        self.plugins = plugins
        self.functions = {}
        self.cont = 0;
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        self.cont = 1;
        self.definefunctions()
        self.connecttoirc();
        self.join()
        self.loop();
    
    def send(self, msg):
    	logging.debug("Send: " + msg)
    	self.sock.send(msg.encode("UTF-8"))

    # IRC functions.
    def irc_ping(self, trailing):
        self.send("PONG :" + trailing + "\n")

    def irc_sendmsg(self, target, msg):
        self.send("PRIVMSG " + target + " :" + msg + "\n")

    def irc_joinchan(self, chan):
        self.send("JOIN " + chan + "\n")

    def irc_quitserv(self, msg):
        self.send("QUIT :" + msg + "\n")

    # Bot functions.
    def echo(self, msg):
        return msg
    
    def joinchan(self, msg):
        self.irc_joinchan(msg)

    def quitserv(self, msg):
        self.irc_quitserv(msg)
        self.cont = 0;
    
    #CTCP functions.
    def ctcp_version(self, msg):
        self.send("VERSION DarqBot 0.0.0 Snapshot.")

    # Operational functions.
    def definefunctions(self):
        self.functions = {, "echo":self.echo, "join":self.irc_joinchan, "quit":self.quitserv}
        for plugin in self.plugins:
            plugin = importlib.import_module("plugin." + plugin)
            instance = plugin.getinstance()
            self.functions.update(instance.functions)
    
    def connecttoirc(self):
        self.sock.connect((self.serv, self.port))
        self.send("USER " + self.nick + " " + self.nick + " " + self.nick + " " + self.nick + "\n")
        self.send("NICK " + self.nick + "\n")

    def join(self):
        for chan in self.chans:
            self.irc_joinchan(chan)

    def loop(self):
        buffer = "";
        while self.cont:
            raw = buffer + self.sock.recv(2048).decode()
            rawmsgs = raw.split("\r\n")
            for rawmsg in rawmsgs[:-1]:
                self.line(msgparse(rawmsg))
            buffer = rawmsgs[-1]

    def line(self, msg):
        logging.debug("Recv: " + str(msg))
        
        if msg.command == "PING":
            self.irc_ping(msg.trailing)
            return

        if msg.command == "PRIVMSG":
            target = None
            trailing = msg.trailing
            if msg.params[0] and msg.params[0] == self.nick:
                # PM.
                target = msg.prefix.split("!", 1)[0]
            elif msg.trailing and trailing.startswith(self.nick + ": "):
                # Channel message.
                target = msg.params[0]
                trailing = trailing[len(self.nick + ", "):]

            if target:
                funcpara = trailing.split(" ", 1) + [""]
                print("FUNCTION: " + funcpara[0] + ", " + funcpara[1])
                if funcpara[0] in self.functions:
                    function = self.functions[funcpara[0]]
                    result = function(funcpara[1])
                    if (result):
                        self.irc_sendmsg(target, result)
                else:
                    self.irc_sendmsg(target, Bot.errmsg_invalidfunction)

