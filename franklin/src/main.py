'''
Created on 12/09/2011

@author: Michael
'''

import sys, optparse
from franklin.configuration_utilities import ConfigurationUtilities
from franklin.simulation import ConfigurationRunner

def _exit_with_error_list(message, list=None):
    _print_error_list(message, list)
    sys.exit(1)

def _print_error_list(message, list=None):
    print >> sys.stderr, 'ERROR -', message
    if list:
        for item in list:
            print >> sys.stderr, ' *', item

if __name__ == '__main__' :    
    #parse command line arguments
    parser = optparse.OptionParser()
    parser.add_option('-c', '--config', help='Configuration file to execute.', metavar='FILE')
    parser.add_option('-o', '--optimise', help='Use Psyco optimisation (requires Psyco to be installed).', action='store_true', default=False)
    options, _ = parser.parse_args()
    
    #load psyco
    if options.optimise:
        try:
            print 'Loading Psyco...'
            import psyco
            psyco.full()
        except ImportError:
            _print_error_list('Failed to import Psyco.' )
    
    if not options.config:
        _exit_with_error_list('No configuration file specified via --config option.')
    
    #load config file
    config_module = ConfigurationUtilities.load_config_module(options.config)
    
    print 'Loading config file \'%s\'...' % options.config
    
    if not config_module:
        _exit_with_error_list('Specified configuration file does not exist.')
    
    critical_errors, non_critical_errors = ConfigurationUtilities.validate_config_module(config_module)
    
    if len(critical_errors) > 0:
        _exit_with_error_list('The following critical errors were encountered:', critical_errors)
    
    if len(non_critical_errors) > 0:
        _print_error_list('The following non-critical errors were encountered:', non_critical_errors)
    
    #run the simulation
    print 'Starting simulation...'
    config_runner = ConfigurationRunner(config_module['config'])
    config_runner.run()
    
    