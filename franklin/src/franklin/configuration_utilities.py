'''
Created on 30/09/2011

@author: Luke Horvat
'''

import os
import sys
from franklin.logger import Logger
from franklin.Generators import LoadGenerator, CapacityGenerator

CONFIG_SYNTAX = {
    'day_limit': {
        'validator': lambda x: type(x) == int and x > 0,
        'default': 1,
    },
    'max_generators': {
        'validator': lambda x: type(x) == int and x > 0,
    },
    'max_consumers': {
        'validator': lambda x: type(x) == int and x > 0,
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
}

BATCH_SYNTAX = {
    'run_limit': {
      'validator': lambda x: type(x) == int and x > 0,
      }
}

class ConfigurationUtilities(object):
    
    @staticmethod
    def parse_config(config):
        return ConfigurationUtilities._parse_dict(CONFIG_SYNTAX, config)
        
    @staticmethod
    def parse_batch_config(batch):
        return ConfigurationUtilities._parse_dict(BATCH_SYNTAX, batch)
    
    @staticmethod    
    def _parse_dict(syntax, dictionary):
        critical_errors = []
        non_critical_errors = []
        unrecognised_keys = dictionary.keys()
        for key in syntax.keys():
            if key in dictionary:
                #raise an error if the value of the key is invalid
                value = dictionary[key]
                if not syntax[key]['validator'](value):
                    critical_errors.append('Invalid value \'%s\' specified for dictionary key \'%s\'.' % (value, key))
                unrecognised_keys.remove(key)
            else:
                #use the default value (or raise an error if no default exists)
                if 'default' in syntax[key]:
                    dictionary[key] = syntax[key]['default']
                else:
                    critical_errors.append('No value specified for required dictionary key \'%s\'.' % key)
        
        for key in unrecognised_keys:
            non_critical_errors.append('Unrecognised dictionary key \'%s\'.' % key)
        
        return (critical_errors, non_critical_errors)
    
    @staticmethod
    def load_module(folder, mod_name):
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
                'batch': getattr(mod, 'batch', None),
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
                'batch': mod.get('batch', None),
            }
        else:
            return None