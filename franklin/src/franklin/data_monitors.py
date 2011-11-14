'''
This module defines classes that enable one to monitor the output data produced by
a simulation run.
'''

import os
from datetime import datetime, timedelta
from csv import writer
from agents import AEMOperator

class CSVFileMonitor(object):
    '''A basic monitor that outputs demand and price per dispatch interval
    per region to a specified file. Output is in CSV format.'''
    
    DATE_TIME_FORMAT = '%Y/%m/%d %H:%M:%S'
    
    def __init__(self, file_location):
        self.file_location = file_location
    
    def log_run(self, simulation):
        '''Writes dispatch interval price and demand data to file.'''
        
        #create directory if it does not exist
        directory = os.path.dirname(self.file_location)
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        #write data to file
        file_writer = writer(open(self.file_location, 'wb'))
        file_writer.writerow(['REGION_ID', 'DISPATCH_INTERVAL', 'PRICE', 'DEMAND_SUPPLIED', 'TOTAL_DEMAND'])
        for operator in simulation.operator_by_region.values():
            time = simulation.start_date
            while time <= simulation.end_date:
                dispatch_interval_price = operator.prices_by_dispatch_interval_date.get(time, 0)
                demand_supplied = operator.demand_supplied_by_dispatch_interval_date.get(time, 0)
                total_demand = sum(demand_forecast.demand for demand_forecast in operator.demand_forecasts_by_dispatch_interval_date[time]) if time in operator.demand_forecasts_by_dispatch_interval_date else 0
                file_writer.writerow([operator.region_id, time.strftime(self.DATE_TIME_FORMAT), dispatch_interval_price, demand_supplied, total_demand])
                time += timedelta(minutes=AEMOperator.DISPATCH_INTERVAL_DURATION_MINUTES)
        