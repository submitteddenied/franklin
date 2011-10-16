from franklin import Generators
from franklin.monitors import CSVMonitor
from franklin.events import ChangeGeneratorMarkupEvent, ChangeGeneratorCapacityDataGeneratorEvent, ChangeConsumerLoadDataGeneratorEvent
from franklin.agents import Generator

'''
e.g. python main.py -c cfgs/example1
'''

providers = [Generators.DataProvider(Generators.MathLoadDataGenerator(), Generators.StaticCapacityDataGenerator()),
             Generators.DataProvider(Generators.MathLoadDataGenerator(), Generators.StaticCapacityDataGenerator())]

config = {
    'runs': 2,
    'days': 3,
    'generators': [{ Generator.COAL_TYPE: 2, Generator.WIND_TYPE: 1, },
                   { Generator.COAL_TYPE: 1, Generator.HYDROELECTRIC_TYPE: 2, Generator.NUCLEAR_TYPE: 1, }],
    'consumers': [1, 1],
    'regions': ['VIC', 'NSW'],
    'data_providers': providers,
    'monitor': CSVMonitor(filepath='results/example1.csv'),
    'events': [ChangeGeneratorMarkupEvent(day=0, interval=280, markup=1.5, region='VIC'), 
               ChangeGeneratorCapacityDataGeneratorEvent(day=1, interval=240, capacity_data_gen=Generators.RandomCapacityDataGenerator(1000, 1500, 25, 50), generator_type=Generator.COAL_TYPE), 
               ChangeConsumerLoadDataGeneratorEvent(day=1, interval=260, load_data_gen=Generators.RandomLoadDataGenerator(5000, 8000), region='VIC')],
}