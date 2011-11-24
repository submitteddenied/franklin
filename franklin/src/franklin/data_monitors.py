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
        file_writer.writerow(['INTERVAL_TYPE', 'REGION_ID', 'TRADING_INTERVAL', 'SPOT_PRICE', 'TOTAL_DEMAND', 'DEMAND_SUPPLIED', 'GENERATORS_DISPATCHED(MW)'])
        for operator in simulation.operator_by_region.values():
            time = simulation.start_date
            while time < simulation.end_date:
                time += timedelta(minutes=AEMOperator.DISPATCH_INTERVAL_DURATION_MINUTES * AEMOperator.DISPATCH_INTERVALS_PER_TRADING_INTERVAL)
                if time in operator.trading_interval_info_by_date:
                    trading_interval_info_by_date = operator.trading_interval_info_by_date[time]
                    file_writer.writerow(['TRADING', 
                                          operator.region_id, 
                                          time.strftime(self.DATE_TIME_FORMAT), 
                                          trading_interval_info_by_date.spot_price, 
                                          trading_interval_info_by_date.total_demand, 
                                          trading_interval_info_by_date.total_demand_supplied,
                                          ','.join(['%s(%.2f)' % (id,demand_supplied) for (id,demand_supplied) in sorted(trading_interval_info_by_date.demand_supplied_by_generator_id.items(), key=lambda (id,demand_supplied): demand_supplied, reverse=True)])])
                else:
                    file_writer.writerow(['TRADING', operator.region_id, time.strftime(self.DATE_TIME_FORMAT), 'N/A', 'N/A', 'N/A', 'N/A'])
        
        #write dispatch interval data to file
        file_writer.writerow(['INTERVAL_TYPE', 'REGION_ID', 'DISPATCH_INTERVAL', 'PRICE', 'PRICE_BAND_NO', 'TOTAL_DEMAND', 'DEMAND_SUPPLIED', 'GENERATORS_DISPATCHED(PRICE,MW)'])
        for operator in simulation.operator_by_region.values():
            time = simulation.start_date
            while time < simulation.end_date:
                time += timedelta(minutes=AEMOperator.DISPATCH_INTERVAL_DURATION_MINUTES)
                if time in operator.dispatch_interval_info_by_date:
                    dispatch_interval_info = operator.dispatch_interval_info_by_date[time]
                    file_writer.writerow(['DISPATCH', 
                                          operator.region_id, 
                                          time.strftime(self.DATE_TIME_FORMAT), 
                                          dispatch_interval_info.price, 
                                          dispatch_interval_info.price_band_no+1, 
                                          dispatch_interval_info.total_demand,
                                          dispatch_interval_info.total_demand_supplied,
                                          ','.join(['%s(%.2f,%.2f)' % (id,price_offer,demand_supplied) for id,(price_offer,demand_supplied) in sorted(dispatch_interval_info.price_offer_and_supply_by_generator_id.items(), key=lambda (id,(price_offer,demand_supplied)): price_offer)])])
                else:
                    file_writer.writerow(['DISPATCH', operator.region_id, time.strftime(self.DATE_TIME_FORMAT), 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'])
    
    def _format_dict_for_csv(self, d):
        return 
    
    def _format_iterable_for_csv(self, iterable):
        return ','.join(iterable)