from franklin import Generators
from franklin.monitors import CSVMonitor
from franklin.events import ChangeGeneratorMarkupEvent, ChangeConsumerLoadGeneratorEvent

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
    'events': [ ChangeGeneratorMarkupEvent(day=0, interval=280, new_markup=1.9), 
                ChangeConsumerLoadGeneratorEvent(day=1, interval=260, load_gen=Generators.RandomLoadGenerator(min_load=5000, max_load=8000)), ]
}