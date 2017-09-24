from google.appengine.ext import ndb


class Transaction(ndb.Model):
    create_time = ndb.DateTimeProperty(auto_now_add=True)
    amount = ndb.FloatProperty()
    payment_time = ndb.DateTimeProperty()
    payment_address = ndb.StringProperty()
    tx_id = ndb.StringProperty()
    payment_complete = ndb.BooleanProperty(default=False)
