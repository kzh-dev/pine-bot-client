# coding=utf-8

from datetime import datetime, timezone

def utcnowtimestamp ():
    return datetime.now(timezone.utc).timestamp()
    
