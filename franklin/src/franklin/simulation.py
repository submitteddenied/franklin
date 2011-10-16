'''
Created on 12/09/2011

@author: Michael
'''

from message import MessageDispatcher
from agents import *

class Simulation(object):
    '''
    The Simulation object contains the logic for running a simulation.
    '''
    
    def __init__(self, logger, monitor, end_time, events, regions, 
                 data_provider, generators, consumers):
        '''
        The Simulation Constructor takes the following arguments:
         - logger: a Logging object
         - monitor: a data monitor object
         - end_time: The end (and therefore length) of a simulation. Simulations
                     always start at Time(0,0)
         - events: A list of events that will be used to modify the simulation while it
           is running.
         - regions: A list of region names
         - data_provider: a list of the same length as regions of the same of 
                     objects with .load_data_gen and .capacity_data_gen, each of which
                     have functions for consumers and generators respectively
         - generators: a list of numbers with the same length as regions 
                         of generators for each region
         - consumers: a list of numbers with the same length as regions 
                         of consumers for each region
        '''
        self.message_dispatcher = MessageDispatcher()
        self.log = logger
        self.monitor = monitor
        self.event_stack = sorted(events, key=lambda event: event.time, reverse=True)
        generator_dict = {}
        consumer_dict = {}
        self.operators = {}
        for i in range(len(regions)):
            region = regions[i]
            self.operators[region] = AEMOperator('AEMO-' + region, self, region)
            region_generators = []
            for generator_type,quantity in generators[i].items():
                for j in range(quantity):
                    gen = Generator("Generator %d.%d" % (i+1, len(region_generators)+1), generator_type, self, data_provider[i].capacity_data_gen, region)
                    generator_dict[gen.id] = gen
                    region_generators.append(gen)
            for j in range(consumers[i]):
                cons= Consumer("Consumer %d.%d" % (i,j), self, 
                               data_provider[i].load_data_gen.get_load, lambda a, t: 1 / consumers[i], region)
                consumer_dict[cons.id] = cons
                
            self.operators[region].initialise(region_generators, data_provider[i].capacity_data_gen,
                                         data_provider[i].load_data_gen)
            
        self.agents = dict(generator_dict.items() + consumer_dict.items() + self.operators.items())
        self.end_time = end_time
    
    def flat_load_dist(self, agent, time):
        cons = 0
        for a in self.agents:
            if isinstance(a, Consumer):
                cons += 1
        if cons > 0:
            return 1/cons
        else:
            return 1
    
    def run(self):
        t = Time(0,0)
        while t < self.end_time:
            self.step(t)
            t = t.increment()
    
    def step(self, time):
        self.log.info(time)
        
        #process events
        while len(self.event_stack) > 0 and self.event_stack[-1].time == time:
            event = self.event_stack.pop()
            event.process_event(self)
            self.log.info("Processed event: %s" % event)
        
        #process agent communications
        nextTime = set()
        thisTime = set(self.agents.keys())
        while(len(thisTime) > 0):
            for a in thisTime:
                if a in nextTime:
                    nextTime.remove(a)
                nextTime.union(self.agents[a].step(time))
            thisTime = nextTime
        
        for operator in self.operators.values():
            operator.process_schedule(time)
