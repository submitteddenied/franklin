'''
Created on 01/10/2011

@author: Luke Horvat
'''
import os
from franklin.time import Time

class Monitor(object):
    #TODO
    pass

class CSVMonitor(Monitor):
    
    def __init__(self, filepath):
        self.filepath = filepath
        folder = os.path.dirname(filepath)
        if os.path.exists(folder):
            if os.path.exists(filepath):
                os.remove(filepath) #delete existing file at location
        else:
            os.makedirs(folder) #create directory if it does not exist
    
    def log_run(self, run_no, simulation):
        f = open(self.filepath, 'a') #FIXME: not efficient
        f.write('run,%d\n' % run_no)
        f.write('day,interval,region,num_bids,price,load_supplied,total_load\n')
        for operator in simulation.operators_by_region.values():
            time = Time(0,0)
            while time < simulation.end_time:
                interval_price = operator.interval_price_log[time]
                load_supplied = operator.load_supplied_log[time]
                total_load = sum(load_prediction.watts for load_prediction in operator.load_predictions_by_time[time])
                num_bids = len(operator.bids_by_time[time])
                f.write('%d,%d,%s,%d,%f,%f,%f\n' % (time.day, time.interval, operator.region, num_bids, interval_price, load_supplied, total_load))
                time.increment()
        f.close()
        