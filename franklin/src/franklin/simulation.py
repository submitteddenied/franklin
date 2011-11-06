'''
Created on 12/09/2011

@author: Michael
'''

from message import MessageDispatcher
from agents import AEMOperator
from datetime import timedelta

class Simulation(object):
    '''
    The Simulation object contains the logic for running a simulation.
    '''
    
    def __init__(self, logger, start_time, end_time, events, regions, regional_data_initialisers, generators, consumers):
        '''
        The Simulation Constructor takes the following arguments:
         - logger: a logging object.
         - start_time: the start date and time of the simulation.
         - end_time: the end date and time of the simulation.
         - events: a collection of events that will be used to modify the simulation while it is running.
         - regions: a collection of region names.
         - regional_data_initialisers: a dictionary of region names mapped to objects that have a load_data_provider and capacity_data_provider.
         - generators: a collection of generators.
         - consumers: a collection of consumers.
        '''
        self.message_dispatcher = MessageDispatcher()
        self.logger = logger
        self.start_time = start_time
        self.end_time = end_time
        self.time = self.start_time
        self._event_stack = sorted(events, key=lambda event: event.time_delta, reverse=True)
        self.regions = regions
        
        self.generators_by_region = {}
        self.consumers_by_region = {}
        self.operator_by_region = {}
        for region in self.regions:
            for generator in generators:
                self.generators_by_region.setdefault(generator.region, set()).add(generator)
            
            for consumer in consumers:
                self.consumers_by_region.setdefault(consumer.region, set()).add(consumer)
            
            operator = AEMOperator('AEMO-%s' % region, region)
            self.operator_by_region[region] = operator
            if region in regional_data_initialisers:
                region_data_initialiser = regional_data_initialisers[region]
                operator.initialise(self, region_data_initialiser.capacity_data_provider, region_data_initialiser.load_data_provider)
    
    def run(self):
        while self.time <= self.end_time:
            self.step()
    
    def step(self):
        self.logger.info('<Time: %s>' % self.time)
        
        #process events
        while len(self._event_stack) > 0 and self.time >= self.start_time + self._event_stack[-1].time_delta:
            event = self._event_stack.pop()
            event.process_event(self)
            self.logger.info('Processed event: %s' % event)
        
        #process agent communications
        agents_for_next_time_step = set()
        agents_for_this_time_step = set(self.agents)
        while len(agents_for_this_time_step) > 0:
            for agent in agents_for_this_time_step:
                if agent in agents_for_next_time_step:
                    agents_for_next_time_step.remove(agent)
                agents_for_next_time_step.union(agent.step(self))
            agents_for_this_time_step = agents_for_next_time_step
        
        #process market operator schedules
        for operator in self.operator_by_region.values():
            operator.process_schedule(self)
        
        #increment the time
        self.time += timedelta(minutes=AEMOperator.INTERVAL_DURATION_MINUTES)
    
    @property
    def agents(self):
        agents = set(self.operator_by_region.values())
        for region in self.regions:
            agents |= self.generators_by_region[region] | self.consumers_by_region[region]
        return agents
        