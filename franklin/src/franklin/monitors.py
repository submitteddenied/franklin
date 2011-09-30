'''
Created on 01/10/2011

@author: Luke Horvat
'''
import os, logging

class Monitor(object):
    #TODO
    pass

class CSVMonitor(Monitor):
    
    def __init__(self, filepath):
        self.filepath = filepath
        folder = os.path.dirname(filepath)
        if not os.path.exists(folder):
            os.makedirs(folder)
    
    def log_period(self, interval_price_log, num_dispatched, load_handled, load):
        f = open(self.filepath, 'w') #FIXME: not efficient
        for time,price in interval_price_log:
            f.write('%d,%d,%f\n' % (time.day, time.interval, price), num_dispatched, load_handled, load)
        f.close()
    
    def log_run_start(self, run_no):
        f = open(self.filepath, 'w') #FIXME: not efficient
        f.write('run,%d\n' % run_no)
        f.close()
    
    def log_run_end(self, spot_price_log):
        f = open(self.filepath, 'w') #FIXME: not efficient
        f.write('day,interval,spot_price\n')
        for time,spot_price in spot_price_log:
            f.write('%d,%d,%f\n' % (time.day, time.interval, spot_price))
        f.close()
        