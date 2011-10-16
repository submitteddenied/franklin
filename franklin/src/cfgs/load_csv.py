from franklin import Generators
from franklin.monitors import CSVMonitor
from franklin.agents import Generator

'''
e.g. python main.py -c cfgs/load_csv
'''

providers = [Generators.DataProvider(Generators.CSVLoadDataGenerator('../data/vic-to213005102011.csv'), Generators.StaticCapacityDataGenerator())]

config = {
    'runs': 1,
    'days': 1,
    'generators': [{ Generator.COAL_TYPE: 6 }],
    'consumers': [3],
    'regions': ['VIC'],
    'data_providers': providers,
    'monitor': CSVMonitor(filepath='results/csv_loader.csv'),
}