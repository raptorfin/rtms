from django.db import models


class TradeStatus(models.Model):
    status = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return self.status


class TradeType(models.Model):
    type = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return self.type


class InstrumentType(models.Model):
    type = models.CharField(max_length=100, unique=True)
    multiplier = models.IntegerField()

    def __unicode__(self):
        return self.type


class OrderType(models.Model):
    type = models.CharField(max_length=100, unique=True)
    action = models.CharField(max_length=100)

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
    instr_id = models.ForeignKey(Instrument)
    quantity = models.IntegerField()
    trade_type = models.ForeignKey(TradeType)
    status_type = models.ForeignKey(TradeStatus)
    
    def __unicode__(self):
        return self.name


class Order(models.Model):
    date = models.DateTimeField('order date')
    broker_order_id = models.IntegerField(unique=True)
    instr_id = models.ForeignKey(Instrument)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=6)
    comm = models.DecimalField(max_digits=10, decimal_places=6)
    order_type = models.ForeignKey(OrderType)
    trade_id = models.ForeignKey(Trade)
    price_elems = []
    #price_list = []
    #qty_list = []
    #comm_list = []

    def __unicode__(self):
        return '<brokerid={0}, instrid={1}, date={2}, type={3}>'.format(self.broker_order_id, self.instr_id, self.date, self.order_type)
