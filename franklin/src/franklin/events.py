'''
This module defines event classes that can be activated at specific times within
a simulation, modifying and manipulating the the simulation in some manner.
'''

class SimulationEvent(object):
    '''Provides a basic skeleton for event classes to inherit from.'''
    
    def __init__(self, name, time_delta):
        self.name = name
        self.time_delta = time_delta #the relative time difference from the start time of the simulation
    
    def process_event(self, simulation):
        '''Activates and runs the event, modifying the specified simulation
        in some manner.'''
        pass

    def __str__(self):
        return "<Event: %s>" % self.name

class ChangeConsumerDemandForecastDataProviderEvent(SimulationEvent):
    '''
    An event that changes the demand forecast data provider for consumers in a region. 
    Only operates on consumers that have a demand_forecast_data_provider attribute
    (e.g. the ConsumerWithDemandForecastDataProvider type).
    '''
    
    def __init__(self, time_delta, demand_forecast_data_provider, region_id):
        super(ChangeConsumerDemandForecastDataProviderEvent, self).__init__('Change Consumer Demand Forecast Data Provider (value=%s)', time_delta)
        self.demand_forecast_data_provider = demand_forecast_data_provider
        self.region_id = region_id
    
    def process_event(self, simulation):
        '''Replaces the demand forecast data provider for consumers
        that use one in this region.'''
        
        for consumer in simulation.consumers_by_region[self.region_id]:
            if hasattr(consumer, 'demand_forecast_data_provider'):
                consumer.demand_forecast_data_provider = self.demand_forecast_data_provider