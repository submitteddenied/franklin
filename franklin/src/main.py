'''
Provides a centralised location from which config dictionaries can be loaded
from file, parsed, validated, and run as a simulation (with some optional
command line arguments).
'''

import sys, optparse
from franklin import configuration_utilities

def _exit_with_error_list(message, list=None):
    '''Prints a list of error messages before exiting.'''
    
    _print_error_list(message, list)
    sys.exit(1)

def _print_error_list(message, list=None):
    '''Prints a list of error messages.'''
    
    print >> sys.stderr, 'ERROR -', message
    if list:
        for item in list:
            print >> sys.stderr, ' *', item

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
    
    #load config dictionary from file
    print 'Loading config file \'%s\'...' % options.config
    config_dict = configuration_utilities.load_config_dict_from_module(options.config)
    if not config_dict:
        _exit_with_error_list('Specified configuration file does not exist or config dictionary could not be found in the file.')
    
    #validate the config dictionary
    print 'Parsing and validating config...'
    critical_errors, non_critical_errors = configuration_utilities.validate_config_dict(config_dict)
    if len(critical_errors) > 0:
        _exit_with_error_list('The following critical errors were encountered:', critical_errors)
    if len(non_critical_errors) > 0:
        _print_error_list('The following non-critical errors were encountered:', non_critical_errors)
    
    #run the config (and profile if specified)
    print 'Simulation started...'
    if options.profile:
        from cProfile import Profile
        print 'Initialising cProfile...'
        profiler = Profile()
        try:
            profiler.runcall(configuration_utilities.run_simulation_with_config, config_dict)
        finally:
            import pstats
            print ''
            print 'cProfile statistics:'
            pstats.Stats(profiler).sort_stats('cumulative').print_stats()
    else:
        configuration_utilities.run_simulation_with_config(config_dict)
    print 'Simulation finished.'