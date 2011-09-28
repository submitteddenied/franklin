'''
Created on 12/09/2011

@author: Michael
'''

from message import MessageDispatcher
from time import Time
from agents import *
import Generators

class Simulation(object):
    '''
    classdocs
    '''
    
    def __init__(self):
        '''
        Constructor
        '''
        load_gen = Generators.MathLoadGenerator()
        capacity_gen = Generators.StaticGenerationCapacityGenerator()
        generators = {1: Generator(1, self, capacity_gen)}
        self.agents = {2: Consumer(2, self, load_gen.get_load, self.flat_load_dist)}
        for id, agent in generators.items():
            self.agents[id] = agent
        self.operator = AEMOperator(3, self, load_gen.get_load)
        self.operator.initialise(generators.values(), capacity_gen, load_gen)
        self.agents[self.operator.id] = self.operator
        self.message_dispatcher = MessageDispatcher()
        self.log = Logger()
        self.end_time = Time(1,0)
    
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
        while(t.increment() < self.end_time):
            self.step(t)
    
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
    
import logging, sys
    
class Logger(object):
    '''Performs logging!'''
    
    def __init__(self):
        logging.basicConfig(file=sys.stdout,level=logging.DEBUG, format='%(asctime)s %(message)s')
    
    def debug(self, msg):
        logging.debug(msg)
        
    def info(self, msg):
        logging.info(msg)
    
    def warning(self, msg):
        logging.warning(msg)
        
    def error(self, msg):
        logging.error(msg)
        
    def critical(self, msg):
        logging.critical(msg)
        
    def _logline(self, line):
        logging.info(line)
        
    def output(self, lines):
        if isinstance(lines, list):
            for l in lines:
                self._logline(l)
        else:
            self._logline(lines)
    