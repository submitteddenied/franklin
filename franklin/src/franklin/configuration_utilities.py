'''
Created on 30/09/2011

@author: Luke Horvat
'''

import os
from franklin.logger import Logger
from franklin.data_providers import RegionalDataInitialiser
from franklin.events import SimulationEvent
from franklin.agents import AEMOperator
from datetime import datetime, timedelta

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
    'runs': {
        'pre-validator': lambda x: type(x) is int and x > 0,
        'default': 1,
    },
    'start_time': {
        'pre-validator': lambda x: isinstance(x, datetime),
        'post-processor': lambda x: x.replace(hour=AEMOperator.DAILY_TRADING_START_HOUR, minute=AEMOperator.INTERVAL_DURATION_MINUTES, second=0, microsecond=0),
    },
    'end_time': {
        'pre-validator': lambda x: isinstance(x, datetime),
        'post-validators': {
            'start_time': lambda x, start_time: x > start_time,
        },
        'post-processor': lambda x: x.replace(hour=AEMOperator.DAILY_TRADING_START_HOUR, minute=0, second=0, microsecond=0),
    },
    'generators': {
        #we start with True and then make sure that they all pass _validate_agent_item
        'pre-validator': lambda x: _is_iterable(x, False) and reduce(lambda a, b: a and _validate_agent_item(b), x, True),
    },
    'consumers': {
        #we start with True and then make sure that they all pass _validate_agent_item
        'pre-validator': lambda x: _is_iterable(x, False) and reduce(lambda a, b: a and _validate_agent_item(b), x, True),
    },
    'regions': {
        'pre-validator': lambda x: _is_iterable(x, False),
        'post-processor': lambda x: set(x), #convert to set to remove duplicates
    },
    'regional_data_initialisers': {
        'pre-validator': lambda x: isinstance(x, dict) and reduce(lambda a, b: a and _has_attributes(b, 'load_data_provider', 'capacity_data_provider'), x.values()), 
    },
    'events': {
        'pre-validator': lambda x: _is_iterable(x, False) and reduce(lambda a, b: a and _has_attributes(b, 'process_event'), x, True),
        'default': set(),
    },
    'monitor': {
        'pre-validator': lambda x: _has_attributes(x, 'log_run'),
    },
    'logger': {
        'pre-validator': lambda x: _has_attributes(x, 'debug', 'info', 'warning', 'error', 'critical'),
        'default': Logger(),
    },
}

def _has_attributes(x, *attributes):
    for attribute in attributes:
        if not hasattr(x, attribute):
            return False
    return True

def _is_iterable(x, treat_string_as_iterable=True):
    try:
        iterator = iter(x)
        return True if treat_string_as_iterable else not isinstance(x, basestring)
    except TypeError:
        return False

def _validate_agent_item(generator_dict):
    import inspect
    if 'type' not in generator_dict or 'params' not in generator_dict:
        return False
    params = generator_dict['params']
    args, _, _, defaults = inspect.getargspec(generator_dict['type'].__init__)
    #these params are not specified in the config.
    ignored_args = set(['self', 'id', 'simulation', 'dist_share_func'])
    for arg_idx in range(len(args)):
        if args[arg_idx] in ignored_args:
            continue
        has_default = defaults is not None and len(args) - arg_idx <= len(defaults)
        if not params.has_key(args[arg_idx]) and not has_default:
            return False
    return True

def validate_config_module(config_module):
    return _parse_dict(CONFIG_SYNTAX, config_module, 'config')
     
def _parse_dict(syntax, config_module, dictionary_name):
    critical_errors = []
    non_critical_errors = []
    if dictionary_name in config_module:
        dictionary = config_module[dictionary_name]
        unrecognised_keys = dictionary.keys()
        
        for key in syntax.keys():
            if key in dictionary:
                #raise an error if the value of the key is not specified or invalid
                value = dictionary[key]
                if 'deprecated' in syntax[key]:
                    non_critical_errors.append('Deprecated %s dictionary key \'%s\'. Please use/refer to key \'%s\' instead.' % (dictionary_name, key, syntax[key]['deprecated']))
                if value is None or not syntax[key]['pre-validator'](value):
                    critical_errors.append('Invalid value \'%s\' specified for %s dictionary key \'%s\'.' % (value, dictionary_name, key))
                unrecognised_keys.remove(key)
            else:
                #use the default value (or raise an error if no default exists)
                if 'default' in syntax[key]:
                    dictionary[key] = syntax[key]['default']
                else:
                    critical_errors.append('No value specified for required %s dictionary key \'%s\'.' % (dictionary_name, key))
        
        for key in unrecognised_keys:
            non_critical_errors.append('Unrecognised %s dictionary key \'%s\'.' % (dictionary_name, key))
    else:
        critical_errors.append('No %s dictionary exists in specified configuration file.' % (dictionary_name, key))
    
    #if all pre-validation completed successfully...
    if not critical_errors:
        #apply post-processing to dictionary values if necessary
        for key in set(dictionary.keys()).difference(unrecognised_keys):
            if 'post-processor' in syntax[key]:
                value = dictionary[key]
                dictionary[key] = syntax[key]['post-processor'](value) #replace the dictionary value
        
        #apply post-validation to dictionary values if necessary
        for key in set(dictionary.keys()).difference(unrecognised_keys):
            if 'post-validators' in syntax[key]:
                for post_validator_key, post_validator_func in syntax[key]['post-validators'].items():
                    if not post_validator_func(dictionary[key], dictionary[post_validator_key]):
                        critical_errors.append('%s dictionary key \'%s\' does not comply with dictionary key \'%s\'.' % (dictionary_name, key, post_validator_key))
            
    return critical_errors, non_critical_errors

def load_config_module(module_path):
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
        
        return {
            'config': getattr(mod, 'config', None),
        }
    elif os.path.exists(py_file):
        mod = { }
        
        source = open(file, 'r')
        try:
            exec source.read() in mod
        finally:
            source.close()
        
        return {
            'config': mod.get('config', None),
        }
    else:
        return None