# coding=utf-8

import time
from logging import getLogger
logger = getLogger(__name__)

from util.time import utcnowtimestamp
from util.comm import call_api, call_api2

from bot.broker import Broker

class VMIsPurged (Exception):
    pass

class BotVM (object):

    def __init__ (self, params, ident, market):
        self.params = params
        self.ident = ident
        self.market = market
        self.jitter = 0.0
        self.worst_jitter = 0.0
        self.ohlcv = None
        self.broker = Broker(market, params['strategy'])
        self.position = 0.0

        self.hb_interval_base = 300
        self.hb_interval_variance = 0.2
        bot_params = params.get('bot', None)
        if bot_params:
            self.hb_interval_base = bot_params.get('hb_interval', self.hb_interval_base)
            self.hb_interval_variance = bot_params.get('hb_interval_variance', self.hb_interval_variance)
        self.initialize_hb_range()

    def initialize_hb_range (self):
        delta = int(self.hb_interval_base * 0.2)
        minimum = self.hb_interval_base - delta
        maximum = self.hb_interval_base + delta + 1
        self.hb_interval_range = (minimum, maximum)

    @property
    def current_clock (self):
        return self.ohlcv['t'][-1]
    @property
    def next_clock (self):
        return self.ohlcv['t'][-1] + self.market.resolution * 60

    CLOCK_JITTER_THRESHOLD = 3.0
    def update_jitter (self, server_clock):
        local_clock = utcnowtimestamp()
        self.jitter = local_clock - server_clock
        # NOTICE
        if self.worst_jitter == 0.0:
            if self.jitter > self.CLOCK_JITTER_THRESHOLD:
                logger.warning('clock jitter = %.3f', self.jitter)
            else:
                logger.info('clock jitter = %.3f', self.jitter)
            self.worst_jitter = self.jitter
        if self.jitter > self.CLOCK_JITTER_THRESHOLD and self.jitter > self.worst_jitter:
            self.worst_jitter = self.jitter
            logger.warning(f'worst clock jitter = {self.jitter}')
            
        return self.jitter

    def now (self):
        return int(utcnowtimestamp() + self.jitter)

    def call_api (self, path, **kws):
        status, res = call_api2(self.params, path, **kws)
        if status == 205:
            raise VMIsPurged()
        self.update_jitter(res['server_clock'])
        return res

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
                if actions:
                    self.apply_actions(actions)

            except VMIsPurged:
                logger.warning(f'vm was purged: {self.ident}')
                raise
            except Exception as e:
                logger.error(f"fail to trystep: {e}")
                time.sleep(3)

    def sleep_randomly (self, now):
        import random
        interval = self.next_clock - self.current_clock
        actual_sleep = to_sleep = interval - now % interval
        if actual_sleep > self.hb_interval_base:
            actual_sleep = random.randrange(*self.hb_interval_range) # ~5min
        logger.debug(f'sleep={actual_sleep}/{to_sleep} now={now} interval={interval}')
        time.sleep(actual_sleep)
        return to_sleep == actual_sleep

    def sleep_with_hb (self, next_clock):
        while True:
            now = self.now()
            if now >= next_clock - 1:
                break
            if not self.sleep_randomly(now):
                # HB
                self.call_api('/touch-vm', vmid=self.ident)

    def fetch_ohlcv (self, next_clock):
        delay = 1.0
        ratio = 1.5
        for i in range(5):
            ohlcv = self.market.fetch_ohlcv(self.current_clock)
            self.update_ohlcv(ohlcv)
            # Return having new
            if self.current_clock >= next_clock:
                return True
            time.sleep(delay)
            delay *= ratio
        # 
        logger.warning(f'long delay in fetching OHLCV data')
        time.sleep(60)
        return False
            
    def wait_till_next (self):
        next_clock = self.next_clock
        now = int(self.now())
        while True:
            # Sleep
            self.sleep_with_hb(next_clock)

            # Fetch & update candle
            if self.fetch_ohlcv(self.next_clock):
                break

        # Get broker's status
        self.position = self.broker.sync()

    def apply_actions (self, actions):
        logger.debug(f'apply actions {actions}')
        self.broker.push_actions(actions)

    def sync_broker (self):
        return self.broker.sync()

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
            self.ohlcv[k][-1] = ohlcv[k][0]
            self.ohlcv[k].append(ohlcv[k][1])

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
        obj = self.call_api('/step-vm', vmid=self.ident, broker=broker,
                                ohlcv2=self.latest_ohlcv2, position=self.position)
        return obj['actions']
