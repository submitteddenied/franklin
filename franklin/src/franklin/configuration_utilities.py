'''
This module defines the syntax for configuration dictionaries used to set 
the parameters for simulations. It also provides functions for loading, 
parsing, validating, and running configuration dictionaries.
'''

import os
from franklin.logger import BasicFileLogger
from franklin.simulation import Simulation
from franklin.events import SimulationEvent
from franklin.agents import AEMOperator
from datetime import datetime, timedelta

'''Defines the name required for a configuration dictionary to be
recognised within a module as an attribute.'''
CONFIG_DICT_NAME = 'config'

'''
The CONFIG_SYNTAX dictionary defines the accepted syntax for simulation configs.
Every key in the dictionary is a setting that can be configured by the user in their 
own configs. Each key has a value that is itself a dictionary, and the items in these
sub-dictionaries are explained below:
 - pre-validator: defines a function that parses and validates a value in a config
                  based on some criteria. Ensures only valid values are accepted and
                  passed into a simulation. Returns True if the value is valid; otherwise,
                  False.
 - post-processor: defines a function that is applied to a config value if it pass 
                   pre-validation. This function must return either a new instance 
                   of the config value (which is accepted back into the original 
                   config), or the same instance (albeit having underwent some
                   modification or processing).
 - post-validators: defines a sub-dictionary of keys mapped to validation functions.
                    Each key in the sub-dictionary is another key from the syntax dictionary,
                    and each value is a function that validates that syntax key's value against
                    the value of this dictionary key (returning a True or False value if both
                    keys are valid). This allows for side-ways validation between keys in the 
                    same dictionary. Post-validation is only performed if a key successfully 
                    passes pre-validation, and after any post-processing operations.
 - default: defines the default value for a config key, in the event that the user does
            not specify one. If no default is specified, the value must be specified by
            the user in their config.
 - deprecated: defines a config key that is legacy and has been replaced by a newer config
               key, the value of this key.
'''
CONFIG_SYNTAX = {
    'start_date': {
        'pre-validator': lambda x: isinstance(x, datetime),
        'post-processor': lambda x: x.replace(hour=AEMOperator.TRADING_DAY_START_HOUR, minute=AEMOperator.TRADING_DAY_START_MINUTE, second=0, microsecond=0),
    },
    'end_date': {
        'pre-validator': lambda x: isinstance(x, datetime),
        'post-processor': lambda x: x.replace(hour=AEMOperator.TRADING_DAY_START_HOUR, minute=AEMOperator.TRADING_DAY_START_MINUTE, second=0, microsecond=0),
        'post-validators': {
            'start_date': lambda x, start_date: x > start_date,
        },
    },
    'generators': {
        'pre-validator': lambda x: _is_iterable(x, False) and reduce(lambda a, b: a and _has_attributes(b, 'get_initialisation_times', 'step', 'handle_messages' ), x),
        'post-processor': lambda x: set(x), #convert to set to remove duplicates
    },
    'consumers': {
        'pre-validator': lambda x: _is_iterable(x, False) and reduce(lambda a, b: a and _has_attributes(b, 'get_initialisation_times', 'step', 'handle_messages' ), x),
        'post-processor': lambda x: set(x), #convert to set to remove duplicates
    },
    'regions': {
        'pre-validator': lambda x: _is_iterable(x, False),
        'post-processor': lambda x: set(x), #convert to set to remove duplicates
    },
    'events': {
        'pre-validator': lambda x: _is_iterable(x, False) and reduce(lambda a, b: a and _has_attributes(b, 'process_event', 'time_delta'), x, True),
        'post-processor': lambda x: set(x), #convert to set to remove duplicates
        'default': set(),
    },
    'data_monitor': {
        'pre-validator': lambda x: _has_attributes(x, 'log_run'),
    },
    'logger': {
        'pre-validator': lambda x: _has_attributes(x, 'debug', 'info', 'warning', 'error', 'critical'),
        'default': BasicFileLogger(),
    },
}

def _has_attributes(x, *attributes):
    '''Returns True if x has the specified attribute(s); otherwise, False.'''
    
    for attribute in attributes:
        if not hasattr(x, attribute):
            return False
    return True

