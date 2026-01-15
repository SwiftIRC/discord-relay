#!/usr/bin/env python3

import functools
import irc.bot
import irc.client
import irc.connection
import re
import ssl


class IRC(irc.bot.SingleServerIRCBot):
    thread_lock = None
    running = True

    config = None
    connection = None
    discord = None
    bot = None

    def __init__(self, config):
        irc.client.ServerConnection.buffer_class.encoding = "latin-1"
        server_address = (config["SERVER"], config["PORT"])
        server_hostname = "{}:{}".format(server_address[0], server_address[1])

        wrapper = functools.partial(ssl.SSLContext().wrap_socket, server_hostname=server_hostname)
        factory = irc.connection.Factory(wrapper=wrapper, ipv6=True)
        self.bot = irc.bot.SingleServerIRCBot.__init__(self,
                                                  server_list=[server_address],
                                                  connect_factory=factory,
                                                  nickname=config["NICK"],
                                                  realname=config["NICK"] + " Relay",
                                                  )
        self.config = config

    def set_discord(self, discordd):
        self.discord = discordd

    def set_thread_lock(self, lock):
        self.thread_lock = lock

    def close(self):
        self.running = False
        self.connection.quit("Adios!")

    def privmsg(self, target, message):
        self.connection.privmsg(target, message.strip())

    def on_nicknameinuse(self, connection, event):
        connection.nick(connection.get_nickname() + "_")

    def on_welcome(self, connection, event):
        self.connection = connection

        connection.join(
            ','.join([channel for channel in self.config['CHANNELS']]))

    def on_pubmsg(self, connection, event):
        if (event.target in self.config['CHANNELS']):
            with self.thread_lock:
                message = event.arguments[0].strip()
                message = "**<{:s}>** {:s}".format(
                    re.sub(r"(]|-|\\|[`*_{}[()#+.!])", r'\\\1', event.source.nick), message)
                message = re.sub(r"\u0002|\u0003(\d\d?(,\d\d)?)?|\u001D|\u0015|\u000F", "", message)
                self.discord.privmsg(
                    self.config['CHANNELS'][event.target], message)

    def on_action(self, connection, event):
        if (event.target in self.config['CHANNELS']):
            with self.thread_lock:
                message = event.arguments[0].strip()
                message = "* {:s} {:s}".format(
                    re.sub(r"(]|-|\\|[`*_{}[()#+.!])", r'\\\1', event.source.nick), message)
                self.discord.privmsg(
                    self.config['CHANNELS'][event.target], message)

    def run(self):
        self.start()

        if self.running:
            self.running = False
            ircd = IRC({"irc": self.config})
            ircd.set_discord(self.discord)
            self.discord.set_irc(ircd)
            ircd.set_thread_lock(self.thread_lock)
            ircd.run()
