from franklin.data_providers import RegionalDataInitialiser, CSVOneDayLoadDataProvider, StaticCapacityDataProvider
from franklin.monitors import CSVMonitor
from franklin.agents import Generator, Consumer

'''
e.g. python main.py -c cfgs/load_csv
'''
load_data_provider = CSVOneDayLoadDataProvider('../data/vic-to213005102011.csv')
capacity_data_provider = StaticCapacityDataProvider()

config = {
    'runs': 1,
    'start_time': load_data_provider.start_time,
    'end_time': load_data_provider.end_time,
    'generators': [ { 'type': Generator, 'params': { 'capacity_data_provider': capacity_data_provider, 'region': 'VIC' } }, ],
    'consumers': [ { 'type': Consumer, 'params': { 'load_data_provider': load_data_provider, 'dist_share_func': None, 'region': 'VIC' } }, ],
    'regions': ('VIC',),
    'regional_data_initialisers': { 'VIC': RegionalDataInitialiser(load_data_provider, capacity_data_provider) },
    'monitor': CSVMonitor(filepath='results/csv_loader.csv'),
    'events': [],
}