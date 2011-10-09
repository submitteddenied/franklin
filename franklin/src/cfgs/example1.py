from franklin import Generators
from franklin.monitors import CSVMonitor

'''
e.g. python main.py -c cfgs/example1
'''

providers = [Generators.DataProvider(Generators.MathLoadGenerator(), Generators.StaticGenerationCapacityGenerator()),
             Generators.DataProvider(Generators.MathLoadGenerator(), Generators.StaticGenerationCapacityGenerator())]

config = {
    'runs': 2,
    'days': 3,
    'generators': [3, 3],
    'consumers': [1, 1],
    'regions': ['VIC', 'NSW'],
    'data_providers': providers,
    'monitor': CSVMonitor(filepath='results/example1.csv'),
}