'''
This modules defines messaging classes used within a simulation to enable agents
to communicate with each other.
'''

class MessageDispatcher(object):
    '''Defines a centralised location from which messages can be sent and received
    between entities.'''
    
    def __init__(self):
        #maps a date to recipient message_id's; each message_id maps to an inbox (a collection of messages)
        self.inboxes_by_id_by_date = {}
    
    def fetch_messages(self, date, recipient_id):
        '''Gets all of messages in the recipient message_id's inbox at this date.'''
        
        inboxes_by_id = self.inboxes_by_id_by_date.get(date, None)
        return inboxes_by_id.get(recipient_id, None) if inboxes_by_id else None
        
    def send(self, message, to_process_date, recipient_id):
        '''Sends the message to the inbox with the given recipient message_id, to be processed at the
        specified date.'''
        
        self.inboxes_by_id_by_date.setdefault(to_process_date, {}).setdefault(recipient_id, []).append(message)

class Message(object):
    '''Defines a bundle of information that can be passed around by a MessageDispatcher.'''
    
    NEXT_ID = 0
    
    def __init__(self, sender_id):
        self.message_id = Message.NEXT_ID
        self.sender_id = sender_id
        Message.NEXT_ID += 1

class GeneratorAvailabilityBid(Message):
    '''Defines a generator's availabilities per trading interval for a specified
    trading day. The trading day is identified by the settlement day of the bid.'''
    
    def __init__(self, sender_id, settlement_date, availability_bid_by_trading_interval_date):
        super(GeneratorAvailabilityBid, self).__init__(sender_id)
        self.settlement_date = settlement_date #the trading day the bid is being submitted for
        self.availability_bid_by_trading_interval_date = availability_bid_by_trading_interval_date #trading interval dates mapped to individual availability bids
    
    class TradingIntervalAvailabilityBid(object):
        '''Defines a generator's availability per price band for a specified trading interval.'''
        
        def __init__(self, availability_per_band, trading_interval_date, max_availability, physical_availability, rate_of_change_up_per_min, rate_of_change_down_per_min):
            self.availability_per_band = availability_per_band #availability per price band
            self.dispatch_interval_date = trading_interval_date #the trading interval this bid applies to
            self.max_availability = max_availability  #TODO: determine when this is used
            self.physical_availability = physical_availability #the physical plant capability (MW) #TODO: determine what this is used for
            self.rate_of_change_up_per_min = rate_of_change_up_per_min #MW per min for energy raise #TODO: determine what this is used for
            self.rate_of_change_down_per_min = rate_of_change_down_per_min #MW per min for energy lower #TODO: determine what this is used for

class GeneratorDispatchOffer(GeneratorAvailabilityBid):
    '''Defines a generator's price offer at various bands and its availabilities 
    per trading interval for a specified trading day. The trading day is identified
    by the settlement day of the offer.'''
    
    def __init__(self, sender_id, settlement_date, price_per_band, availability_bid_by_trading_interval_date):
        super(GeneratorDispatchOffer, self).__init__(sender_id, settlement_date, availability_bid_by_trading_interval_date)
        self.price_per_band = price_per_band #price per the band the total demand falls into

class GeneratorAvailabilityRebid(GeneratorAvailabilityBid):
    '''Defines a modification to a generator's availabilities per trading interval for 
    a specified trading day, with an explanation of why the modification was made. The 
    trading day is identified by the settlement day of the bid.'''
    
    def __init__(self, sender_id, settlement_date, rebid_explanation, availability_bid_by_trading_interval_date):
        super(GeneratorAvailabilityRebid, self).__init__(sender_id, settlement_date, availability_bid_by_trading_interval_date)
        self.rebid_explanation = rebid_explanation
        
class DemandForecast(Message):
    '''Defines the predicted demand expected for a specified dispatch interval date.'''
    
    def __init__(self, sender_id, dispatch_interval_date, demand):
        super(DemandForecast, self).__init__(sender_id)
        self.dispatch_interval_date = dispatch_interval_date #the dispatch interval date of the predicted demand
        self.demand = demand #the demand in MW
        
class GeneratorDispatchNotification(Message):
    '''Defines a notification for a generator to be dispatched at a specified
    dispatch interval date and to generated a specified MW amount of energy.'''
    
    def __init__(self, sender_id, dispatch_interval_date, demand_to_supply):
        super(GeneratorDispatchNotification, self).__init__(sender_id)
        self.dispatch_interval_date = dispatch_interval_date
        self.demand_to_supply = demand_to_supply #the demand in MW