'''
This module defines classes to control the simulation of energy market operations.
'''

from messaging import MessageDispatcher
from agents import AEMOperator
from datetime import timedelta

class Simulation(object):
    '''
    Defines a class for simulating energy market operations over some 
    specified date range. Calling this class' run() function executes
    a simulation from its start date to its end date.
    '''
    
    def __init__(self, logger, start_date, end_date, region_ids, generators, consumers, events):
        '''
        The constructor takes the following arguments:
         - logger: a logging object.
         - start_date: the start date and time of the simulation.
         - end_date: the end date and time of the simulation.
         - events: a collection of events that will be used to modify the simulation while it is running.
         - region_ids: a collection of region id's.
         - regional_data_initialisers: a dictionary of region_id names mapped to objects that have a load_data_provider and capacity_data_provider.
         - generators: a collection of generators.
         - consumers: a collection of consumers.
        '''
        
        self.logger = logger
        self.start_date = start_date
        self.end_date = end_date
        self.region_ids = region_ids
        self._event_stack = sorted(events, key=lambda event: event.time_delta, reverse=True)
        self.message_dispatcher = MessageDispatcher()
        
        self.operator_by_region = {}
        self.generators_by_region = {}
        self.consumers_by_region = {}
        time_steps_to_run_before_start = set()
        
        #create a market operator per region
        for region_id in self.region_ids:
            operator = AEMOperator('AEMO-%s' % region_id, region_id)
            self.operator_by_region[region_id] = operator
            self.generators_by_region[region_id] = set()
            self.consumers_by_region[region_id] = set()
            time_steps_to_run_before_start.update(operator.get_initialisation_times(self))
        
        #set the generators per region
        for generator in generators:
            if generator.region_id in self.region_ids:
                self.generators_by_region[generator.region_id].add(generator)
                time_steps_to_run_before_start.update(generator.get_initialisation_times(self))
        
        #set the consumers per region
        for consumer in consumers:
            if consumer.region_id in self.region_ids:
                self.consumers_by_region[consumer.region_id].add(consumer)
                time_steps_to_run_before_start.update(consumer.get_initialisation_times(self))
        
        #run the time steps required for market simulation initialisation
        for time in sorted(time_steps_to_run_before_start):
            self.time = time
            self.step(process_market_schedules=False)
    
    def run(self):
        '''Runs a simulation from its start date to its end date.'''
        
        self.time = self.start_date
        while self.time <= self.end_date:
            self.step()
            self.time += timedelta(minutes=1)
    
    def step(self, process_market_schedules=True):
        '''Executes a single time step for a simulation. This includes processing
        defined events at this time, running each agent's step() function, and 
        processing their inter-communications via the message dispatching system.'''
        
        self.logger.info('<Time: %s>' % self.time)
        #process events
        while len(self._event_stack) > 0 and self.time >= self.start_date + self._event_stack[-1].time_delta:
            event = self._event_stack.pop()
            event.process_event(self)
            self.logger.info('Processed simulation event: %s' % event)
        
        #execute each agent for this time step
        agents_by_id = self.agents_by_id
        for agent in agents_by_id.values():
            agent.step(self)
        
        #handle agent communications for this time step
        #TODO: refactor this
        message_inboxes_by_agent_id = self.message_dispatcher.inboxes_by_id_by_date.get(self.time, None)
        while message_inboxes_by_agent_id and len(message_inboxes_by_agent_id) > 0:
            message_inboxes_by_agent_id_copy = dict(message_inboxes_by_agent_id) #make a copy of the inboxes
            message_inboxes_by_agent_id.clear() #clear all inboxes
            for id,messages in message_inboxes_by_agent_id_copy.items():
                agents_by_id[id].handle_messages(self, messages)
    
    @property
    def agents_by_id(self):
        #NOTE: below may be slow if called repeatedly throughout a simulation.
        #however, if agents can be injected into the simulation while it is running
        #(which is entirely possible), this may be the only way to effectively
        #collate them all into a single dictionary. the alternative would be to store all
        #agents in a single dictionary all the time.
        agents_by_id = {}
        for region_id in self.region_ids:
            if region_id in self.operator_by_region:
                operator = self.operator_by_region[region_id]
                agents_by_id[operator.id] = operator
            if region_id in self.generators_by_region:
                agents_by_id.update({ generator.id : generator for generator in self.generators_by_region[region_id] })
            if region_id in self.consumers_by_region:
                agents_by_id.update({ consumer.id : consumer for consumer in self.consumers_by_region[region_id] })
        return agents_by_id
        