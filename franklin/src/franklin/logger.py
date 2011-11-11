'''
This module defines logging classes that can be used within a simulation to log
events as they occur.
'''

import logging, sys
    
class BasicFileLogger(object):
    '''Logs output to a file or output stream.'''
    
    def __init__(self, file=None):
        logging.basicConfig(stream=sys.stdout, file=file,level=logging.DEBUG, format='%(message)s')
    
    def debug(self, msg):
        logging.debug(msg)
        
    def info(self, msg):
        logging.info(msg)
    
    def warning(self, msg):
        logging.warning(msg)
        
    def error(self, msg):
        logging.error(msg)
        
    def critical(self, msg):
        logging.critical(msg)
    
        