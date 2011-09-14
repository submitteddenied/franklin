'''
Created on 12/09/2011

@author: Michael
'''

from message import MessageDispatcher
from agents import *

class Simulation(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.agents = [Generator(1, self), Consumer(2, self)]
        self.operator = Agent(3, self)
        #self.operator =
        self.message_dispatcher = MessageDispatcher()
        t = Time(0,0)
        self.message_dispatcher.send(Bid(t, 100, 100), 1)
        self.message_dispatcher.send(Bid(t, 100, 100), 2)
    
    
    def run(self):
        #while(True):
        self.step()
    
    def step(self):
        t = Time(0,0)
        for a in self.agents:
            a.step(t)
    
    
    


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