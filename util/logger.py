# coding=utf-8

import os
import logging
import logging.handlers
import threading
import queue
import requests

PINE_IMG_URL = 'https://cdn.discordapp.com/icons/506478371786457099/356884415058fcc8891c20f68c5d2b47.png'

class Logger (object):

    def __init__ (self, name):
        self.name = name
        self.logger = logging.getLogger(name)
        self.console = logging.StreamHandler()
        self.console.setFormatter(logging.Formatter('%(asctime)s: %(levelname)s: %(message)s'))
        self.file = None
        self.discord = None
        self.logger.addHandler(self.console)
        self.logger.setLevel(logging.INFO)

    def verbose (self, discord=True):
        self.console.setLevel(logging.INFO)
        if discord and self.discord:
            self.console.setLevel(logging.INFO)
    def quiet (self, discord=True):
        self.console.setLevel(logging.WARNING)
        if discord and self.discord:
            self.console.setLevel(logging.CRITICAL)

    def enable_file (self, basename):
        try:
            os.mkdir("log")
        except FileExistsError:
            pass
        path = os.path.join("log", os.path.basename(basename))
        self.file = logging.handlers.TimedRotatingFileHandler(path, when='D', backupCount=99)
        self.file.setFormatter(logging.Formatter('%(asctime)s: %(levelname)s: %(message)s'))
        self.logger.addHandler(self.file)
        return self

    def enable_discord (self, url):
        self.discord_url = url
        self.discord_queue.Queue()
        self.discord_thread = threading.Thread(target=self.discord_sender, daemon=True)
        self.discord_thread.start()
        self.discord = logging.handlers.QueueHandler(self.discord_queue)
        self.discord.setLevel(logging.CRITICAL)
        self.logger.addHandler(self.discord)
        return self

    def discord_sender (self):
        while True:
            msg = self.queue.get()
            data = {
                "content": msg,
                "username": self.name,
                "avatar_url": PINE_IMG_URL,
            }
            r = requests.post(self.discord_url, data=data)
            if r.status_code != 204:
                sys.stderr.write("fail to send message to Discord: {}".format(r.status_code))

logger = None
def initialize_logger (name):
    global logger
    logger = Logger(name)
    return logger

def critical (msg, *args, **kwargs):
    logger.logger.critical(msg, *args, **kwargs)
def error (msg, *args, **kwargs):
    logger.logger.error(msg, *args, **kwargs)
def exception (msg, *args, **kwargs):
    logger.logger.exception(msg, *args, **kwargs)
def warning (msg, *args, **kwargs):
    logger.logger.warning(msg, *args, **kwargs)
def info (msg, *args, **kwargs):
    logger.logger.info(msg, *args, **kwargs)
def debug (msg, *args, **kwargs):
    logger.logger.debug(msg, *args, **kwargs)
def report (msg, *args, **kwargs):
    try:
        logger.verbose(True)
        logger.logger.info(msg, *args, **kwargs)
    finally:
        logger.quiet(True)
def report2 (msg, *args, **kwargs):
    try:
        logger.verbose(False)
        logger.logger.info(msg, *args, **kwargs)
    finally:
        logger.quiet(False)
def report3 (msg, *args, **kwargs):
    try:
        logger.file.setLevel(logging.WARN)
        report2(msg, *args, **kwargs)
    finally:
        logger.file.setLevel(logging.INFO)
