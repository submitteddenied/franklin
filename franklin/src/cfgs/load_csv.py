from franklin import Generators
from franklin.monitors import CSVMonitor
from franklin.agents import Generator, Consumer

'''
e.g. python main.py -c cfgs/load_csv
'''

providers = [Generators.DataProvider(Generators.CSVLoadDataGenerator('../data/vic-to213005102011.csv'), Generators.StaticCapacityDataGenerator())]

config = {
    'runs': 1,
    'days': 1,
    'generators': [{ 'type': Generator, 'params': {'type': Generator.COAL_TYPE, 'capacity_data_gen': providers[0].capacity_data_gen, 'region': 'VIC'}},],
    'consumers': [{ 'type': Consumer, 'params': {'load_func': providers[0].load_data_gen.get_load, 'dist_share_func': None, 'region': 'VIC'}},],
    'regions': ['VIC'],
    'data_providers': providers,
    'monitor': CSVMonitor(filepath='results/csv_loader.csv'),
}