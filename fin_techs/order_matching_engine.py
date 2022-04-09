import json
import logging
from copy import deepcopy
from datetime import datetime, timedelta
from ezcode.heap import PriorityMap
from prettytable import PrettyTable
from threading import current_thread, Lock
from time import sleep
from typing import List


logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
logger.addHandler(logging.StreamHandler())


class Order:
    def __init__(self, order_id: int, symbol: str, side: str, price: float, volume: int, account: str, expire_sec: int):
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.price = price
        self.volume = volume
        self.account = account
        self.time = datetime.now()
        self.expire_sec = expire_sec

    def __str__(self):
        return "{" + f"\"order_id\": {self.order_id}, \"symbol\": \"{self.symbol}\", \"side\": \"{self.side}\", \"price\": {self.price}, " +\
                     f"\"volume\": {self.volume}, \"account\": \"{self.account}\", \"time\": \"{self.time}\", \"expire_sec\": {self.expire_sec}" + "}"

    def check_type(self, other):
        if not isinstance(other, type(self)): 
            raise NotImplementedError(f"{other} is not type {type(self)}")

    def __gt__(self, other):
        self.check_type(other)
        # return other < self
        if self.price > other.price:
            return True
        if other.price > self.price:
            return False
        if self.time < other.time:    # Max Heap should always put earlier order on top
            return True
        if other.time < self.time:    # Max Heap should always put earlier order on top
            return False
        return self.volume > other.volume

    def __lt__(self, other):
        self.check_type(other)
        if self.price < other.price:
            return True
        if other.price < self.price:
            return False
        if self.time < other.time:
            return True
        if other.time < self.time:
            return False
        return self.volume < other.volume

    def time_left(self) -> str:
        tl = self.time + timedelta(seconds=self.expire_sec) - datetime.now() if self.is_valid() else timedelta(seconds=0)
        return str(tl).split(".")[0]  # remove microseconds

    def is_valid(self) -> bool:
        return self.time + timedelta(seconds=self.expire_sec) >= datetime.now()


class MatchingEngine:
    def __init__(self, logger=logger):
        self.logger = logger
        self.history = list()
        self.queues = dict()  # {symbol: {ask: min_q, bid: max_q}}
        self.locks = dict()   # {symbol: {ask: lock, bid: lock}}
        self.db = dict()      # mimic the order database {order_id: order}

    def load_symbols(self, symbols: List[str]):
        for symbol in symbols:
            if symbol not in self.queues:
                self.queues[symbol] = dict()
                self.locks[symbol] = dict()
            self.queues[symbol]["ask"] = PriorityMap(min_heap=True)
            self.queues[symbol]["bid"] = PriorityMap(min_heap=False)
            self.locks[symbol]["ask"] = Lock()
            self.locks[symbol]["bid"] = Lock()

    def view_history(self):
        history_str = ""
        for match_result in self.history:
            history_str += json.dumps(match_result, indent=4) + "\n"
        return history_str if history_str else "No Transaction Found!\n"

    def _match(self, order, queue):
        while len(queue) > 0:
            q_top_order, _ = queue.peek()
            if not q_top_order.is_valid():
                queue.pop()
                self.logger.info(f"Order Expired: {q_top_order}")
            else:
                if (order.side == "ask" and order.price <= q_top_order.price) or (order.side == "bid" and order.price >= q_top_order.price):
                    queue.pop()
                    order_copy, q_top_order_copy = deepcopy(order), deepcopy(q_top_order)
                    volume_filled = min(order.volume, q_top_order.volume)
                    order.volume -= volume_filled
                    q_top_order.volume -= volume_filled
                    if q_top_order.volume > 0:
                        queue.push(q_top_order, q_top_order.order_id)  # push back residual volume
                    match_result = {
                        "accepted_order": json.loads(str(order_copy)),
                        "matched_order": json.loads(str(q_top_order_copy)),
                        "volume_filled": volume_filled,
                        "final_price": q_top_order.price,
                        "price_gap": abs(order.price - q_top_order.price),
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                    }
                    self.history.append(match_result)
                    self.logger.info(f"Matched Orders: {match_result}")
                    if order.volume == 0:
                        return
                else:
                    return

    def accept_order(self, order: Order):
        self.logger.info(f"[{current_thread().name} {current_thread().native_id}] Accepted Order: {order}")
        self.db[order.order_id] = order  # persist the order
        other_side = "ask" if order.side == "bid" else "bid"
        self.locks[order.symbol][other_side].acquire()
        self._match(order, self.queues[order.symbol][other_side])
        self.locks[order.symbol][other_side].release()
        if order.volume > 0:
            self.locks[order.symbol][order.side].acquire()
            self.queues[order.symbol][order.side].push(order, order.order_id)
            self.locks[order.symbol][order.side].release()

    def cancel_order(self, order_id: int):
        if order_id not in self.db:
            raise ValueError(f"Order ID \"{order_id}\" not found in db")
        order = self.db[order_id]
        self.logger.info(f"[{current_thread().name} {current_thread().native_id}] Cancelled Order: {order}")
        self.locks[order.symbol][order.side].acquire()
        self.queues[order.symbol][order.side].delete(order_id)
        self.locks[order.symbol][order.side].release()
        del self.db[order_id]
        return order

    def view_orders(self, symbol, include_expired: bool = False, size: int = None) -> str:
        ask_view = self.queues[symbol]["ask"].top_n(size)
        bid_view = self.queues[symbol]["bid"].top_n(size)
        table = PrettyTable(["Symbol", "Type", "Price", "Volume", "Order ID", "Created", "Time Left"])
        for order, _ in ask_view[::-1]:
            if not include_expired and not order.is_valid():
                continue
            table.add_row([order.symbol, order.side, order.price, order.volume, order.order_id, order.time.strftime("%Y-%m-%d %H:%M:%S"), order.time_left()])
        table.add_row(["-"] * len(table.field_names))
        for order, _ in bid_view:
            if not include_expired and not order.is_valid():
                continue
            table.add_row([order.symbol, order.side, order.price, order.volume, order.order_id, order.time.strftime("%Y-%m-%d %H:%M:%S"), order.time_left()])
        return table.get_string() + "\n"


