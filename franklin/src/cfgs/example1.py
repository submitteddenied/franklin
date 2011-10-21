from franklin import Generators
from franklin.monitors import CSVMonitor
from franklin.events import ChangeGeneratorMarkupEvent, ChangeGeneratorCapacityDataGeneratorEvent, ChangeConsumerLoadDataGeneratorEvent
from franklin.agents import Generator, Consumer

'''
e.g. python main.py -c cfgs/example1
'''

providers = [Generators.DataProvider(Generators.MathLoadDataGenerator(), Generators.StaticCapacityDataGenerator()),
             Generators.DataProvider(Generators.MathLoadDataGenerator(), Generators.StaticCapacityDataGenerator())]

config = {
    'runs': 2,
    'days': 3,
    'generators': [{ 'type': Generator, 'params': {'type': Generator.COAL_TYPE, 'capacity_data_gen': providers[0].capacity_data_gen, 'region': 'VIC'}},
                   { 'type': Generator, 'params': {'type': Generator.COAL_TYPE, 'capacity_data_gen': providers[1].capacity_data_gen, 'region': 'NSW'}},],
    'consumers': [{ 'type': Consumer, 'params': {'load_func': providers[0].load_data_gen.get_load, 'dist_share_func': None, 'region': 'VIC'}},
                  { 'type': Consumer, 'params': {'load_func': providers[1].load_data_gen.get_load, 'dist_share_func': None, 'region': 'NSW'}},],
    'regions': ['VIC', 'NSW'],
    'data_providers': providers,
    'monitor': CSVMonitor(filepath='results/example1.csv'),
    'events': [ChangeGeneratorMarkupEvent(day=0, interval=280, markup=1.5, region='VIC'), 
               ChangeGeneratorCapacityDataGeneratorEvent(day=1, interval=240, capacity_data_gen=Generators.RandomCapacityDataGenerator(1000, 1500, 25, 50), generator_type=Generator.COAL_TYPE), 
               ChangeConsumerLoadDataGeneratorEvent(day=1, interval=260, load_data_gen=Generators.RandomLoadDataGenerator(5000, 8000), region='VIC')],
}