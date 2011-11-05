'''
Created on 22/09/2011

@author: mjensen
'''
from collections import namedtuple
from datetime import datetime
from agents import AEMOperator

RegionalDataInitialiser = namedtuple('RegionalDataInitialiser', ['load_data_provider', 'capacity_data_provider'])

class MathLoadDataProvider(object):
    
    SECONDS_IN_A_MINUTE = 60
    
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
        first_interval_time_today = time.replace(hour=AEMOperator.DAILY_TRADING_START_HOUR, minute=AEMOperator.INTERVAL_DURATION_MINUTES)
        time_difference = time - first_interval_time_today
        interval_number = (time_difference.seconds / self.SECONDS_IN_A_MINUTE) / AEMOperator.INTERVAL_DURATION_MINUTES
        if interval_number < 97 or interval_number > 287:
            return 0
        else:
            return -0.22 * (interval_number - 192)**2 + 2000
    
    def get_load(self, time):
        result = 0
        for func in self.funcs:
            result += func(time)
        
        return result

class RandomLoadDataProvider(object):
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

class StaticCapacityDataProvider(object):
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

class RandomCapacityDataProvider(object):
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

class CSVOneDayLoadDataProvider(object):
    '''
    CSVOneDayLoadDataProvider reads in a file from the AEMO website that contains
    24 hours of load demand data.
    The file must be in CSV format and contain the following columns:
     - REGION
     - SETTLEMENTDATE (in YYYY/MM/DD HH:mm:ss format)
     - TOTALDEMAND
     - RRP
     - PERIODTYPE
    
    The file must also contain a header row (which will be ignored).
    
    By default, when get_load() is called the data generator ignores dates, and
    only uses the time to get the load. This enables the data generator to be
    called repeatedly over many days, returning the same load each day.
    '''
    
    DEFAULT_TIME_FORMAT = '%Y/%m/%d %H:%M:%S'
    DataRow = namedtuple('DataRow', ['region', 'settlement_date', 'total_demand', 'rrp', 'period_type'])
    
    def __init__(self, file, time_format=DEFAULT_TIME_FORMAT, ignore_date=True):
        '''
        Constructs a CSV Load generator. The 'file' argument is the path to a 
        file that contains CSV data.
        '''
        self.time_format = time_format
        self.ignore_date = ignore_date
        self.data, self.start_time, self.end_time = self._parse_file(file)
    
    def _parse_file(self, file_location):
        '''
        Reads the given file into a map that will allow an agent to query for
        the total load at the given time.
        '''
        data = {}
        start_time = None
        end_time = None
        with open(file_location, 'r') as file:
            rows = file.read().split('\n')
            for row in rows[1:]:
                row_arr = row.split(',')
                data_row = self.DataRow(*row_arr)
                #parse settlement date
                settlement_date = data_row.settlement_date
                if settlement_date.endswith((' ', '"', '\'')): 
                    settlement_date = settlement_date[:-1]
                if settlement_date.startswith((' ', '"', '\'')): 
                    settlement_date = settlement_date[1:]
                #store data in a dict mapped to its settlement date
                time = datetime.strptime(settlement_date, self.time_format)
                data[time] = data_row
                if not start_time:
                    start_time = time
                end_time = time
        
        return data, start_time, end_time
    
    def get_load(self, time):
        #TODO: refactor this, it's messy
        if self.ignore_date:
            time = self.start_time.replace(hour=time.hour, minute=time.minute)
            if time not in self.data:
                time = self.end_time.replace(hour=time.hour, minute=time.minute)
        
        return float(self.data[time].total_demand) if time in self.data else None
        