# coding=utf-8

from logging import getLogger
logger = getLogger(__name__)

import threading
import queue

class Broker (object):

    def __init__ (self, market):
        self.market = market
        self.immediate_orders = {}
        self.pending_orders = {}
        self.positions = {}

        self.status_queue = queue.Queue()
        self.command_queue = queue.Queue()

        self.broker_thread = threading.Thread(target=self.broker, daemon=True)
        self.broker_thread.start()

    @property
    def position (self):
        q = 0.0
        for pos in self.positions.values():
            q += pos['qty']
        return q

    def push_actions (self, actions):
        self.command_queue.put(('actions', actions))

    def sync (self):
        self.command_queue.put(('sync', None))
        return self.status_queue.get()

    def broker (self):
        while True:
            try:
                try:
                    cmd, args = self.command_queue.get(timeout=10)
                except queue.Empty:
                    self.update_order_status()
                else:
                    if cmd == 'actions':
                        self.process_actions(args)
                    elif cmd == 'sync':
                        self.sync_status()
                    else:
                        raise Exception(f'invalid command: {cmd}')

            except Exception as e:
                logger.exception(f'error happened in borker thread: {e}')
                raise

    def process_actions (self, actions):
        logger.debug(f'process actions: {actions}')
        for a in actions:
            action = a['action']
            if action == 'entry':
                self.process_entry(a)
            elif action == 'close':
                self.close_position(a)
            elif action == 'close_all':
                self.close_all_positions()
            else:
                raise Exception(f'invlaid action: {action}')

    def update_order_status (self, sync=False):
        while self.immediate_orders:
            orders = self.market.fetch_orders(self.immediate_orders.keys())
            for o in orders:
                status = o['status']
                if status == 'open':
                    continue
                logger.debug(f'order {status}: {o}')
                self.immediate_orders.pop(o['id'])
                # TODO limit order
            # unnecessary to wait for fulfillment of all immediate orders
            if not sync:
                break
            time.sleep(3)

    def sync_status (self):
        self.update_order_status(True)
        self.status_queue.put(self.position)

    def process_entry (self, action):
        aid = action['id']
        long_ = action['long']
        qty = action.get('qty')
        if qty is None:
            qty = 1   # FIXME
        if not long_:
            qty = -qty

        # TODO pyramiding
        cur_pos = self.positions.get(aid, None)
        if cur_pos:
            order_qty = qty - cur_pos['qty']
        else:
            # Clear all positions
            cur_qty = self.position
            order_qty = qty - cur_qty

        if order_qty:
            o = self.market.create_order(order_qty)
            # Apply position
            if o:
                self.immediate_orders[o['id']] = o
                self.positions = dict(aid=dict(order=o, qty=qty))

    def close_position (self, action):
        aid = action['id']
        pos = self.positions.get(aid, None)
        if pos:
            o = self.market.create_order(-pos['qty'], -1)
            self.immediate_orders[o['id']] = o
            self.positions.clear()

    def close_all_positions (self):
        pos = self.position
        if pos:
            o = self.market.create_order(-pos, -1)
            self.immediate_orders[o['id']] = o
            self.positions.clear()
