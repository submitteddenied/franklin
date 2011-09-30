import franklin.Generators
from franklin.monitors import CSVMonitor

'''
e.g. python.exe main.py -c cfgs/example1
'''

config = {
    'runs': 2,
    'days': 3,
    'max_generators': 3,
    'max_consumers': 1,
    'load_gen': franklin.Generators.MathLoadGenerator(),
    'capacity_gen': franklin.Generators.StaticGenerationCapacityGenerator(),
    'monitor': CSVMonitor(filepath='results/example1.csv'),
}