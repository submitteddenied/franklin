'''
Created on 12/09/2011

@author: Michael
'''

from message import MessageDispatcher
from time import Time
from agents import *

class BatchSimulation(object):
    
    def __init__(self, config, batch_config):
        self.simulation_config = config
        self.run_limit = batch_config['run_limit']
        
    def run(self):
        run = 0
        while(run < self.run_limit):
            self.step()
            run += 1
   
    def step(self):
        simulation = Simulation(self.simulation_config)
        simulation.run()

class Simulation(object):
    '''
    classdocs
    '''
    
    def __init__(self, config):
        '''
        Constructor
        '''
        self.log = config['logger']
        self.end_time = Time(config['day_limit'], 0)
        load_gen = config['load_gen']
        capacity_gen = config['capacity_gen']
        generators = {}
        for i in range(config['max_generators']):
            id = 'Generator %d' % (i+1)
            generators[id] = Generator(id, self, capacity_gen)
        consumers = {}
        for i in range(config['max_consumers']):
            id = 'Consumer %d' % (i+1)
            consumers[id] = Consumer(id, self, load_gen.get_load, self.flat_load_dist)
        self.operator = AEMOperator('AEMO', self, load_gen.get_load)
        self.operator.initialise(generators.values(), capacity_gen, load_gen)
        self.agents = dict(generators.items() + consumers.items())
        self.agents[self.operator.id] = self.operator
        self.message_dispatcher = MessageDispatcher()
    
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
        while(t < self.end_time):
            self.step(t)
            t.increment()
    
    def step(self, time):
        nextTime = set()
        thisTime = set(self.agents.keys())
        while(len(thisTime) > 0):
            for a in thisTime:
                if a in nextTime:
                    nextTime.remove(a)
                nextTime.union(self.agents[a].step(time))
            thisTime = nextTime
        self.operator.process_schedule(time)