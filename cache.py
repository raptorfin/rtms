import logging
from collections import defaultdict
import admin.models as model
from django.core.exceptions import ObjectDoesNotExist


class BaseCache(dict):
    def __init__(self, cont, attr):
        self.update(self.load(cont, attr))

    def load(self, cont, attr):
        return {getattr(obj, attr): obj for obj in cont.objects.all()}


class InstrumentCache(BaseCache):
    def __init__(self, cont, attr):
        BaseCache.__init__(self, cont, attr)
        self.types = self.load_instrument_types()

    def load_instrument_types(self):
        return {t.type: (t.id, t.multiplier) for t in model.InstrumentType.objects.all()}

    def create_instrument(self, name, sym, type_id):
        i = model.Instrument(name=name, symbol=sym, instr_type_id=type_id[0])
        try:
            i.save()
            self[i.name] = i
        except Exception as err:
            if err[0] == 1062:
                logging.debug("Duplicate entry for %s", i.name)
            else:
                raise Exception(err)

    def set_instrument_type(self, category, otype):
        if category == 'STK':
            return self.types['Stock']
        elif category == 'OPT':
            if otype == 'C':
                return self.types['Call']
            elif otype == 'P':
                return self.types['Put']
        raise Exception("Unable to map instrument type")


class TradeCache(BaseCache):
    def __init__(self, cont, attr):
        self.stypes = self.load_status_types()
        self.ttypes = self.load_trade_types()
        BaseCache.__init__(self, cont, attr)

    def load(self, cont, attr):
        try:
            return {getattr(obj, attr): obj for obj in cont.objects.filter(status_type_id=self.stypes['Open'])}
        except ObjectDoesNotExist:
            logging.info("No Open Trades. Init with empty cache")
            return {}

    def load_status_types(self):
        return {t.status: t for t in model.TradeStatus.objects.all()}
    
    def load_trade_types(self):
        return {t.type: t for t in model.TradeType.objects.all()}
    
    def get_trade(self, order, status):
        name = order.instr_id.name
        if self.get(name):
            return self.get(name)
        else:            
            return model.Trade(
                name=name,
                date=None,
                instr_id=order.instr_id,
                quantity=order.quantity,
                trade_type=None,
                status_type=self.stypes[status]
            )


class OrderCache(BaseCache):
    BUY_ACTION = "Buy"
    SELL_ACTION = "Sell"
    
    def __init__(self):
        self.types = self.load_order_types()
    
    def load_order_types(self):
        return {t.type: t for t in model.OrderType.objects.all()}

    def get_orders_by_trade(self, t_id):
        return model.Order.objects.filter(trade_id_id=t_id)

    def aggregate_orders(self):
        for order in self:
            order.quantity = sum(order.qty_list)
            order.comm = sum(order.comm_list)
            #order.price = 

    def group_orders(self):
        grouped = defaultdict(lambda : defaultdict(list))
        for obj in self:
            i_key = self[obj].instr_id.name
            t_key = self[obj].order_type.action
            grouped[i_key][t_key].append(self[obj])
        return grouped

    def set_order_type(self, code, action):
        if action == 'BUY' and 'O' in code:
            return self.types['BuyToOpen']
        elif action == 'BUY' and 'C' in code:
            return self.types['BuyToClose']
        elif action == 'SELL' and 'O' in code:
            return self.types['SellToOpen']
        elif action == 'SELL' and 'C' in code:
            return self.types['SellToClose']
        raise Exception("Unknown order type: code=%s, action=%s", code, action)

    def process_orders(self, orders, tcache):
        for instr in orders:
            o_orders = orders[instr][self.BUY_ACTION]
            c_orders = orders[instr][self.SELL_ACTION]

            if len(c_orders) == 0:
                trade = tcache.get_trade(o_orders[0], 'Open')
                for order in o_orders:
                    order.trade_id = trade
'''
            elif self.quantities_are_equal(o_orders, c_orders):
                t_cache.process_close_trade(instr, c_orders[0], o_orders[0])
                allorders = o_orders + c_orders
                [self.insert_obj(o) for o in allorders if o.id == 'NULL']
            else:
                self.orphans.extend(o_orders + c_orders)
'''


if __name__ == '__main__':
    i = OrderCache()
    print(i)
