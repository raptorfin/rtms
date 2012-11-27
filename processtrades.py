import os
import sys
import datetime as dt
import argparse
import logging
import decimal


from common import config, myftp, myxml, logutil
import admin.models as model
import cache

# set logger
LOGGER = logging.getLogger(__name__)

# set constants
LOGDIRSTR = 'logdir'
TCNAME = "DailyTradeConfirms"
TCEXT = "xml"

# init config object
cfg = None

def parse_cmdline_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--today', default=dt.datetime.now().strftime("%Y%m%d"))
    parser.add_argument('--config', default='config.yaml')
    parser.add_argument('--loglevel', default='INFO')
    parser.add_argument('--xml', help="tradeconfirm file")
    merge_configuration(vars(parser.parse_args()))

def merge_configuration(args):
    global cfg
    cfg = config.YAMLConfigProvider(args['config'])
    cfg.required.append(LOGDIRSTR)
    cfg.update_values(args)
    cfg.validate()

def init_logger():
    log = (os.path.join(cfg[LOGDIRSTR], 'processtrades'), cfg['today'], 'log')
    logutil.init_log(cfg['loglevel'], ".".join(log))

def get_tradeconfirm():
    if cfg.get('xml'):
        return cfg['xml']
    else:
        return download_tradeconfirm()

def download_tradeconfirm():
    rfile = '.'.join((cfg['acctnum'], TCNAME, cfg['today'], cfg['today'], TCEXT))
    lfile = (os.path.join(cfg['lpath'], TCNAME), TCEXT)
    lfile = '.'.join(lfile)
    conn = myftp.init_ftp(cfg['ftp.host'], cfg['ftp.user'], cfg['ftp.pwd'])
    myftp.change_dir(conn, cfg['rpath'])
    got_file = myftp.get_file(conn, lfile, rfile)
    myftp.close_ftp(conn)
    if got_file:
        return lfile
    else:
        logging.info("%s not found. Exiting", rfile)
        sys.exit(0)

def parse_tradeconfirm(t_confirm):
    result = myxml.parse_xml(t_confirm)
    return myxml.query_for_element(result, 'TradeConfirm')

def populate_open_trades(tcache, ocache):
    for trade in tcache:
        for order in ocache.get_orders_by_trade(tcache[trade].id):
            ocache[order.broker_order_id] = order

def create_trades(data, icache, ocache):
    for line in data:
        vals = myxml.get_values(line, cfg['fields'])
        create_order(vals, icache, ocache)

def create_order(vals, icache, ocache):
    name = vals['description']
    sym = vals['symbol']
    oid = vals['orderID']
    cat = vals['assetCategory']
    otype = vals['putCall']
    qty = int(vals['quantity'])
    price = decimal.Decimal(vals['price'])
    comm = decimal.Decimal(vals['commission'])
    parts = {'qty': qty, 'price': price, 'comm': comm}

    if name not in icache:
        itype = icache.set_instrument_type(cat, otype)
        icache.create_instrument(name, sym, itype)
    if oid in ocache:
        ocache[oid].price_elems.append(parts)
    else:
        order = model.Order(broker_order_id=oid)
        order.date = vals['dateTime'].replace(',','')
        order.instr_id = icache[name]
        order.price_elems.append(parts)
        order.order_type = ocache.set_order_type(vals['code'], vals['buySell'])
        ocache[oid] = order
 
def main():
    parse_cmdline_args()
    init_logger()
    data = parse_tradeconfirm(get_tradeconfirm())

    if data:
        icache = cache.InstrumentCache(model.Instrument, 'name')
        ocache = cache.OrderCache()
        tcache = cache.TradeCache(model.Trade, 'name')
        populate_open_trades(tcache, ocache)
        create_trades(data, icache, ocache)
        # aggregate_orders(ocache)
        # ocache.process_orders(ocache.group_orders(), tcache)
    else:
        logging.info("No new trades for today")


if __name__ == '__main__':
    main()