# Web Service
import argparse
import os
from flask import Flask, Response, request
from logging.config import dictConfig

dictConfig({
    'version': 1,
    'formatters': {'default': {'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',}},
    'handlers': {'wsgi': {'class': 'logging.StreamHandler', 'stream': 'ext://flask.logging.wsgi_errors_stream', 'formatter': 'default'}},
    'root': {'level': 'INFO', 'handlers': ['wsgi']}
})

web = Flask(__name__)
engine = MatchingEngine(logger=web.logger)


@web.route("/order", methods=["GET", "POST", "DELETE"])
def order():
    if request.method == "GET":
        symbol = request.args.get("symbol")
        size = int(request.args.get("size")) if "size" in request.args else None
        include_expired = True if "include_expired" in request.args else False
        view = engine.view_orders(symbol, include_expired, size)
        return Response(response=view, content_type='text/plain; chatset=utf-8', status=200)
    elif request.method == "POST":
        data = request.get_json()
        order = Order(int(data["order_id"]), data["symbol"], data["side"], data["price"], data["volume"], data["account"], data["expire_sec"])
        engine.accept_order(order)
        return Response(response=f"Posted order: {order}\n", content_type='text/plain; chatset=utf-8', status=200)
    elif request.method == "DELETE":
        order_id = int(request.args.get("order_id"))
        order = engine.cancel_order(order_id)
        return Response(response=f"Cancelled order: {order}\n", content_type='text/plain; chatset=utf-8', status=200)


@web.route("/history", methods=["GET"])
def history():
    return Response(response=engine.view_history(), content_type='text/plain; chatset=utf-8', status=200)


PARSER = argparse.ArgumentParser(description="Web host and port")
PARSER.add_argument("-H", "--host", dest="host", default="localhost", help="Host or IP")
PARSER.add_argument("-p", "--port", dest="port", default=9999, help="Port")
PARSER.add_argument("-s", "--symbols", dest="symbols", default="AAPL,MSFT", help="Trading Symbols, delimiter = ','")
ARGUMENTS = PARSER.parse_args()
if __name__ == "__main__":
    engine.load_symbols(ARGUMENTS.symbols.split(","))
    web.run(host=ARGUMENTS.host, port=ARGUMENTS.port, threaded=True, debug=True)


