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
    
    def __init__(self, logger, monitor, start_time, end_time, events, regions, regional_data_initialisers, generators, consumers):
        '''
        The Simulation Constructor takes the following arguments:
         - logger: a Logging object
         - monitor: a data monitor object
         - start_time: The start date and time of a simulation.
         - end_time: The end date and time of a simulation.
         - events: A list of events that will be used to modify the simulation while it
           is running.
         - regions: A list of region names
         - regional_data_initialisers: a list of the same length as regions of the same of 
                     objects with .load_data_gen and .capacity_data_gen, each of which
                     have functions for consumers and generators respectively
         - generators: a list of "agent spec" dictionaries, see consumers.
         - consumers: a list of "agent spec" dictionaries, which contains the following:
             'type': An agent class to be used to instantiate this agent
             'params': A dict containing params the class requires to be constructed
                 excluding the 'id' and 'simulation' args, which will be provided
                 when the simulation is being constructed.
        '''
        self.message_dispatcher = MessageDispatcher()
        self.logger = logger
        self.monitor = monitor
        self.start_time = start_time
        self.end_time = end_time
        self.event_stack = sorted(events, key=lambda event: event.time_delta, reverse=True)
        self.agents = {}
        self.operators_by_region = {}
        region_consumers = {}
        for consumer in consumers:
            r = consumer['params']['region']
            if region_consumers.has_key(r):
                region_consumers[r] += 1
            else:
                region_consumers[r] = 1
        region_generators = {}
        agent_id = 1
        for gen_data in generators:
            id = gen_data['id'] if 'id' in gen_data else "Generator %d" % (agent_id) 
            generator = gen_data['type'](id, self, **gen_data['params'])
            if generator.region not in region_generators:
                region_generators[generator.region] = []
            region_generators[generator.region].append(generator)
            self.agents[generator.id] = generator
            agent_id += 1
            
        for cons_data in consumers:
            id = cons_data['id'] if 'id' in cons_data else "Consumer %d" % (agent_id) 
            cons_data['params']['dist_share_func'] = lambda a, t: 1/region_consumers[cons_data['params']['region']]
            consumer = cons_data['type'](id, self, **cons_data['params'])
            self.agents[consumer.id] = consumer
            agent_id += 1
            
        for region in regions:
            operator = AEMOperator('AEMO-%s' % region, self, region)
            self.operators_by_region[region] = operator
            self.agents[operator.id] = operator
            region_data_initialiser = regional_data_initialisers[region]
            operator.initialise(region_generators[region], region_data_initialiser.capacity_data_provider, region_data_initialiser.load_data_provider)
    
    def run(self):
        time = self.start_time
        while time <= self.end_time:
            self.step(time)
            time += timedelta(minutes=AEMOperator.INTERVAL_DURATION_MINUTES)
    
    def step(self, time):
        self.logger.info('<Time: %s>' % time)
        
        #process events
        while len(self.event_stack) > 0 and time >= self.start_time + self.event_stack[-1].time_delta:
            event = self.event_stack.pop()
            event.process_event(self)
            self.logger.info('Processed event: %s' % event)
        
        #process agent communications
        nextTime = set()
        thisTime = set(self.agents.keys())
        while(len(thisTime) > 0):
            for a in thisTime:
                if a in nextTime:
                    nextTime.remove(a)
                nextTime.union(self.agents[a].step(time))
            thisTime = nextTime
        
        for operator in self.operators_by_region.values():
            operator.process_schedule(time)
