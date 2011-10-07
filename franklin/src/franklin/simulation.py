'''
Created on 12/09/2011

@author: Michael
'''

from message import MessageDispatcher
from time import Time
from agents import *

class ConfigurationRunner(object):
    
    def __init__(self, config):
        self.config = config
    
    def run(self):
        logger = self.config['logger']
        monitor = self.config['monitor']
        end_time = Time(self.config['days'], 0)
        events = self.config['events']
        load_gen = self.config['load_gen']
        capacity_gen = self.config['capacity_gen']
        max_generators = self.config['max_generators']
        max_consumers = self.config['max_consumers']
        for i in range(self.config['runs']):
            #run a simulation
            simulation = Simulation(logger, monitor, end_time, events, load_gen, capacity_gen, max_generators, max_consumers)
            simulation.run()
            
            #log the run via the monitor
            monitor.log_run(i, simulation.operator.spot_price_log)

class Simulation(object):
    
    def __init__(self, logger, monitor, end_time, events, load_gen, capacity_gen, max_generators, max_consumers):
        self.message_dispatcher = MessageDispatcher()
        self.log = logger
        self.monitor = monitor
        self.end_time = end_time
        self.event_stack = sorted(events, key=lambda event: event.time, reverse=True)
        generators = {}
        for i in range(max_generators):
            id = 'Generator %d' % (i+1)
            generators[id] = Generator(id, self, capacity_gen)
        consumers = {}
        for i in range(max_consumers):
            id = 'Consumer %d' % (i+1)
            consumers[id] = Consumer(id, self, load_gen.get_load, self.flat_load_dist)
        self.agents = dict(generators.items() + consumers.items())
        self.operator = AEMOperator('AEMO', self, load_gen.get_load)
        self.operator.initialise(generators.values(), capacity_gen, load_gen)
        self.agents[self.operator.id] = self.operator
    
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
        
        #process operator schedule
        self.operator.process_schedule(time)