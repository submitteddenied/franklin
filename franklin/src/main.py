'''
Created on 12/09/2011

@author: Michael
'''

import sys, optparse
from franklin import configuration_utilities
from franklin.simulation import Simulation

def _exit_with_error_list(message, list=None):
    _print_error_list(message, list)
    sys.exit(1)

def _print_error_list(message, list=None):
    print >> sys.stderr, 'ERROR -', message
    if list:
        for item in list:
            print >> sys.stderr, ' *', item

def run_config(config):
    '''Executes simulation runs for a specified config dictionary (assuming the config is valid).'''
    
    logger = config['logger']
    monitor = config['monitor']
    start_time = config['start_time']
    end_time = config['end_time']
    events = config['events']
    regions = config['regions']
    regional_data_initialisers = config['regional_data_initialisers']
    generators = config['generators']
    consumers = config['consumers']
    runs = config['runs']
    
    print 'Starting...'
    for run_no in range(runs):
        print 'Conducting run #%d...' % (run_no + 1)
        
        #run a simulation
        simulation = Simulation(logger, monitor, start_time, end_time, events, regions, regional_data_initialisers, generators, consumers)
        simulation.run()
        
        #log the run via the monitor
        monitor.log_run(run_no, simulation)
    print ' ...Complete'

if __name__ == '__main__' :    
    #parse command line arguments
    parser = optparse.OptionParser()
    parser.add_option('-c', '--config', help='Configuration file to execute.', metavar='FILE')
    parser.add_option('-o', '--optimise', help='Use Psyco optimisation (requires Psyco to be installed).', action='store_true', default=False)
    parser.add_option('-p', '--profile', help='Use cProfile profiling.', action='store_true', default=False)
    options, _ = parser.parse_args()
    
    #load psyco if specified
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
    config_module = configuration_utilities.load_config_module(options.config)
    
    print 'Loading config file \'%s\'...' % options.config
    
    if not config_module:
        _exit_with_error_list('Specified configuration file does not exist.')
    
    critical_errors, non_critical_errors = configuration_utilities.validate_config_module(config_module)
    
    if len(critical_errors) > 0:
        _exit_with_error_list('The following critical errors were encountered:', critical_errors)
    
    if len(non_critical_errors) > 0:
        _print_error_list('The following non-critical errors were encountered:', non_critical_errors)
    
    #run the config (and profile if specified)
    if options.profile:
        from cProfile import Profile
        print 'Initialising cProfile...'
        profiler = Profile()
        try:
            profiler.runcall(run_config, config_module['config'])
        finally:
            import pstats
            print ''
            print 'cProfile statistics:'
            pstats.Stats(profiler).sort_stats('cumulative').print_stats()
    else:
        run_config(config_module['config'])