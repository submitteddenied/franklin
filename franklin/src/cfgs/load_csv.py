from franklin.data_providers import DataProvider, CSVOneDayLoadDataGenerator, StaticCapacityDataGenerator
from franklin.monitors import CSVMonitor
from franklin.agents import Generator, Consumer

'''
e.g. python main.py -c cfgs/load_csv
'''
load_data_gen = CSVOneDayLoadDataGenerator('../data/vic-to213005102011.csv')
capacity_data_gen = StaticCapacityDataGenerator()

data_providers = [DataProvider(load_data_gen, capacity_data_gen)]

config = {
    'runs': 1,
    'start_time': load_data_gen.start_time,
    'end_time': load_data_gen.end_time,
    'generators': [{ 'type': Generator, 'params': {'type': Generator.COAL_TYPE, 'capacity_data_gen': capacity_data_gen, 'region': 'VIC'}},],
    'consumers': [{ 'type': Consumer, 'params': {'load_func': load_data_gen.get_load, 'dist_share_func': None, 'region': 'VIC'}},],
    'regions': ['VIC'],
    'data_providers': data_providers,
    'monitor': CSVMonitor(filepath='results/csv_loader.csv'),
}