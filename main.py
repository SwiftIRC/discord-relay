#!/usr/bin/env python3

from ircd import *
from discordd import *
from dotenv import load_dotenv
import json
import threading
import os

load_dotenv()

config = {
    'TOKEN': os.getenv('TOKEN'),
    'NICK': os.getenv('NICK'),
    'SERVER': os.getenv('SERVER'),
    'PORT': int(os.getenv('PORT')),
    'CHANNELS': json.loads(os.getenv('CHANNELS'))
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
