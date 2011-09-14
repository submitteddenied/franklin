'''
This module contains Franklin's agents.
'''

from message import Bid

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
        messages = self.simulation.message_dispatcher.fetch_messages(self.id)
        print "%d: I got %d messages!" % (self.id, len(messages))
        
        self.simulation.message_dispatcher.send(Bid(time.tomorrow(), 250, 50),
                                              self.simulation.operator.id)
        
        return []
    
class Consumer(Agent):
    '''
    Represents an electical consumer, which consumes power from the grid and
    reports (predicted) load data to AEMO
    '''
    
    def step(self, time):
        '''
        At each step, consumers fetch their messages from the dispatcher, and
        submit an estimate for the load requirements for tomorrow
        
        Returns a list of agent ids if this Consumer requires other agents (or
        itself) to run their step again in this time interval.
        ''' 
        messages = self.simulation.message_dispatcher.fetch_messages(self.id)
        print "%d: I got %d messages!" % (self.id, len(messages))
        
        self.simulation.message_dispatcher.send(Bid(time.tomorrow(), 250, 50),
                                              self.simulation.operator.id)
        
        return []
        