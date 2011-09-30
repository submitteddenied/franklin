'''
Created on 22/09/2011

@author: mjensen
'''

class LoadGenerator(object):
    def get_capacity(self, generator, time):
        pass
    
    def get_load(self, time):
        pass

class MathLoadGenerator(LoadGenerator):
    '''
    This class uses mathematical functions to generate load data.
    '''
    def __init__(self):
        self.funcs = [self._base_load, self._peaks]
    
    def _base_load(self, time):
        return 4000
    
    def _peaks(self, time):
        '''
        Using formula -.22(x-192)^2+2000 to get a rough approximation of a peak in the day
        See http://fooplot.com/index.php?q0=-.22%28x-192%29^2+2000
        '''
        if time.interval < 97 or time.interval > 287:
            return 0
        else:
            return -0.22 * (time.interval - 192)**2 + 2000
    
    def get_load(self, time):
        result = 0
        for func in self.funcs:
            result += func(time)
        
        return result

class CapacityGenerator(object):
    def get_capacity(self, generator, time):
        pass
    
    def get_cost(self, generator, time):
        pass

class StaticGenerationCapacityGenerator(CapacityGenerator):
    '''
    This class just spits out flat data for generators to use.
    It does introduce some randomness for the price calculation.
    '''
    
    def __init__(self, seed=9487239147):
        import random
        self.rand = random.Random()
        self.rand.seed(seed)
    
    def get_capacity(self, generator, time):
        '''
        Returns 1110, the average generation capacity of power plants in Victoria
        '''
        return 1110
    
    def get_cost(self, generator, time):
        '''
        Returns $32.50 plus/minus some random perturbation
        '''
        return 32.5 + self.rand.uniform(-10, 10)