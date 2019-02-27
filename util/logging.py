# coding=utf-8

import logging
import logging.handlers

logger = logging.getLogger(__name__)

# Helpers
console_handler = logging.StreamHandler()

# Formatters
shortest_formatter = logging.Formatter('%(message)s')
short_formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s')
long_formatter = logging.Formatter('%(asctime)s: %(name)s: %(levelname)s: %(message)s')

# Handlers
console_handler = logging.StreamHandler()
console_handler.setFormatter(short_formatter)
console_handler.setLevel(logging.INFO)

file_handler = None
def make_file_handler (filename):
    global file_handler
    file_handler = logging.handlers.TimedRotatingFileHandler(filename,
                                                            when='D', backupCount=99, delay=True)
    file_handler.setFormatter(long_formatter)
    file_handler.setLevel(logging.DEBUG)
    return file_handler

import threading
import queue
discord_thread = None
discord_queue = queue.Queue()
discord_handler = logging.handlers.QueueHandler(discord_queue)
discord_handler.setFormatter(shortest_formatter)
discord_handler.setLevel(logging.CRITICAL)
DEFAULT_DISCORD_NAME = 'PINE Bot'
DEFAULT_DISCORD_AVATAR_URL = 'https://cdn.discordapp.com/icons/506478371786457099/356884415058fcc8891c20f68c5d2b47.png'
discord_conf = dict(
    url='',
    name=DEFAULT_DISCORD_NAME,
    avatar_url=DEFAULT_DISCORD_AVATAR_URL,
)
import requests
def discord_sender ():
    while True:
        msg = discord_queue.get()
        if msg is None:
            break
        if msg.startswith('fail to send to Disocrd'):
            continue
        data = {
            "content": msg,
            "username": discord_conf['name'] or DEFAULT_DISCORD_NAME,
            "avatar_url": discord_conf['avatar_url'] or DEFAULT_DISCORD_AVATAR_URL,
        }
        try:
            r = requests.post(discord_conf['url'], data=data)
            if r.status_code != 204:
                logger.error(f'fail to send to Discord: {r.status_code}')
        except Exception as e:
            logger.error(f'fail to send to Discord: {e}')

## App logger
app_logger = logging.getLogger()
app_logger.addHandler(console_handler)
app_logger.setLevel(logging.DEBUG)

# load logging conf
import os
if os.path.exists('./logging.conf'):
    from logging import config
    config.fileConfig('./logging.conf', disable_existing_loggers=False)

# utilities
import os.path
def enable_logfile (pine_fname, params={}):
    dir_name = 'log'
    try:
        os.mkdir(dir_name)
    except FileExistsError:
        pass
    except Exception as e:
        logger.error(f'fail to make log directory: {e}') 
        raise e
    path = os.path.join(dir_name, os.path.basename(pine_fname+'.log'))
    app_logger.addHandler(make_file_handler(path))

from util.dict_merge import dict_merge
import threading
def enable_discord (params={}):
    global discord_thread
    conf = params.get('discord', None)
    if conf:
        dict_merge(discord_conf, conf)
    if discord_conf['url']:
        app_logger.addHandler(discord_handler)
        discord_thread = threading.Thread(target=discord_sender, daemon=True)
        discord_thread.start()

## Report incl. discord
def notify (logger, msg):
    logger.info(msg)
    if discord_thread:
        discord_queue.put(msg)

def notify_order (logger, msg):
    logger.info(msg)
    if discord_thread and discord_conf.get('order', None) is not False:
        discord_queue.put(msg)
