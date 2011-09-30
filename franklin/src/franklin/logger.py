import logging, sys
    
class Logger(object):
    '''Performs logging!'''
    
    def __init__(self):
        logging.basicConfig(file=sys.stdout,level=logging.DEBUG, format='%(asctime)s %(message)s')
    
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
        
    def _logline(self, line):
        logging.info(line)
        
    def output(self, lines):
        if isinstance(lines, list):
            for l in lines:
                self._logline(l)
        else:
            self._logline(lines)