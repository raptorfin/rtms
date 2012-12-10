from django.db import models


class TradeStatus(models.Model):
    status = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return self.status


class TradeType(models.Model):
    type = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return self.type


class OrderType(models.Model):
    type = models.CharField(max_length=100, unique=True)
    action = models.CharField(max_length=100)

    def __unicode__(self):
        return self.type


class OrderTradeMapping(models.Model):
    order_type = models.ForeignKey(OrderType)
    trade_type = models.ForeignKey(TradeType)

    def __unicode__(self):
        return '<ordertype={0}, tradetype={1}>'


class InstrumentType(models.Model):
    type = models.CharField(max_length=100, unique=True)
    multiplier = models.IntegerField()

    def __unicode__(self):
        return self.type


class Instrument(models.Model):
    name = models.CharField(max_length=100, unique=True)
    symbol = models.CharField(max_length=100, unique=True)
    instr_type = models.ForeignKey(InstrumentType)

    def __unicode__(self):
        return '<name={0}, sym={1}, type={2}>'.format(self.name, self.symbol, self.instr_type)


class Trade(models.Model):
    date = models.DateField('trade date')
    name = models.CharField(max_length=100, unique_for_date=date)
    instr = models.ForeignKey(Instrument)
    quantity = models.IntegerField()
    trade_type = models.ForeignKey(TradeType)
    status_type = models.ForeignKey(TradeStatus)
    
    def __unicode__(self):
        return self.name


class Order(models.Model):
    date = models.DateTimeField('order date')
    broker_order_id = models.IntegerField(unique=True)
    instr = models.ForeignKey(Instrument)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=6)
    commission = models.DecimalField(max_digits=10, decimal_places=6)
    order_type = models.ForeignKey(OrderType)
    trade = models.ForeignKey(Trade)
    price_elems = []

    def calc_weighted_price(self):
        sum_price = sum(i['price'] * i['qty'] for i in self.price_elems)
        sum_qty = sum(i['qty'] for i in self.price_elems)
        return sum_price / sum_qty

    def __unicode__(self):
        return (
            '<brokerid={0}, instrid={1}, date={2}, type={3}>, '
            'price={4}, qty={5}, comm={6}, tradeid={7}>'.format(self.broker_order_id,
                                                                self.instr_id,
                                                                self.date,
                                                                self.order_type,
                                                                self.price,
                                                                self.quantity,
                                                                self.commission,
                                                                self.trade_id)
                )
