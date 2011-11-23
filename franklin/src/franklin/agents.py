'''
This module provides agents, such as generators and consumers, to 
a simulation. An agent requires three functions to be used within a 
simulation: get_initialisation_times(), step(), and handle_messages()
(and therefore does not necessarily need to subclass Agent).
'''

from messaging import GeneratorDispatchOffer, GeneratorAvailabilityRebid, DemandForecast, GeneratorDispatchNotification
from datetime import timedelta
from collections import namedtuple

class Agent(object):
    '''
    Represents an agent/participant within the energy market. 
    This is a skeleton class which has the necessary functions
    defined for use within a simulation.
    '''

    def __init__(self, id, region_id):
        self.id = id
        self.region_id = region_id
    
    def get_initialisation_times(self, simulation):
        '''Gets the dates and times required for this agent's step()
        function to be called in order to initialise the agent within 
        the market prior to a simulation commencing.'''
        pass
       
    def step(self, simulation):
        '''Execute the agent at this time in the simulation.'''
        pass
    
    def handle_messages(self, simulation, messages):
        '''Process messages received from other agents.'''
        pass
    
class GeneratorWithBidDataProvider(Agent):
    '''
    Represents an electical generator, which provides power to the NEM and makes 
    money per MWh generated. This type of generator has no decision making 
    abilities; it uses a bid data provider to determine what bids to make.
    '''
    
    def __init__(self, id, region_id, bid_data_provider, gen_type=None):
        super(GeneratorWithBidDataProvider, self).__init__(id, region_id)
        assert hasattr(bid_data_provider, 'get_bids_at_offer_date')
        assert hasattr(bid_data_provider, 'get_bids_by_offer_date_before_date')
        self.gen_type = gen_type
        self.bid_data_provider = bid_data_provider
    
    def get_initialisation_times(self, simulation):
        '''Returns the offer dates of all bids before the simulation start date.'''
        
        return self.bid_data_provider.get_bids_by_offer_date_before_date(self.id, simulation.start_date).keys()
    
    def step(self, simulation):
        '''
        Each time step, this generator gets any dispatch offers and rebids to submit
        at this time, and sends them as messages to the regional market operator.
        '''
        
        bids = self.bid_data_provider.get_bids_at_offer_date(self.id, simulation.time)
        if bids:
            for bid in bids:
                simulation.message_dispatcher.send(bid, simulation.time, simulation.operator_by_region[self.region_id].id)
        
    def handle_messages(self, simulation, messages):
        pass
        for message in messages:
            if isinstance(message, GeneratorDispatchNotification):
                simulation.logger.info("%s: Received notification from %s to dispatch for %.2fMW" % (self.id, message.sender_id, message.demand_to_supply))
                
        
class ConsumerWithDemandForecastDataProvider(Agent):
    '''
    Represents an electrical consumer that consumes power from the grid and
    reports predicted demand for the day ahead to the regional market operator. 
    This type of consumer uses a demand forecast data provider to determine demand 
    predictions.
    '''
    
    def __init__(self, id, region_id, demand_forecast_data_provider):
        super(ConsumerWithDemandForecastDataProvider, self).__init__(id, region_id)
        assert hasattr(demand_forecast_data_provider, 'get_demand_forecast')
        self.demand_forecast_data_provider = demand_forecast_data_provider
        
    def get_initialisation_times(self, simulation):
        '''Returns 24 hours worth of dispatch interval times for the day before the simulation start date.
        This will be required to seed the simulation's first trading day with a demand forecast per 
        dispatch interval.'''
        
        initialisation_times = set()
        time = simulation.start_date - timedelta(days=1)
        while time < simulation.start_date:
            initialisation_times.add(time)
            time += timedelta(minutes=AEMOperator.DISPATCH_INTERVAL_DURATION_MINUTES)
        return initialisation_times
    
    def step(self, simulation):
        '''
        Each time step, this consumer gets its forecasted demand for 24 hours
        from the current trading interval time, and send it as a message to the 
        regional market operator.
        '''
        
        if simulation.time.minute % AEMOperator.DISPATCH_INTERVAL_DURATION_MINUTES == 0:
            demand_forecast_tomorrow = self.demand_forecast_data_provider.get_demand_forecast(self.region_id, simulation.time)
            if demand_forecast_tomorrow:
                simulation.message_dispatcher.send(DemandForecast(self.id, simulation.time + timedelta(days=1), demand_forecast_tomorrow), simulation.time, simulation.operator_by_region[self.region_id].id)
    
    def handle_messages(self, simulation, messages):
        pass

