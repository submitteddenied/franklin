'''
Created on 30/09/2011

@author: Luke Horvat
'''

import os
import sys
from franklin.logger import Logger
from franklin.monitors import Monitor, CSVMonitor
from franklin.Generators import LoadGenerator, CapacityGenerator

CONFIG_SYNTAX = {
    'runs': {
        'validator': lambda x: type(x) is int and x > 0,
        'default': 1,
    },
    'days': {
        'validator': lambda x: type(x) is int and x > 0,
        'default': 1,
    },
    'max_generators': {
        'validator': lambda x: type(x) is int and x > 0,
    },
    'max_consumers': {
        'validator': lambda x: type(x) is int and x > 0,
    },
    'logger': {
        'validator': lambda x: isinstance(x, Logger),
        'default': Logger(),
    },
    'load_gen': {
        'validator': lambda x: isinstance(x, LoadGenerator),
    },
    'capacity_gen': {
        'validator': lambda x: isinstance(x, CapacityGenerator),
    },
    'monitor': {
        'validator': lambda x: isinstance(x, Monitor),
    },
}

class ConfigurationUtilities(object):
    
    @staticmethod    
    def validate_config_module(config_module):
        critical_errors = []
        non_critical_errors = []
        ConfigurationUtilities._parse_dict(CONFIG_SYNTAX, config_module, 'config', critical_errors, non_critical_errors)
        return (critical_errors, non_critical_errors)
        
    @staticmethod    
    def _parse_dict(syntax, config_module, dictionary_name, critical_errors, non_critical_errors):
        if dictionary_name in config_module:
            dictionary = config_module[dictionary_name]
            unrecognised_keys = dictionary.keys()
            for key in syntax.keys():
                if key in dictionary:
                    #raise an error if the value of the key is invalid
                    value = dictionary[key]
                    if not syntax[key]['validator'](value):
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
    
    @staticmethod
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