from franklin.Generators import MathLoadGenerator, StaticGenerationCapacityGenerator, RandomLoadGenerator
from franklin.monitors import CSVMonitor
from franklin.events import ChangeGeneratorMarkupEvent, ChangeConsumerLoadGeneratorEvent

'''
e.g. python main.py -c cfgs/example1
'''

config = {
    'runs': 2,
    'days': 3,
    'max_generators': 3,
    'max_consumers': 1,
    'load_gen': MathLoadGenerator(),
    'capacity_gen': StaticGenerationCapacityGenerator(),
    'monitor': CSVMonitor(filepath='results/example1.csv'),
    'events': [ ChangeGeneratorMarkupEvent(day=0, interval=280, new_markup=1.9), 
                ChangeConsumerLoadGeneratorEvent(day=1, interval=260, load_gen=RandomLoadGenerator(min_load=5000, max_load=8000)), ]
}