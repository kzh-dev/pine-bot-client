# coding=utf-8

import time
from datetime import datetime, timezone
from util.logger import info, debug, report2, report3, error, warning
from util.comm import call_api2

class BotVM (object):

    def __init__ (self, params, **kws):
        self.params = params
        self.ident = kws['vm']
        self.clock = kws['clock']
        self.next_clock = kws['next_clock']
        self.update_jitter(kws['server_clock'])

    def update_jitter (self, server_clock):
        local_clock = datetime.now(timezone.utc).timestamp()
        self.jitter = local_clock - server_clock
        self.local_next_clock = self.next_clock + self.jitter
        

    def run_forever (self):
        while True:
            ready = self.sleep()
            if not ready:
                # update current position, orders
                continue

            report2('ready!')

            # Try to step VM by 1tick
            try:
                r, actions = self.trystep()
                if r == 'wait':
                    continue
                if r == 'reset':
                    raise NotImplementedError

                #
                for a in actions:
                    warning(a)
                #  step(status, next_clock)
                #  if wait
                #     continue
                #  if missing
                #     reinit VM
                #     continue
                #
                #  if actions:
                #     applyr(actions)
            except Exception as e:
                error("fail to trystep: {}".format(e))
                time.sleep(3)
            
    def sleep (self):
        margin = 1 # sec
        now = datetime.now(timezone.utc).timestamp()
        remain = self.local_next_clock - margin - now
        if remain <= 0:
            time.sleep(1)
            return True
        interval = 10
        period = min((interval, remain))
        report2('sleep: %.1f, reamin=%.1f', period, remain)
        time.sleep(period)
        return remain < interval

    def trystep (self):
        broker = dict(position_size=0)
        report2('trystep: next_clock=%s', self.next_clock)
        status, obj = call_api2(self.params, '/step-vm', 
                                    vm=self.ident, next_clock=self.next_clock, broker=broker)
        report2('status=%s, obj=%s', status, obj)

        if status == 206:   # try again
            report2("try again: next={}, sever:={}".format(self.next_clock, obj['server_clock']))
            self.update_jitter(obj['server_clock'])
            return 'wait', None
        if status == 205:   # reset
            return 'reset', None

        # status 200
        self.next_clock = obj['next_clock']
        self.update_jitter(obj['server_clock'])
        return 'action', obj['actions']
