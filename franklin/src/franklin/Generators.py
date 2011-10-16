'''
Created on 22/09/2011

@author: mjensen
'''
from collections import namedtuple
from time import Time

DataProvider = namedtuple("DataProvider", ['load_data_gen', 'capacity_data_gen'])

class LoadDataGenerator(object):
    def get_capacity(self, generator, time):
        pass
    
    def get_load(self, time):
        pass

class MathLoadDataGenerator(LoadDataGenerator):
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

class RandomLoadDataGenerator(LoadDataGenerator):
    '''
    This class generates random load data within a specified range.
    '''
    def __init__(self, min_load, max_load, seed=0):
        assert 0 <= min_load < max_load
        import random
        self.rand = random.Random()
        self.rand.seed(seed)
        self.min_load = min_load
        self.max_load = max_load
    
    def get_load(self, time):
        return self.rand.uniform(self.min_load, self.max_load)

class CapacityDataGenerator(object):
    def get_capacity(self, generator, time):
        pass
    
    def get_cost(self, generator, time):
        pass

class StaticCapacityDataGenerator(CapacityDataGenerator):
    '''
    This class just spits out flat data for generators to use.
    It does introduce some randomness for the price calculation.
    '''
    
    def __init__(self, seed=0):
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

class RandomCapacityDataGenerator(CapacityDataGenerator):
    '''
    This class generates random capacity data within a specified range.
    '''
    def __init__(self, min_capacity, max_capacity, min_cost, max_cost, seed=0):
        assert 0 <= min_capacity < max_capacity
        assert 0 <= min_cost < max_cost
        import random
        self.rand = random.Random()
        self.rand.seed(seed)
        self.min_capacity = min_capacity
        self.max_capacity = max_capacity
        self.min_cost = min_cost
        self.max_cost = max_cost
    
    def get_capacity(self, generator, time):
        return self.rand.uniform(self.min_capacity, self.max_capacity)
    
    def get_cost(self, generator, time):
        return self.rand.uniform(self.min_cost, self.max_cost)

class CSVLoadDataGenerator(LoadDataGenerator):
    '''
    CSV Load Data Generator reads in a file from the AEMO website to provide load data.
    The file must be in CSV format and contain the following columns:
     - REGION
     - SETTLEMENTDATE (in YYYY/MM/DD HH:mm:ss format)
     - TOTALDEMAND
     - RRP
     - PERIODTYPE
    
    The file must also contain a header row (which will be ignored)
    
    Note that the "SettlementDate" field is (at this time) ignored entirely. The
    first row in the file is treated as time Time(0, 0)
    '''
    
    DataRow = namedtuple('DataRow', ['region', 'settlementdate', 'total_demand', 'rrp', 'period_type'])
    
    def __init__(self, file):
        '''
        Constructs a CSV Load generator. The 'file' argument is the path to a 
        file that contains CSV data.
        '''
        self.file_location = file
        self.data = {}
        self.last_time = None
        self._parse_file()
    
    def _parse_file(self):
        '''
        Reads the given file into a map that will allow an agent to query for
        the total load at the given time.
        '''
        with open(self.file_location, 'r') as file:
            rows = file.read().split('\n')
            t = Time(0, 0)
            for row in rows[1:]:
                row_arr = row.split(',')
                self.data[str(t)] = self.DataRow(*row_arr)
                self.last_time = t
                t = t.next()
    
    def get_load(self, time):
        if self.last_time is None:
            raise Exception("Data not initialised!")
        elif time > self.last_time:
            raise Exception("Not enough data in the file!")
        return float(self.data[str(time)].total_demand)
