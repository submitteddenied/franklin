'''
This module contains Franklin's agents.
'''

from message import *

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
        
        self.simulation.message_dispatcher.send(Bid(time.tomorrow(), 250, 50),
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
        self.simulation.message_dispatcher.send(LoadPrediction(tomorrow, load_req),
                                                self.simulation.operator.id)
        
        return []

class AEMOperator(Agent):
    '''
    The AEMOperator agent receives bids from generators and load requirements from
    consumers. It the schedules generators to generate power, based on the best
    cost schedule.
    '''
    
    def process_schedule(self, time):
        self.simulation.log.debug("Get to work, slackers!")
        self.simulation.log.output("Producing Schedule for %s" % time)
    
    def step(self, time):
        messages = self.get_messages()
        self.simulation.log.debug("AEMO %d: I got %d messages!" % (self.id, len(messages)))
        for m in messages:
            if isinstance(m, GenerationAmendment):
                self.handle_generation_amendment(m)
            elif isinstance(m, Bid):
                self.handle_bid(m)
            elif isinstance(m, LoadPrediction):
                self.handle_load_prediction(m)
            else:
                #unrecognised!
                self.simulation.log.warning("AEMO received unknown message type, " + type(m))
            
        return []
    
    def handle_generation_amendment(self, generation_amendment):
        pass
    
    def handle_bid(self, bid):
        pass
    
    def handle_load_prediction(self, prediction):
        pass