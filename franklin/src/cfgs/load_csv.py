from franklin import Generators
from franklin.monitors import CSVMonitor

'''
e.g. python main.py -c cfgs/example1
'''

providers = [Generators.DataProvider(Generators.CSVLoadGenerator('../data/vic-to213005102011.csv'), Generators.StaticGenerationCapacityGenerator())]

config = {
    'runs': 1,
    'days': 1,
    'generators': [6],
    'consumers': [3],
    'regions': ['VIC'],
    'data_providers': providers,
    'monitor': CSVMonitor(filepath='results/csv_loader.csv'),
}