"""
orders=(
    '{"order_id":"1","symbol":"MSFT","side":"ask","price":200,"volume":3,"account":"Trader_A","expire_sec":20}'
    '{"order_id":"2","symbol":"MSFT","side":"ask","price":180,"volume":5,"account":"Trader_B","expire_sec":20}'
    '{"order_id":"3","symbol":"MSFT","side":"ask","price":170,"volume":2,"account":"Trader_B","expire_sec":1}'
    '{"order_id":"4","symbol":"AAPL","side":"ask","price":200,"volume":3,"account":"Trader_A","expire_sec":20}'
    '{"order_id":"5","symbol":"MSFT","side":"bid","price":170,"volume":4,"account":"Trader_C","expire_sec":20}'
    '{"order_id":"6","symbol":"MSFT","side":"bid","price":150,"volume":1,"account":"Trader_D","expire_sec":20}'
    '{"order_id":"7","symbol":"MSFT","side":"ask","price":170,"volume":3,"account":"Trader_A","expire_sec":20}'
    '{"order_id":"8","symbol":"MSFT","side":"bid","price":160,"volume":2,"account":"Trader_E","expire_sec":20}'
    '{"order_id":"9","symbol":"MSFT","side":"ask","price":190,"volume":4,"account":"Trader_F","expire_sec":20}'
    '{"order_id":"10","symbol":"MSFT","side":"bid","price":185,"volume":5,"account":"Trader_G","expire_sec":20}'
    '{"order_id":"11","symbol":"AAPL","side":"bid","price":210,"volume":3,"account":"Trader_E","expire_sec":20}'
    '{"order_id":"12","symbol":"MSFT","side":"ask","price":175,"volume":2,"account":"Trader_H","expire_sec":20}'
    '{"order_id":"13","symbol":"MSFT","side":"bid","price":190,"volume":1,"account":"Trader_I","expire_sec":20}'
    '{"order_id":"14","symbol":"MSFT","side":"bid","price":160,"volume":3,"account":"Trader_E","expire_sec":20}'
)

for order in ${orders[@]}; do curl -X POST http://localhost:9999/order -H 'Content-Type: application/json' -d "${order}"; done

curl "http://localhost:9999/order?symbol=MSFT"
curl -X DELETE "http://localhost:9999/order?order_id=1"
curl "http://localhost:9999/order?symbol=MSFT"
curl "http://localhost:9999/history" | jq
curl "http://localhost:9999/order?symbol=MSFT&include_expired"
curl "http://localhost:9999/order?symbol=MSFT&size=2"


exec(open("matching_engine.py").read())
m = MatchingEngine()
m.load_symbols(["AAPL", "MSFT"])
orders = [
    Order(order_id=1, symbol="MSFT", side="ask", price=200, volume=3, account="Trader_A", expire_sec=600),
    Order(order_id=2, symbol="MSFT", side="ask", price=180, volume=5, account="Trader_B", expire_sec=600),
    Order(order_id=3, symbol="MSFT", side="ask", price=170, volume=2, account="Trader_B", expire_sec=1),
    Order(order_id=4, symbol="AAPL", side="ask", price=200, volume=3, account="Trader_A", expire_sec=600),
    Order(order_id=5, symbol="MSFT", side="bid", price=170, volume=4, account="Trader_C", expire_sec=600),
    Order(order_id=6, symbol="MSFT", side="bid", price=150, volume=1, account="Trader_D", expire_sec=600),
    Order(order_id=7, symbol="MSFT", side="bid", price=160, volume=2, account="Trader_E", expire_sec=600),
    Order(order_id=8, symbol="MSFT", side="ask", price=190, volume=4, account="Trader_F", expire_sec=600),
    Order(order_id=9, symbol="MSFT", side="bid", price=185, volume=5, account="Trader_G", expire_sec=600),
    Order(order_id=10, symbol="AAPL", side="bid", price=210, volume=3, account="Trader_E", expire_sec=600),
    Order(order_id=11, symbol="MSFT", side="ask", price=175, volume=2, account="Trader_H", expire_sec=600),
    Order(order_id=12, symbol="MSFT", side="bid", price=190, volume=1, account="Trader_I", expire_sec=600)
]
order_itr = iter(orders)
m.accept_order(next(order_itr))
"""

