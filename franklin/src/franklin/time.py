'''
Created on 28/09/2011

@author: Michael
'''

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