class AEMOperator(Agent):
    '''
    The AEMOperator agent receives bids from generators and demand/load requirements from
    consumers. Each dispatch interval it schedules generators to generate power, based on 
    the best price schedule to meet the demand.
    '''

    DispatchIntervalInfo = namedtuple('DispatchIntervalInfo', 'price total_demand_supplied total_demand price_band_no generator_ids_dispatched')
    TradingIntervalInfo = namedtuple('TradingIntervalInfo', 'spot_price total_demand_supplied total_demand generator_ids_dispatched')
    
    DISPATCH_INTERVAL_DURATION_MINUTES = 5
    DISPATCH_INTERVALS_PER_TRADING_INTERVAL = 6
    SECOND_HOURLY_TRADING_INTERVAL_END_MINUTE = 0
    FIRST_HOURLY_TRADING_INTERVAL_END_MINUTE = 30
    TRADING_DAY_SETTLEMENT_HOUR = 0
    TRADING_DAY_SETTLEMENT_MINUTE = 0
    TRADING_DAY_START_HOUR = 4
    TRADING_DAY_START_MINUTE = 0
    DAILY_DISPATCH_OFFER_CUTOFF_HOUR = 12
    DAILY_DISPATCH_OFFER_CUTOFF_MINUTE = 30
    MARKET_PRICE_CAP = 12500.
    MARKET_FLOOR_CAP = -1000.
    NUM_PRICE_BANDS = 10
    
    def __init__(self, id, region):
        super(AEMOperator, self).__init__(id, region)
        self._dispatch_offer_by_settlement_date_by_generator_id = {} #generator ids mapped to settlement dates mapped to a dispatch offer
        self._demand_forecasts_by_dispatch_interval_date = {} #demand forecasts stored in a dict. key = date, value = demand forecast for that date.
        self.dispatch_interval_info_by_date = {} #dispatch interval information stored in a dict. key = date, value = dispatch interval information at that date.
        self.trading_interval_info_by_date = {} #trading interval information stored in a dict. key = date, value = trading interval information at that date.
    
    def get_initialisation_times(self, simulation):
        return []
    
    def step(self, simulation, schedule_before_simulation_start=False):
        '''Each time step, this agent processes its dispatch schedule if
        the simulation time is currently at a dispatch interval.'''
        
        if (simulation.time >= simulation.start_date or schedule_before_simulation_start) and simulation.time.minute % self.DISPATCH_INTERVAL_DURATION_MINUTES == 0:
            self._process_dispatch_schedule(simulation)
    
    def _process_dispatch_schedule(self, simulation):
        '''Determines which generators to dispatch at this dispatch interval to meet the 
        consumer demand/load using a stack-based pricing model (i.e. generators are dispatched 
        in order of lowest price).'''        
        
        if simulation.time in self._demand_forecasts_by_dispatch_interval_date:
            #determine the current trading interval's end date #FIXME: a bit excessive calling this every dispatch interval. needs refactoring too.
            if 0 < simulation.time.minute <= self.FIRST_HOURLY_TRADING_INTERVAL_END_MINUTE:
                current_trading_interval_end_date = simulation.time.replace(minute=self.FIRST_HOURLY_TRADING_INTERVAL_END_MINUTE)
            elif simulation.time.minute == self.SECOND_HOURLY_TRADING_INTERVAL_END_MINUTE:
                current_trading_interval_end_date = simulation.time
            else:
                current_trading_interval_end_date = simulation.time.replace(minute=self.SECOND_HOURLY_TRADING_INTERVAL_END_MINUTE) + timedelta(hours=1)
            
            #determine the trading day's settlement date (used to get today's bids)
            trading_day_settlement_date = simulation.time.replace(hour=self.TRADING_DAY_SETTLEMENT_HOUR, minute=self.TRADING_DAY_SETTLEMENT_MINUTE)
            if simulation.time.hour < self.TRADING_DAY_START_HOUR or (simulation.time.hour == self.TRADING_DAY_START_HOUR and simulation.time.minute == 0):
                trading_day_settlement_date -= timedelta(days=1)
            
            #using the settlement date, get all price offers submitted for this trading day
            dispatch_offers = set()
            for generator in self._dispatch_offer_by_settlement_date_by_generator_id:
                if trading_day_settlement_date in self._dispatch_offer_by_settlement_date_by_generator_id[generator]:
                    dispatch_offers.add(self._dispatch_offer_by_settlement_date_by_generator_id[generator][trading_day_settlement_date])
            
            #get the total demand for this dispatch interval
            total_demand = sum(demand_forecast.demand for demand_forecast in self._demand_forecasts_by_dispatch_interval_date[simulation.time])
            
            #using stack-based pricing, determine the dispatch schedule for generators
            total_demand_supplied = 0.
            dispatch_interval_price = 0.
            demand_generated_by_duid = {} #maps a generator id to the demand it will be dispatched to generate
            for price_band_no in xrange(self.NUM_PRICE_BANDS):
                total_demand_supplied = 0.
                dispatch_interval_price = 0.
                demand_generated_by_duid.clear()
                #determine which generators get dispatched for this interval based on their price
                for dispatch_offer in sorted(dispatch_offers, key=lambda dispatch_offer: dispatch_offer.price_per_band[price_band_no]):
                    availability_bid = dispatch_offer.availability_bid_by_trading_interval_date[current_trading_interval_end_date]
                    #availability = availability_bid.availability_per_band[price_band_no]
                    availability = sum(availability_bid.availability_per_band[:price_band_no+1])
                    #availability = min(sum(availability_bid.availability_per_band[:price_band_no+1]), availability_bid.max_availability)
                    if availability > 0:
                        demand_to_supply = min(availability, total_demand - total_demand_supplied)
                        total_demand_supplied += demand_to_supply
                        demand_generated_by_duid[dispatch_offer.sender_id] = demand_to_supply
                        dispatch_interval_price = dispatch_offer.price_per_band[price_band_no]
                        if total_demand_supplied >= total_demand:
                            break
                    else:
                        #FIXME: what to do here?
                        pass
                
                if total_demand_supplied >= total_demand:
                    break
            
            #send dispatch notifications
            for duid,demand_to_generate in demand_generated_by_duid.items():
                simulation.message_dispatcher.send(GeneratorDispatchNotification(self.id, simulation.time, demand_to_generate), simulation.time, duid)
            
            #store information for this dispatch interval date
            self.dispatch_interval_info_by_date[simulation.time] = self.DispatchIntervalInfo(price=dispatch_interval_price, total_demand_supplied=total_demand_supplied, 
                                                                                                    total_demand=total_demand, price_band_no=price_band_no, 
                                                                                                    generator_ids_dispatched=demand_generated_by_duid.keys())
            
            simulation.logger.info("%s: Dispatch interval schedule -> demand supplied = %.2fMW of %.2fMW, price = $%.2f (band %d)" % (self.id, total_demand_supplied, total_demand, dispatch_interval_price, price_band_no))
            
            #calculate the spot price (average dispatch interval price) if this is the last dispatch interval in the trading interval
            if simulation.time.minute == self.SECOND_HOURLY_TRADING_INTERVAL_END_MINUTE or simulation.time.minute == self.FIRST_HOURLY_TRADING_INTERVAL_END_MINUTE:
                dispatch_interval_infos = []
                for i in xrange(self.DISPATCH_INTERVALS_PER_TRADING_INTERVAL):
                    dispatch_interval_time = simulation.time - timedelta(minutes=self.DISPATCH_INTERVAL_DURATION_MINUTES * i)
                    if dispatch_interval_time in self.dispatch_interval_info_by_date:
                        dispatch_interval_infos.append(self.dispatch_interval_info_by_date[dispatch_interval_time])
                    else:
                        break
                
                if len(dispatch_interval_infos) == self.DISPATCH_INTERVALS_PER_TRADING_INTERVAL:
                    #calculate trading interval info
                    spot_price = 0.
                    total_demand_supplied = 0.
                    total_demand = 0.
                    generator_ids_dispatched = set()
                    for dispatch_interval_info in dispatch_interval_infos:
                        spot_price += dispatch_interval_info.price
                        total_demand_supplied += dispatch_interval_info.total_demand_supplied
                        total_demand += dispatch_interval_info.total_demand
                        generator_ids_dispatched.update(dispatch_interval_info.generator_ids_dispatched)
                    spot_price = max(self.MARKET_FLOOR_CAP, min(self.MARKET_PRICE_CAP, spot_price / self.DISPATCH_INTERVALS_PER_TRADING_INTERVAL))
                    
                    #store information for this trading interval date
                    self.trading_interval_info_by_date[simulation.time] = self.TradingIntervalInfo(spot_price=spot_price, total_demand_supplied=total_demand_supplied, 
                                                                                                   total_demand=total_demand, generator_ids_dispatched=generator_ids_dispatched)
                    simulation.logger.info("%s: Trading interval finished -> spot price = $%.2f" % (self.id, spot_price))
                else:
                    simulation.logger.info("%s: Trading interval %d finished; insufficient dispatch interval information to calculate spot price." % (self.id, simulation.time.minute / self.DISPATCH_INTERVALS_PER_TRADING_INTERVAL))
        else:
            simulation.logger.info("%s: No load and/or bid data for this trading interval." % self.id)
    
    def handle_messages(self, simulation, messages):
        for message in messages:
            if isinstance(message, GeneratorDispatchOffer):
                self._handle_dispatch_offer(message, simulation)
            elif isinstance(message, GeneratorAvailabilityRebid):
                self._handle_availability_rebid(message, simulation)
            elif isinstance(message, DemandForecast):
                self._handle_demand_forecast(message, simulation)
            else:
                #unrecognised!
                simulation.logger.warning("%s: received unknown message type (%s)." % (self.id, type(message)))
    
    def _handle_dispatch_offer(self, dispatch_offer, simulation):
        cut_off_date = (dispatch_offer.settlement_date - timedelta(days=1)).replace(hour=self.DAILY_DISPATCH_OFFER_CUTOFF_HOUR, minute=self.DAILY_DISPATCH_OFFER_CUTOFF_MINUTE)
        if simulation.time < cut_off_date:
            self._dispatch_offer_by_settlement_date_by_generator_id.setdefault(dispatch_offer.sender_id, {})[dispatch_offer.settlement_date] = dispatch_offer
            simulation.logger.info('%s: Received dispatch offer from %s.' % (self.id, dispatch_offer.sender_id))
        else:
            simulation.logger.info('%s: Rejected dispatch offer from %s (received after daily cut-off time).' % (self.id, dispatch_offer.sender_id))
    
    def _handle_availability_rebid(self, availability_rebid, simulation):
        #TODO: AEMO needs to reject any availability re-bids for a trading interval less than 5 minutes away
        if availability_rebid.sender_id in self._dispatch_offer_by_settlement_date_by_generator_id and \
           availability_rebid.settlement_date in self._dispatch_offer_by_settlement_date_by_generator_id[availability_rebid.sender_id]:
            #replace the dispatch offer's reference to the availability bids per trading interval
            self._dispatch_offer_by_settlement_date_by_generator_id[availability_rebid.sender_id][availability_rebid.settlement_date].availability_bid_by_trading_interval_date = availability_rebid.availability_bid_by_trading_interval_date
            simulation.logger.info('%s: Received availability re-bid from %s for trading day %s. Explanation: %s' % (self.id, availability_rebid.sender_id, availability_rebid.settlement_date, availability_rebid.rebid_explanation))
        else:
            simulation.logger.info('%s: Rejected availability re-bid from %s for trading day %s (no original dispatch offer received for this trading day).' % (self.id, availability_rebid.settlement_date, availability_rebid.sender_id))

    def _handle_demand_forecast(self, demand_forecast, simulation):
        self._demand_forecasts_by_dispatch_interval_date.setdefault(demand_forecast.dispatch_interval_date, set()).add(demand_forecast)
            