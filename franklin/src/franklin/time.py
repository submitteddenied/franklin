'''
Created on 28/09/2011

@author: Michael
'''
INTERVALS_IN_DAY = 6 * 2 * 24

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
    
    def increment(self):
        self.interval += 1
        if self.interval > INTERVALS_IN_DAY:
            self.interval = 0
            self.day += 1
            
        return self
    
    def __str__(self):
        return "<Day: %d, Interval: %d>" % (self.day, self.interval)
    
    def __eq__(self, other):
        return self._comp(other) == 0
    
    def __ne__(self, other):
        return not self == other
    
    def __lt__(self, other):
        return self._comp(other) < 0
    
    def __le__(self, other):
        return self._comp(other) <= 0
    
    def __gt__(self, other):
        return self._comp(other) > 0
    
    def __ge__(self, other):
        return self._comp(other) >= 0
    
    def _comp(self, other):
        '''
        Does a "java style" comparison between two Time objects. Returns 0 if 
        they are equal,  positive number if self > other and a negative number 
        if self < other.
        Note: This number can't really be used for inferring the distance between
        two times.
        '''
        day_diff = self.day - other.day
        if day_diff == 0:
            return self.interval - other.interval
        else:
            return day_diff