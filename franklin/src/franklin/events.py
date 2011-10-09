'''
Created on 07/10/2011

@author: Luke Horvat
'''

from time import Time
from agents import Generator, Consumer

class SimulationEvent(object):
    
    def __init__(self, name, day, interval):
        self.name = name
        self.time = Time(day, interval)
    
    def process_event(self, simulation):
        pass

    def __str__(self):
        return "<Event: %s>" % self.name

class ChangeGeneratorMarkupEvent(SimulationEvent):
    
    def __init__(self, day, interval, new_markup, relative=False):
        super(ChangeGeneratorMarkupEvent, self).__init__('Change Generator Markup (value=%0.2f, relative=%s)' % (new_markup, relative), day, interval)
        self.new_markup = new_markup
        self.relative = relative
    
    def process_event(self, simulation):
        for agent in simulation.agents.values():
            if isinstance(agent, Generator):
                agent.markup = agent.markup + new_markup if self.relative else self.new_markup

class ChangeConsumerLoadGeneratorEvent(SimulationEvent):
    
    def __init__(self, day, interval, load_gen):
        super(ChangeConsumerLoadGeneratorEvent, self).__init__('Change Consumer Load Generator', day, interval)
        self.load_gen = load_gen
    
    def process_event(self, simulation):
        for agent in simulation.agents.values():
            if isinstance(agent, Consumer):
                agent.load_func = self.load_gen.get_load