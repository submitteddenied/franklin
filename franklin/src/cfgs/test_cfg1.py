import franklin.Generators

config = {
    'day_limit': 2,
    'max_generators': 3,
    'max_consumers': 1,
    'load_gen': franklin.Generators.MathLoadGenerator(),
    'capacity_gen': franklin.Generators.StaticGenerationCapacityGenerator(),
}

batch = {
    'run_limit': 5,
}

