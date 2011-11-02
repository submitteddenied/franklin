'''
This module contains Franklin's agents.
'''

from copy import copy
from message import GenerationAmendment, LoadPrediction, Bid, Dispatch
from time import Time

INTERVAL_DURATION_MINUTES = 5
INTERVALS_PER_TRADING_PERIOD = 6
INTERVALS_PER_DAY = (60 * 24) / INTERVAL_DURATION_MINUTES

class Agent(object):
    '''
    Represents an agent in the NEM system
    This is an *abstract* class.
    '''

    def __init__(self, id, simulation, region):
        '''
        Constructs a new "agent" with the given simulation.
        Note that you shouldn't call Agent(sim), you should use
        a subclass.
        '''
        self.simulation = simulation
        self.id = id
        self.region = region
        
    def step(self, time):
        '''
        Abstract method!
        '''
        pass
    
    def get_messages(self):
        return self.simulation.message_dispatcher.fetch_messages(self.id)
    
class Generator(Agent):
    '''
    Represents an electical generator, which provides
    power to the NEM and makes money per MWh generated
    '''
    
    COAL_TYPE = 'Coal'
    WIND_TYPE = 'Wind'
    HYDROELECTRIC_TYPE = 'Hydro'
    NUCLEAR_TYPE = 'Nuclear'
    
    def __init__(self, id, simulation, type, capacity_data_gen, region, markup=1.0):
        super(Generator, self).__init__(id, simulation, region)
        self.type = type
        self.capacity_data_gen = capacity_data_gen
        self.markup = markup
    
    def step(self, time):
        '''
        At each step, generators fetch their messages from the dispatcher, post
        a bid for this time tomorrow and possibly revise their generating 
        capacity for the current period.
        
        Returns a list of agent ids if this Generator requires other agents (or
        itself) to run their step again in this time interval.
        ''' 
        messages = self.get_messages()
        #self.simulation.log.debug("%s: I got %d messages!" % (self.id, len(messages)))
        price = self.capacity_data_gen.get_cost(self, time.tomorrow()) * self.markup
        self.simulation.message_dispatcher.send(Bid(self,
                                                    time.tomorrow(), 
                                                    self.capacity_data_gen.get_capacity(self, time.tomorrow()), 
                                                    price),
                                              self.simulation.operators_by_region[self.region].id)
        
        return []
    

class Consumer(Agent):
    '''
    Represents an electrical consumer, which consumes power from the grid and
    reports (predicted) load data to AEMO
    '''
    
    def __init__(self, id, simulation, load_func, dist_share_func, region):
        super(Consumer, self).__init__(id, simulation, region)
        self.load_func = load_func
        self.dist_share_func = dist_share_func
        
    
    def step(self, time):
        '''
        At each step, consumers fetch their messages from the dispatcher, and
        submit an estimate for the load requirements for tomorrow
        
        Returns a list of agent ids if this Consumer requires other agents (or
        itself) to run their step again in this time interval.
        ''' 
        messages = self.get_messages()
        #self.simulation.log.debug("%s: I got %d messages!" % (self.id, len(messages)))
        
        tomorrow = time.tomorrow()
        load_req = self.load_func(tomorrow) * self.dist_share_func(self, tomorrow)
        self.simulation.message_dispatcher.send(LoadPrediction(self, tomorrow, load_req),
                                                self.simulation.operators_by_region[self.region].id)
        
        return []

class AEMOperator(Agent):
    '''
    The AEMOperator agent receives bids from generators and load requirements from
    consumers. It then schedules generators to generate power, based on the best
    cost schedule.
    '''
    
    def __init__(self, id, simulation, region):
        super(AEMOperator, self).__init__(id, simulation, region)
        self.bids_by_time = {} #bids stored in a dict. key = time, value = a list of bids for that time.
        self.load_predictions_by_time = {} #load predictions stored in a dict. key = time, value = load prediction for that time.
        self.interval_price_log = {} #interval prices stored in a dict. key = time, value = interval price at that time.
        self.load_supplied_log = {} #loads supplied stored in a dict. key = time, value = load supplied at that time.
        
    def initialise(self, generators, capacity_data_gen, load_data_gen):
        #seed the operator with day zero load and bid data
        for interval in range(INTERVALS_PER_DAY):
            time = Time(0, interval)
            for generator in generators:
                capacity = capacity_data_gen.get_capacity(generator, time)
                price = capacity_data_gen.get_cost(generator, time)
                self._handle_bid(Bid(generator, time, capacity, price * generator.markup))
            self._handle_load_prediction(LoadPrediction(None, time, load_data_gen.get_load(time)))
    
    def process_schedule(self, time):
        self.simulation.log.info("%s's schedule:" % self.id)
        if time in self.load_predictions_by_time and time in self.bids_by_time:
            #get the load and bids for this interval
            total_load = sum(load_prediction.watts for load_prediction in self.load_predictions_by_time[time])
            bids = self.bids_by_time[time]
            
            #determine which generators get dispatched for this interval based on their price
            self.simulation.log.info(" * Generators dispatched:")
            total_load_supplied = 0
            for bid in sorted(bids, key=lambda bid: bid.price):
                load_to_supply = min(bid.watts, total_load - total_load_supplied)
                total_load_supplied += load_to_supply
                self.simulation.log.info("   * %s (%s) for %dMW" % (bid.sender.id, bid.sender.type, load_to_supply))
                self.simulation.message_dispatcher.send(Dispatch(self, time, load_to_supply), bid.sender.id)
                if total_load_supplied >= total_load:
                    break
            
            self.simulation.log.info(" * Total load supplied: %dMW of %dMW (%.2f%%)" % (total_load_supplied, total_load, (100*total_load_supplied / total_load)))
            self.load_supplied_log[copy(time)] = total_load_supplied
            
            self.simulation.log.info(" * Interval price: $%.2f" % (bid.price))
            self.interval_price_log[copy(time)] = bid.price
            
            #calculate the spot price if the trading period has ended
            if time.interval % INTERVALS_PER_TRADING_PERIOD == INTERVAL_DURATION_MINUTES:
                #calculate the spot price (average interval price) for the trading period
                spot_price = sum(self.interval_price_log[Time(time.day, time.interval - i)] for i in range(INTERVALS_PER_TRADING_PERIOD)) / INTERVALS_PER_TRADING_PERIOD
                self.simulation.log.info(" * Trading period %d finished, spot price: $%.2f" % (time.interval / INTERVALS_PER_TRADING_PERIOD, spot_price))
        else:
            self.simulation.log.info("No load and/or bid data for this time interval.")
            
    
    def step(self, time):
        #self.simulation.log.debug("%s: I got %d messages!" % (self.id, len(messages)))
        messages = self.get_messages()
        for m in messages:
            if isinstance(m, Bid):
                self._handle_bid(m)
            elif isinstance(m, GenerationAmendment):
                self._handle_generation_amendment(m)
            elif isinstance(m, LoadPrediction):
                self._handle_load_prediction(m)
            else:
                #unrecognised!
                self.simulation.log.warning("%s received unknown message type, " % (self.id) + type(m))
            
        return []
    
    def _handle_generation_amendment(self, generation_amendment):
        pass
    
    def _handle_bid(self, bid):
        self.bids_by_time.setdefault(bid.time, set()).add(bid)
    
    def _handle_load_prediction(self, load_prediction):
        self.load_predictions_by_time.setdefault(load_prediction.time, set()).add(load_prediction)