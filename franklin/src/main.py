'''
Created on 12/09/2011

@author: Michael
'''

import sys
import optparse
from franklin.configuration_utilities import ConfigurationUtilities
from franklin.simulation import Simulation, BatchSimulation

def _exit_with_error_list(message, list=None):
    _print_error_list(message, list)
    sys.exit(1)

def _print_error_list(message, list=None):
    print >> sys.stderr, message
    if list:
        for item in list:
            print >> sys.stderr, ' * ', item

if __name__ == '__main__' :
    #parse command line arguments
    parser = optparse.OptionParser()
    parser.add_option('-c', '--config', help='Configuration file to execute.', metavar='FILE')
    parser.add_option('-b', '--batch', help='Perform a batch run.', action='store_true', default=False)
    options, _ = parser.parse_args()
    
    if not options.config:
        _exit_with_error_list('Cannot proceed - no configuration file specified via --config option.')
    
    config_module = ConfigurationUtilities.load_module('cfgs', options.config)
    
    if not config_module:
        _exit_with_error_list('Cannot proceed - specified configuration file does not exist.')
    
    if 'config' not in config_module:
        _exit_with_error_list('Cannot proceed - no configuration dictionary exists in specified configuration file.')
       
    if options.batch and 'batch' not in config_module:
        _exit_with_error_list('Cannot proceed with batch run - no batch dictionary exists in specified configuration file.')
    
    print 'Parsing \'%s\' configuration dictionary...' % options.config
    critical_errors, non_critical_errors = ConfigurationUtilities.parse_config(config_module['config'])
    
    if len(critical_errors) > 0:
        _exit_with_error_list('Cannot proceed - the following critical errors were encountered:', critical_errors)
    
    if len(non_critical_errors) > 0:
        _print_error_list('The following non-critical errors were encountered:', non_critical_errors)
    
    simulation = None
    if options.batch:
        print 'Parsing \'%s\' batch dictionary...' % options.config
        critical_errors, non_critical_errors = ConfigurationUtilities.parse_batch_config(config_module['batch'])
        
        if len(critical_errors) > 0:
            _exit_with_error_list('Cannot proceed - the following critical errors were encountered:', critical_errors)
        
        if len(non_critical_errors) > 0:
            _print_error_list('The following non-critical errors were encountered:', non_critical_errors)
        
        simulation = BatchSimulation(config_module['config'], config_module['batch'])
    else:
        simulation = Simulation(config_module['config'])
    
    #run the simulation
    print 'Starting simulation...'
    simulation.run()
    