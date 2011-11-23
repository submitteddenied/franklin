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
        
        #open file
        file_writer = writer(open(self.file_location, 'wb'))
        
        #write trading interval data to file
        file_writer.writerow(['INTERVAL_TYPE', 'REGION_ID', 'TRADING_INTERVAL', 'SPOT_PRICE', 'DEMAND_SUPPLIED', 'TOTAL_DEMAND', 'GENERATORS_DISPATCHED'])
        for operator in simulation.operator_by_region.values():
            time = simulation.start_date
            while time < simulation.end_date:
                time += timedelta(minutes=AEMOperator.DISPATCH_INTERVAL_DURATION_MINUTES * AEMOperator.DISPATCH_INTERVALS_PER_TRADING_INTERVAL)
                if time in operator.trading_interval_info_by_date:
                    trading_interval_info_by_date = operator.trading_interval_info_by_date[time]
                    file_writer.writerow(['TRADING', operator.region_id, time.strftime(self.DATE_TIME_FORMAT), trading_interval_info_by_date.spot_price, 
                                          trading_interval_info_by_date.total_demand_supplied, trading_interval_info_by_date.total_demand, 
                                          self._format_iterable_for_csv(trading_interval_info_by_date.generator_ids_dispatched)])
                else:
                    file_writer.writerow(['TRADING', operator.region_id, time.strftime(self.DATE_TIME_FORMAT), 'N/A', 'N/A', 'N/A', 'N/A'])
        
        #write dispatch interval data to file
        file_writer.writerow(['INTERVAL_TYPE', 'REGION_ID', 'DISPATCH_INTERVAL', 'PRICE', 'PRICE_BAND_NO', 'DEMAND_SUPPLIED', 'TOTAL_DEMAND', 'GENERATORS_DISPATCHED'])
        for operator in simulation.operator_by_region.values():
            time = simulation.start_date
            while time < simulation.end_date:
                time += timedelta(minutes=AEMOperator.DISPATCH_INTERVAL_DURATION_MINUTES)
                if time in operator.dispatch_interval_info_by_date:
                    dispatch_interval_info = operator.dispatch_interval_info_by_date[time]
                    file_writer.writerow(['DISPATCH', operator.region_id, time.strftime(self.DATE_TIME_FORMAT), dispatch_interval_info.price, 
                                          dispatch_interval_info.price_band_no+1, dispatch_interval_info.total_demand_supplied, 
                                          dispatch_interval_info.total_demand, self._format_iterable_for_csv(dispatch_interval_info.generator_ids_dispatched)])
                else:
                    file_writer.writerow(['DISPATCH', operator.region_id, time.strftime(self.DATE_TIME_FORMAT), 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'])
    
    def _format_iterable_for_csv(self, iterable):
        return ','.join(iterable)