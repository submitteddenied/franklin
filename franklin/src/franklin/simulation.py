'''
Created on 12/09/2011

@author: Michael
'''

from message import MessageDispatcher
from agents import *
import aemo_functions

class Simulation(object):
    '''
    classdocs
    '''
    
    def __init__(self):
        '''
        Constructor
        '''
        self.agents = {1: Generator(1, self), 2: Consumer(2, self, aemo_functions.base_load, self.flat_load_dist)}
        self.operator = AEMOperator(3, self)
        self.agents[self.operator.id] = self.operator
        self.message_dispatcher = MessageDispatcher()
        self.log = Logger()
    
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
        #while(True):
        self.step()
    
    def step(self):
        t = Time(0,0)
        nextTime = set()
        thisTime = set(self.agents.keys())
        while(len(thisTime) > 0):
            for a in thisTime:
                if a in nextTime:
                    nextTime.remove(a)
                nextTime.union(self.agents[a].step(t))
            thisTime = nextTime
        self.operator.process_schedule(t)


class Time(object):
    '''
    Represents a time in the simulation.
    '''
    
    def __init__(self, day, interval):
        '''
        Constructs a new time set to the given day and interval indices.
        Intervals are 5-minute dispatch periods, which are the lowest resolution
        available in the simulation. 
        '''
        self.day = day
        self.interval = interval
        
    def tomorrow(self):
        '''
        Returns a copy of this time, set to tomorrow
        Note: the new time will be at the same interval of the day
        '''
        return Time(self.day + 1, self.interval)
    
    def __str__(self):
        return "<Day: %d, Interval: %d>" % (self.day, self.interval)
    
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
    