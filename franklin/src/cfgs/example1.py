from franklin.data_providers import RegionalDataInitialiser, RandomCapacityDataProvider, RandomLoadDataProvider, MathLoadDataProvider, StaticCapacityDataProvider
from franklin.monitors import CSVMonitor
from franklin.events import ChangeGeneratorMarkupEvent, ChangeGeneratorCapacityDataProviderEvent, ChangeConsumerLoadDataProviderEvent
from franklin.agents import Generator, Consumer
from datetime import datetime, timedelta

'''
e.g. python main.py -c cfgs/example1
'''

regions = ('VIC', 'NSW')

load_data_provider = MathLoadDataProvider()
capacity_data_provider = StaticCapacityDataProvider()

generators = [ { 'type': Generator, 'params': {'capacity_data_provider': capacity_data_provider, 'region': 'VIC', } },
               { 'type': Generator, 'params': {'capacity_data_provider': capacity_data_provider, 'region': 'NSW', } }, ]

consumers = [ { 'type': Consumer, 'params': { 'load_data_provider': load_data_provider, 'dist_share_func': None, 'region': 'VIC' } },
              { 'type': Consumer, 'params': { 'load_data_provider': load_data_provider, 'dist_share_func': None, 'region': 'NSW' } }, ]

regional_data_initialisers = { 'VIC': RegionalDataInitialiser(load_data_provider, capacity_data_provider),
                               'NSW': RegionalDataInitialiser(load_data_provider, capacity_data_provider), }

events = [ ChangeGeneratorMarkupEvent(timedelta(days=1), markup=1.5, relative=False, region='VIC'), 
           ChangeGeneratorCapacityDataProviderEvent(timedelta(days=2), capacity_data_provider=RandomCapacityDataProvider(1000, 1500, 25, 50)), 
           ChangeConsumerLoadDataProviderEvent(timedelta(days=2), load_data_provider=RandomLoadDataProvider(4000, 7000), region='NSW'), ]

config = {
    'runs': 2,
    'start_time': datetime.today(),
    'end_time': datetime.today() + timedelta(days=4),
    'generators': generators,
    'consumers': consumers,
    'regions': regions,
    'regional_data_initialisers': regional_data_initialisers,
    'events': events,
    'monitor': CSVMonitor(filepath='results/example1.csv'),
}