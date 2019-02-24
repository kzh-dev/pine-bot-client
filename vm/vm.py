# coding=utf-8

import time
from logging import getLogger
logger = getLogger(__name__)

from util.time import utcnowtimestamp
from util.comm import call_api, call_api2

class VMIsPurged (Exception):
    pass

class BotVM (object):

    def __init__ (self, params, ident, market):
        self.params = params
        self.ident = ident
        self.market = market
        self.jitter = 0.0
        self.ohlcv = None

    @property
    def current_clock (self):
        return self.ohlcv['t'][-1]
    @property
    def next_clock (self):
        return self.ohlcv['t'][-1] + self.market.resolution * 60

    def update_jitter (self, server_clock):
        local_clock = utcnowtimestamp()
        self.jitter = local_clock - server_clock
        return self.jitter

    def now (self):
        return int(utcnowtimestamp() + self.jitter)

    def boot (self):
        self.ohlcv = self.market.load_ohlcv(self.now())
        res = call_api(self.params, '/boot-vm',
                        vmid=self.ident, ohlcv=self.ohlcv)
        error = res.get('error', None)
        if error:
            raise Exception(f'fail to boot VM: {error}')
        self.update_jitter(res['server_clock'])

    def run_forever (self):
        while True:
            # Try to step VM by 1tick
            try:
                self.wait_till_next()
                logger.debug(f'wakeup! {self.current_clock}')

                actions = self.trystep()
                for a in actions:
                    logger.info(a)

                #  if actions:
                #     applyr(actions)
            except VMIsPurged:
                logger.warning(f'vm was purged: {self.ident}')
                raise
            except Exception as e:
                logger.error(f"fail to trystep: {e}"))
                time.sleep(3)
            
    def wait_till_next (self):
        next_clock = self.next_clock
        while True:
            # Sleep
            interval = self.next_clock - self.current_clock
            now = self.now()
            if now < self.next_clock:
                to_sleep = interval - now % interval
                logger.debug(f'sleep={to_sleep} now={now} interval={interval}')
                time.sleep(to_sleep)

            # Fetch & update candle
            for i in range(3):
                ohlcv = self.market.fetch_ohlcv(self.current_clock)
                self.update_ohlcv(ohlcv)
                # Return having new
                if self.current_clock >= next_clock:
                    break
                time.sleep(5)
            if self.current_clock >= next_clock:
                break

    def update_ohlcv (self, ohlcv):
        ts0 = ohlcv['t'][0]
        if ts0 != self.current_clock:
            raise Exception(f'clock out-of-sync: {ts0} for {self.current_clock}')
        # update current clock
        for k in ohlcv.keys():
            self.ohlcv[k][-1] = ohlcv[k][0]
        if len(ohlcv['t']) < 2:
            return
        # have new one
        for k in ohlcv.keys():
            self.ohlcv[k].pop(0)
            self.ohlcv[k][-2] = ohlcv[k][0]
            self.ohlcv[k][-1] = ohlcv[k][1]

    @property
    def latest_ohlcv2 (self):
        return dict(
            t=self.ohlcv['t'][-2:],
            o=self.ohlcv['o'][-2:],
            h=self.ohlcv['h'][-2:],
            l=self.ohlcv['l'][-2:],
            c=self.ohlcv['c'][-2:],
            v=self.ohlcv['v'][-2:],
        )

    def trystep (self):
        logger.debug(f'start_trystep: {self.current_clock}')

        broker = dict(position_size=0)
        status, obj = call_api2(self.params, '/step-vm', vmid=self.ident, broker=broker,
                                ohlcv2=self.latest_ohlcv2)
        if status == 205:   # reset
            raise VMIsPurged()

        # status 200
        self.update_jitter(obj['server_clock'])
        return 'action', obj['actions']
