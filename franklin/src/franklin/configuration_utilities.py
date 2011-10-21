'''
Created on 30/09/2011

@author: Luke Horvat
'''

import os
import sys
from franklin.logger import Logger
from franklin.monitors import Monitor, CSVMonitor
from franklin.Generators import LoadDataGenerator, CapacityDataGenerator, DataProvider
from franklin.events import SimulationEvent

CONFIG_SYNTAX = {
    'runs': {
        'validator': lambda x: type(x) is int and x > 0,
        'default': 1,
    },
    'days': {
        'validator': lambda x: type(x) is int and x > 0,
        'default': 1,
    },
    'generators': {
        #we start with True and then make sure that they all pass validate_agent_item
        'validator': lambda x: reduce(lambda a, b: a and validate_agent_item(b), x, True),
    },
    'consumers': {
        #we start with True and then make sure that they all pass validate_agent_item
        'validator': lambda x: reduce(lambda a, b: a and validate_agent_item(b), x, True),
    },
    'logger': {
        'validator': lambda x: isinstance(x, Logger),
        'default': Logger(),
    },
    'load_data_gen': {
        'validator': lambda x: isinstance(x, LoadDataGenerator),
        'deprecated': True,
        'default': None
    },
    'capacity_data_gen': {
        'validator': lambda x: isinstance(x, CapacityDataGenerator),
        'deprecated': True,
        'default': None
    },
    'regions': {
        'validator': lambda x: type(x) is list,
        'default': ["VIC"]
    },
    'data_providers': {
        #oh holy hell this is messy, first map everything in the list of providers
        #to a true/false value by calling isinstance(c, DataProvider). This yields
        #a list of true/false. Then reduce the list using an "and" so the result will
        #be true if they're all DataProviders. Trust me. -MJ
        'validator': lambda x: reduce(lambda a, b: a and b, map(lambda c: isinstance(c, DataProvider), x)), 
    },
    'monitor': {
        'validator': lambda x: isinstance(x, Monitor),
    },
    'events': {
        'validator': lambda x: reduce(lambda a, b: a and b, map(lambda c: isinstance(c, SimulationEvent), x)),
        'default': [],
    },
}

def validate_agent_item(generator_dict):
    import inspect
    if not (generator_dict.has_key('type') and generator_dict.has_key('params')):
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
    critical_errors = []
    non_critical_errors = []
    _parse_dict(CONFIG_SYNTAX, config_module, 'config', critical_errors, non_critical_errors)
    return (critical_errors, non_critical_errors)
     
def _parse_dict(syntax, config_module, dictionary_name, critical_errors, non_critical_errors):
    if dictionary_name in config_module:
        dictionary = config_module[dictionary_name]
        unrecognised_keys = dictionary.keys()
        for key in syntax.keys():
            if key in dictionary:
                #raise an error if the value of the key is not specified or invalid
                value = dictionary[key]
                if syntax[key].has_key('deprecated') and syntax[key]['deprecated']:
                    non_critical_errors.append('Deprecated %s dictionary key \'%s\'.' % (dictionary_name, key))
                if value is None or not syntax[key]['validator'](value):
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