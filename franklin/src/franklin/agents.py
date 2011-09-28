'''
This module contains Franklin's agents.
'''

from message import GenerationAmendment, LoadPrediction, Bid, Dispatch
from time import Time
from collections import deque

INTERVALS_PER_DAY = 24 * 2 * 6;

class Agent(object):
    '''
    Represents an agent in the NEM system
    This is an *abstract* class.
    '''

    def __init__(self, id, simulation):
        '''
        Constructs a new "agent" with the given simulation.
        Note that you shouldn't call Agent(sim), you should use
        a subclass.
        '''
        self.simulation = simulation
        self.id = id
        
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
    
    def __init__(self, id, simulation, data_generator):
        super(Generator, self).__init__(id, simulation)
        self.data_gen = data_generator
        self.markup = 1.1
    
    def step(self, time):
        '''
        At each step, generators fetch their messages from the dispatcher, post
        a bid for this time tomorrow and possibly revise their generating 
        capacity for the current period.
        
        Returns a list of agent ids if this Generator requires other agents (or
        itself) to run their step again in this time interval.
        ''' 
        messages = self.get_messages()
        self.simulation.log.debug("Generator %d: I got %d messages!" % (self.id, len(messages)))
        price = self.data_gen.get_cost(self, time.tomorrow()) * self.markup
        self.simulation.message_dispatcher.send(Bid(self,
                                                    time.tomorrow(), 
                                                    self.data_gen.get_capacity(self, time.tomorrow()), 
                                                    price),
                                              self.simulation.operator.id)
        
        return []
    
class Consumer(Agent):
    '''
    Represents an electrical consumer, which consumes power from the grid and
    reports (predicted) load data to AEMO
    '''
    
    def __init__(self, id, simulation, load_func, dist_share_func):
        super(Consumer, self).__init__(id, simulation)
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
        self.simulation.log.debug("Consumer %d: I got %d messages!" % (self.id, len(messages)))
        
        tomorrow = time.tomorrow()
        load_req = self.load_func(tomorrow) * self.dist_share_func(self, tomorrow)
        self.simulation.message_dispatcher.send(LoadPrediction(self, tomorrow, load_req),
                                                self.simulation.operator.id)
        
        return []

class AEMOperator(Agent):
    '''
    The AEMOperator agent receives bids from generators and load requirements from
    consumers. It the schedules generators to generate power, based on the best
    cost schedule.
    '''
    
    def __init__(self, id, simulation, load_func):
        super(AEMOperator, self).__init__(id, simulation)
        self.pool_queue = deque()
        self.load_pred_queue = deque()
        self.load = {}
        self.load_func = load_func
        self.interval_pricelog = []
        self.pricelog = []
        
        
    def initialise(self, generators, generator_data_gen, load_data_gen):
        time = Time(0, 0)
        for i in range(288):
            bidlist = []
            for g in generators:
                cap = generator_data_gen.get_capacity(g, time)
                price = generator_data_gen.get_cost(g, time)
                bidlist.append(Bid(g, time, cap, price * g.markup))
            self.load_pred_queue.append(load_data_gen.get_load(time))
            time.interval += 1
            self.pool_queue.append(bidlist)
    
    def process_schedule(self, time):
        self.simulation.log.output("Producing Schedule for %s" % time)
        #send load dispatch messages (probably just log them)
        load = self.load_func(time)
        bids = self.pool_queue.popleft()
        bids.sort(key=lambda b: b.price)
        
        dispatched = []
        remaining = load
        handled = 0
        i = 0
        while remaining > 0 and i < len(bids):
            genned = min(bids[i].watts, remaining)
            remaining -= bids[i].watts
            handled += genned
            dispatched.append((bids[i].sender, genned))
            i += 1
        
        if remaining > 0:
            self.simulation.log.error("Unable to handle load requirements! (produced %d/%dMW)" % (handled, load))
        
        self.simulation.log.info("Load: %d, Dispatched %d generators. Interval price: %f" % (load, len(dispatched), bids[i-1].price))
        self.interval_pricelog.append(bids[i-1].price)
        #tell generators what tomorrow's load is predicted to be
        for d in dispatched:
            self.simulation.log.info(" - Dispatching generator %d for %dMW" % (d[0].id, d[1]))
            self.simulation.message_dispatcher.send(Dispatch(self, time, d[1]), d[0].id)
        
        if time.interval % 6 == 5:
            #calculate the price for the trading period
            period_price = sum(self.interval_pricelog) / 6
            self.interval_pricelog = []
            self.simulation.log.info("Trading Period %d finished, spot price: %f" % (time.interval / 6, period_price))
            self.pricelog.append((time, period_price))
    
    def step(self, time):
        messages = self.get_messages()
        self.simulation.log.debug("AEMO %d: I got %d messages!" % (self.id, len(messages)))
        for m in messages:
            if isinstance(m, Bid):
                self.handle_bid(m)
            elif isinstance(m, GenerationAmendment):
                self.handle_generation_amendment(m)
            elif isinstance(m, LoadPrediction):
                self.handle_load_prediction(m)
            else:
                #unrecognised!
                self.simulation.log.warning("AEMO received unknown message type, " + type(m))
            
        return []
    
    def handle_generation_amendment(self, generation_amendment):
        pass
    
    def handle_bid(self, bid):
        if len(self.pool_queue) < INTERVALS_PER_DAY:
            self.pool_queue.append([])
        self.pool_queue[-1].append(bid)
    
    def handle_load_prediction(self, prediction):
        if len(self.load_pred_queue) < INTERVALS_PER_DAY:
            self.load_pred_queue.append(0)
        self.load_pred_queue[-1] += prediction.watts
        