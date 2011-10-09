'''
Created on 01/10/2011

@author: Luke Horvat
'''
import os

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
    
    '''
    def log_period(self, interval_price_log, num_dispatched, load_handled, load):
        f = open(self.filepath, 'w') #FIXME: not efficient
        for time,price in interval_price_log:
            f.write('%d,%d,%f\n' % (time.day, time.interval, price), num_dispatched, load_handled, load)
        f.close()
    '''
    
    def log_run(self, run_no, spot_price_log, region=""):
        f = open(self.filepath, 'a') #FIXME: not efficient
        f.write('run,%d\n' % run_no)
        f.write('day,interval,spot_price,region\n')
        for time,spot_price in spot_price_log:
            #FIXME: inefficient to log region on every line
            f.write('%d,%d,%f,%s\n' % (time.day, time.interval, spot_price, region))
        f.close()
        