from franklin.data_providers import DataProvider, RandomCapacityDataGenerator, RandomLoadDataGenerator, MathLoadDataGenerator, StaticCapacityDataGenerator
from franklin.monitors import CSVMonitor
from franklin.events import ChangeGeneratorMarkupEvent, ChangeGeneratorCapacityDataGeneratorEvent, ChangeConsumerLoadDataGeneratorEvent
from franklin.agents import Generator, Consumer
from datetime import datetime, timedelta

'''
e.g. python main.py -c cfgs/example1
'''

providers = [DataProvider(MathLoadDataGenerator(), StaticCapacityDataGenerator()),
             DataProvider(MathLoadDataGenerator(), StaticCapacityDataGenerator())]

config = {
    'runs': 2,
    'start_time': datetime.today(),
    'end_time': datetime.today() + timedelta(days=4),
    'generators': [{ 'type': Generator, 'params': {'type': Generator.COAL_TYPE, 'capacity_data_gen': providers[0].capacity_data_gen, 'region': 'VIC'}},
                   { 'type': Generator, 'params': {'type': Generator.COAL_TYPE, 'capacity_data_gen': providers[1].capacity_data_gen, 'region': 'NSW'}},],
    'consumers': [{ 'type': Consumer, 'params': {'load_func': providers[0].load_data_gen.get_load, 'dist_share_func': None, 'region': 'VIC'}},
                  { 'type': Consumer, 'params': {'load_func': providers[1].load_data_gen.get_load, 'dist_share_func': None, 'region': 'NSW'}},],
    'regions': ['VIC', 'NSW'],
    'data_providers': providers,
    'events': [ChangeGeneratorMarkupEvent(timedelta(days=1), markup=10.5, relative=False, region='VIC'), 
               ChangeGeneratorCapacityDataGeneratorEvent(timedelta(days=2), capacity_data_gen=RandomCapacityDataGenerator(1000, 1500, 25, 50), generator_type=Generator.COAL_TYPE), 
               ChangeConsumerLoadDataGeneratorEvent(timedelta(days=2), load_data_gen=RandomLoadDataGenerator(5000, 8000), region='NSW')],
    'monitor': CSVMonitor(filepath='results/example1.csv'),
}