def _is_iterable(x, treat_string_as_iterable=True):
    '''Returns True if x is an iterable sequence; otherwise, False. By default,
    strings are treated as iterable.'''
    
    try:
        iterator = iter(x)
        return True if treat_string_as_iterable else not isinstance(x, basestring)
    except TypeError:
        return False

def validate_config_dict(config_dict):
    '''Validates and parses a config config_dict. Returns a tuple of two lists: 
    critical errors and non-critical errors. If the lists are empty, there were no errors encountered.'''
    
    critical_errors = []
    non_critical_errors = []
    unrecognised_keys = config_dict.keys()
    
    for key in CONFIG_SYNTAX.keys():
        if key in config_dict:
            #raise an error if the value of the key is not specified or invalid
            value = config_dict[key]
            if 'deprecated' in CONFIG_SYNTAX[key]:
                non_critical_errors.append('Deprecated %s key \'%s\'. Please use/refer to key \'%s\' instead.' % (CONFIG_DICT_NAME, key, CONFIG_SYNTAX[key]['deprecated']))
            if value is None or not CONFIG_SYNTAX[key]['pre-validator'](value):
                critical_errors.append('Invalid value \'%s\' specified for %s key \'%s\'.' % (value, CONFIG_DICT_NAME, key))
            unrecognised_keys.remove(key)
        else:
            #use the default value (or raise an error if no default exists)
            if 'default' in CONFIG_SYNTAX[key]:
                config_dict[key] = CONFIG_SYNTAX[key]['default']
            else:
                critical_errors.append('No value specified for required %s key \'%s\'.' % (CONFIG_DICT_NAME, key))
    
    for key in unrecognised_keys:
        non_critical_errors.append('Unrecognised %s key \'%s\'.' % (CONFIG_DICT_NAME, key))
    
    #if all pre-validation completed successfully...
    if not critical_errors:
        #apply post-processing to config_dict values if necessary
        for key in set(config_dict.keys()).difference(unrecognised_keys):
            if 'post-processor' in CONFIG_SYNTAX[key]:
                value = config_dict[key]
                config_dict[key] = CONFIG_SYNTAX[key]['post-processor'](value) #replace the config_dict value
        
        #apply post-validation to config_dict values if necessary
        for key in set(config_dict.keys()).difference(unrecognised_keys):
            if 'post-validators' in CONFIG_SYNTAX[key]:
                for post_validator_key, post_validator_func in CONFIG_SYNTAX[key]['post-validators'].items():
                    if not post_validator_func(config_dict[key], config_dict[post_validator_key]):
                        critical_errors.append('\'%s\' does not comply with %s key \'%s\'.' % (key, CONFIG_DICT_NAME, post_validator_key))
            
    return (critical_errors, non_critical_errors)

def load_config_dict_from_module(module_path):
    '''Loads a Python module containing a config dictionary from a specified file path.
    Returns the config dictionary if it exists; otherwise, None is returned.'''
    
    folder = os.path.dirname(module_path)
    mod_name = os.path.basename(module_path)
    mod_file = os.path.join(*mod_name.split('.')) if '.' in mod_name else mod_name
    py_import = os.path.join(folder, mod_file + '.py')
    init_import = os.path.join(folder, mod_file, '__init__.py')
    py_file = os.path.join(folder, mod_name + '.py')
    
    if os.path.exists(py_import) or os.path.exists(init_import):
        source = folder + '.' + mod_name
        mod = __import__(source)
        for bit in mod_name.split('.'):
            mod = getattr(mod, bit)
        
        return getattr(mod, CONFIG_DICT_NAME, None)
    
    elif os.path.exists(py_file):
        mod = { }
        
        source = open(file, 'r')
        try:
            exec source.read() in mod
        finally:
            source.close()
        
        return mod.get(CONFIG_DICT_NAME, None)
    else:
        return None

def run_simulation_with_config(config_dict):
    '''Executes a simulation run using the specified config dictionary. This can fail if the config
    has not been parsed and validated first.'''
    
    #run a simulation
    simulation = Simulation(config_dict['logger'], config_dict['start_date'], config_dict['end_date'], config_dict['regions'], 
                            config_dict['generators'], config_dict['consumers'], config_dict['events'])
    simulation.run()
    
    #log the run data via the data monitor
    config_dict['data_monitor'].log_run(simulation)