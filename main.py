#!/usr/bin/env python3

from ircd import *
from discordd import *
from dotenv import load_dotenv
import json
import threading
import os

load_dotenv()

channels = {
    '#rshelp': 306269746280529920,
    '#bullshit': 328270978524381184,
    '#minecraft': 576528017661231124,
    '#Games': 882666320406138920,
    '#programming': 882384979609403402,
    '#swiftirc': 875742213978595378,
    '#cooking': 882385109343416340
    # '#asdfghj': 306269746280529920
}

config = {
    'TOKEN': os.getenv('TOKEN'),
    'NICK': os.getenv('NICK'),
    'SERVER': os.getenv('SERVER'),
    'PORT': int(os.getenv('PORT')),
    'CHANNELS': channels
}

thread_lock = threading.Lock()

irc = IRC(config)
discord = Discord(config)

irc.set_discord(discord)
discord.set_irc(irc)

irc.set_thread_lock(thread_lock)
discord.set_thread_lock(thread_lock)

thread = threading.Thread(target=irc.run)
thread.daemon = True
thread.start()

discord.run()  # Keep everything running
irc.close()
