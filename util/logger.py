# coding=utf-8

import os
import logging
import threading
import queue
import requests

class Log (object):

    def __init__ (self, name):
        self.name = name
        self.logger = logging.getLogger(name)
        self.console = logging.StreamHandler()
        self.file = None
        self.discord = None

    def enable_file (self, basename):
        os.mkdir("log")
        path = os.path.join("log", basename)
        self.file = logging.TimedRotatingFileHandler(path, when='D', backupCount=99)
        self.file.setLevel(logging.INFO)
        return self

    def enable_discord (self, url):
        self.discord_url = url
        self.discord_queue.Queue()
        self.discord_thread = threading.Thread(target=self.discord_sender, daemon=True)
        self.discord_thread.start()
        self.discord = logging.QueueHandler(self.discord_queue)
        self.discord.setLevel(logging.CRITICAL)
        self.discord.setFormatter(logging.Formatter('%(message)s'))
        return self

    def discord_sender (self):
        while True:
            msg = self.queue.get()
            data = {
                "content": msg,
                "username": self.name,
                "avatar_url": 'https://cdn.discordapp.com/icons/506478371786457099/356884415058fcc8891c20f68c5d2b47.png'
            }
            r = requests.post(self.discord_url, data=data)
            if r.status_code != 204:
                sys.stderr.write("fail to send message to Discord: {}".format(r.status_code))

logger = None
def initialize_logger (name):
    global logger
    logger = Log(name)
    return logger

def critical (msg, *args, **kwargs):
    logger.logger.critical(msg, *args, **kwargs)
def error (msg, *args, **kwargs):
    logger.logger.error(msg, *args, **kwargs)
def warning (msg, *args, **kwargs):
    logger.logger.warning(msg, *args, **kwargs)
def info (msg, *args, **kwargs):
    logger.logger.info(msg, *args, **kwargs)
def debug (msg, *args, **kwargs):
    logger.logger.debug(msg, *args, **kwargs)
