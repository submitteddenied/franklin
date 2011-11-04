'''
Created on 07/10/2011

@author: Luke Horvat
'''

from agents import Generator, Consumer
from data_providers import CapacityDataGenerator, LoadDataGenerator

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
    
    def __init__(self, time_delta, markup, relative, generator_type=None, region=None):
        super(ChangeGeneratorMarkupEvent, self).__init__('Change Generator Markup (value=%0.2f, relative=%s)' % (markup, relative), time_delta)
        self.markup = markup
        self.relative = relative
        self.generator_type = generator_type
        self.region = region
    
    def process_event(self, simulation):
        for agent in simulation.agents.values():
            if isinstance(agent, Generator) and (not self.generator_type or agent.type == self.generator_type) and (not self.region or self.region == agent.region):
                agent.markup = agent.markup + self.markup if self.relative else self.markup

class ChangeGeneratorCapacityDataGeneratorEvent(SimulationEvent):
    '''
    An event that changes the capacity data for a
    specified type of generator in a region (or 
    all generators and regions if not specified).
    '''
    
    def __init__(self, time_delta, capacity_data_gen, generator_type=None, region=None):
        super(ChangeGeneratorCapacityDataGeneratorEvent, self).__init__('Change Generator Capacity Data Generator (value=%s)' % capacity_data_gen, time_delta)
        assert isinstance(capacity_data_gen, CapacityDataGenerator)
        self.capacity_data_gen = capacity_data_gen
        self.generator_type = generator_type
        self.region = region
    
    def process_event(self, simulation):
        for agent in simulation.agents.values():
            if isinstance(agent, Generator) and (not self.generator_type or agent.type == self.generator_type) and (not self.region or self.region == agent.region):
                agent.capacity_data_gen = self.capacity_data_gen

class ChangeConsumerLoadDataGeneratorEvent(SimulationEvent):
    '''
    An event that changes the load data
    generator for consumers in a region (or 
    all regions if not specified).
    '''
    
    def __init__(self, time_delta, load_data_gen, region=None):
        super(ChangeConsumerLoadDataGeneratorEvent, self).__init__('Change Consumer Load Data Generator (value=%s)', time_delta)
        assert isinstance(load_data_gen, LoadDataGenerator)
        self.load_data_gen = load_data_gen
        self.region = region
    
    def process_event(self, simulation):
        for agent in simulation.agents.values():
            if isinstance(agent, Consumer) and (not self.region or self.region == agent.region):
                agent.load_func = self.load_data_gen.get_load