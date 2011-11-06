'''
Created on 01/10/2011

@author: Luke Horvat
'''
import os
from datetime import datetime, timedelta
from agents import AEMOperator

class CSVMonitor(object):
    
    DATE_TIME_FORMAT = '%Y/%m/%d %H:%M:%S'
    
    def __init__(self, filepath):
        self.filepath = filepath
        folder = os.path.dirname(filepath)
        if os.path.exists(folder):
            if os.path.exists(filepath):
                os.remove(filepath) #delete existing file at location
        else:
            os.makedirs(folder) #create directory if it does not exist
    
    def log_run(self, simulation):
        f = open(self.filepath, 'a') #FIXME: not efficient
        f.write('interval,region,num_bids,price,load_supplied,total_load\n')
        for operator in simulation.operator_by_region.values():
            time = simulation.start_time
            while time <= simulation.end_time:
                interval_price = operator.interval_prices_by_time[time]
                load_supplied = operator.load_supplied_by_time[time]
                total_load = sum(load_prediction.watts for load_prediction in operator.load_predictions_by_time[time])
                num_bids = len(operator.bids_by_time[time])
                f.write('%s,%s,%d,%f,%f,%f\n' % (time.strftime(self.DATE_TIME_FORMAT), operator.region, num_bids, interval_price, load_supplied, total_load))
                time += timedelta(minutes=AEMOperator.INTERVAL_DURATION_MINUTES)
        f.close()
        