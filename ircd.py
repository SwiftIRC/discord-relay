#!/usr/bin/env python3

import functools
import irc.bot
import irc.client
import irc.connection
import logging
import os
import re
import ssl

from formatting import irc_to_discord

log = logging.getLogger(__name__)


def sasl_credentials(config):
    username = config.get("SASL_USERNAME")
    password = config.get("SASL_PASSWORD")
    if not username and not password:
        return None
    if not username or not password:
        raise ValueError("SASL_USERNAME and SASL_PASSWORD must both be set")
    return username, password


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

        wrapper = functools.partial(ssl.create_default_context().wrap_socket, server_hostname=config["SERVER"])
        factory = irc.connection.Factory(wrapper=wrapper, ipv6=True)

        # With sasl_login set, the library sends the server password via SASL PLAIN instead of PASS
        sasl = sasl_credentials(config)
        connect_params = {}
        password = None
        if sasl:
            connect_params["sasl_login"], password = sasl

        self.bot = irc.bot.SingleServerIRCBot.__init__(self,
                                                  server_list=[irc.bot.ServerSpec(*server_address, password)],
                                                  connect_factory=factory,
                                                  nickname=config["NICK"],
                                                  realname=config["NICK"] + " Relay",
                                                  **connect_params,
                                                  )
        self.config = config

        # Runs before irc's SASL handler (priority -42), which doesn't match UnrealIRCd's "ACK :sasl "
        self.connection.add_global_handler("cap", self._strip_cap_arguments, -50)

    @staticmethod
    def _strip_cap_arguments(connection, event):
        event.arguments[:] = [argument.strip() for argument in event.arguments]

    def set_discord(self, discordd):
        self.discord = discordd

    def set_thread_lock(self, lock):
        self.thread_lock = lock

    def close(self):
        self.running = False
        # Between a disconnect and the next reconnect attempt there's nothing to quit
        if self.connection.is_connected():
            self.connection.quit("Adios!")

    def privmsg(self, target, message):
        self.connection.privmsg(target, message.strip())

    def on_nicknameinuse(self, connection, event):
        connection.nick(connection.get_nickname() + "_")

    def on_login_failed(self, connection, event):
        # Don't run unauthenticated, and don't let the bot's reconnect loop retry bad credentials
        # irc builds this event with its arguments shifted into target, so check both
        reason = event.arguments or event.target or []
        log.error("SASL authentication failed: %s", " ".join(reason))
        self.running = False
        connection.quit("SASL authentication failed")
        os._exit(1)

    def _connect(self):
        server = self.servers.peek()
        log.info("Connecting to %s:%s", server.host, server.port)
        super()._connect()

    def on_error(self, connection, event):
        # irc puts the ERROR message in target; it carries the real reason, e.g. a ping timeout or ban
        log.warning("Server error: %s", event.target)

    def on_disconnect(self, connection, event):
        log.warning("Disconnected from %s: %s; will reconnect",
                    connection.get_server_name(), " ".join(event.arguments))

    def on_welcome(self, connection, event):
        self.connection = connection
        log.info("Connected to %s as %s", connection.get_server_name(), connection.get_nickname())

        connection.join(
            ','.join([channel for channel in self.config['CHANNELS']]))

    def on_pubmsg(self, connection, event):
        if (event.target in self.config['CHANNELS']):
            with self.thread_lock:
                message = irc_to_discord(event.arguments[0].strip())
                message = "**<{:s}>** {:s}".format(
                    re.sub(r"(]|-|\\|[`*_{}[()#+.!])", r'\\\1', event.source.nick), message)
                self.discord.privmsg(
                    self.config['CHANNELS'][event.target], message)

    def on_action(self, connection, event):
        if (event.target in self.config['CHANNELS']):
            with self.thread_lock:
                message = irc_to_discord(event.arguments[0].strip())
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
