'''
Created on 07/10/2011

@author: Luke Horvat
'''

from agents import Generator, Consumer

class SimulationEvent(object):
    
    def __init__(self, name, time_delta):
        self.name = name
        self.time_delta = time_delta #the relative time difference from the start time of the simulation
    
    def process_event(self, simulation):
        pass

    def __str__(self):
        return "<Event: %s>" % self.name

class ChangeGeneratorMarkupEvent(SimulationEvent):
    '''
    An event that changes the markup value for a
    specified type of generator in a region (or 
    all generators and regions if not specified).
    '''
    
    def __init__(self, time_delta, markup, relative, region, gen_type=None):
        super(ChangeGeneratorMarkupEvent, self).__init__('Change Generator Markup (value=%0.2f, relative=%s)' % (markup, relative), time_delta)
        self.markup = markup
        self.relative = relative
        self.gen_type = gen_type
        self.region = region
    
    def process_event(self, simulation):
        for generator in simulation.generators_by_region[self.region]:
            if hasattr(generator, 'capacity_data_provider') and \
            (not self.gen_type or (hasattr(generator, 'gen_type') and generator.gen_type and generator.gen_type == self.gen_type)):
                generator.markup = generator.markup + self.markup if self.relative else self.markup

class ChangeGeneratorCapacityDataProviderEvent(SimulationEvent):
    '''
    An event that changes the capacity data for a
    specified type of generator in a region (or 
    all generators and regions if not specified).
    '''
    
    def __init__(self, time_delta, capacity_data_provider, region, gen_type=None):
        super(ChangeGeneratorCapacityDataProviderEvent, self).__init__('Change Generator Capacity Data Generator (value=%s)' % capacity_data_provider, time_delta)
        self.capacity_data_provider = capacity_data_provider
        self.gen_type = gen_type
        self.region = region
    
    def process_event(self, simulation):
        for generator in simulation.generators_by_region[self.region]:
            if hasattr(generator, 'capacity_data_provider') and \
            (not self.gen_type or (hasattr(generator, 'gen_type') and generator.gen_type and generator.gen_type == self.gen_type)):
                generator.capacity_data_provider = self.capacity_data_provider

class ChangeConsumerLoadDataProviderEvent(SimulationEvent):
    '''
    An event that changes the load data
    generator for consumers in a region (or 
    all regions if not specified).
    '''
    
    def __init__(self, time_delta, load_data_provider, region):
        super(ChangeConsumerLoadDataProviderEvent, self).__init__('Change Consumer Load Data Generator (value=%s)', time_delta)
        self.load_data_provider = load_data_provider
        self.region = region
    
    def process_event(self, simulation):
        for consumer in simulation.consumers_by_region[self.region]:
            if hasattr(consumer, 'load_data_provider'):
                consumer.load_data_provider = self.load_data_provider