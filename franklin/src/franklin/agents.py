'''
This module contains Franklin's agents.
'''

from message import GenerationAmendment, LoadPrediction, Bid, Dispatch
from datetime import timedelta

class Agent(object):
    '''
    Represents an agent in the NEM system
    This is an *abstract* class.
    '''

    def __init__(self, id, region):
        '''
        Constructs a new "agent" with the given simulation.
        Note that you shouldn't call Agent(sim), you should use
        a subclass.
        '''
        self.id = id
        self.region = region
        
    def step(self, simulation):
        '''
        Abstract method!
        '''
        pass
    
class Generator(Agent):
    '''
    Represents an electical generator, which provides
    power to the NEM and makes money per MWh generated
    '''
    
    def __init__(self, id, region, capacity_data_provider, gen_type=None, markup=1.0):
        super(Generator, self).__init__(id, region)
        assert hasattr(capacity_data_provider, 'get_cost')
        assert hasattr(capacity_data_provider, 'get_capacity')
        self.gen_type = gen_type
        self.capacity_data_provider = capacity_data_provider
        self.markup = markup
    
    def step(self, simulation):
        '''
        At each step, generators fetch their messages from the dispatcher, post
        a bid for this time time_tomorrow and possibly revise their generating 
        capacity for the current period.
        
        Returns a list of agent ids if this Generator requires other agents (or
        itself) to run their step again in this time interval.
        '''
        messages = simulation.message_dispatcher.fetch_messages(self.id)
        #self.simulation.logger.debug("%s: I got %d messages!" % (self.id, len(messages)))
        
        time_tomorrow = simulation.time + timedelta(days=1)
        price = self.capacity_data_provider.get_cost(self, time_tomorrow) * self.markup
        capacity = self.capacity_data_provider.get_capacity(self, time_tomorrow)
        simulation.message_dispatcher.send(Bid(self, time_tomorrow, capacity, price), simulation.operator_by_region[self.region].id)
        
        return []
    

class Consumer(Agent):
    '''
    Represents an electrical consumer, which consumes power from the grid and
    reports (predicted) load data to AEMO
    '''
    
    def __init__(self, id, region, load_data_provider):
        super(Consumer, self).__init__(id, region)
        assert hasattr(load_data_provider, 'get_load')
        self.load_data_provider = load_data_provider
    
    def step(self, simulation):
        '''
        At each step, consumers fetch their messages from the dispatcher, and
        submit an estimate for the load requirements for time_tomorrow
        
        Returns a list of agent ids if this Consumer requires other agents (or
        itself) to run their step again in this time interval.
        '''
        messages = simulation.message_dispatcher.fetch_messages(self.id)
        #self.simulation.logger.debug("%s: I got %d messages!" % (self.id, len(messages)))
        
        time_tomorrow = simulation.time + timedelta(days=1)
        load_tomorrow = self.load_data_provider.get_load(time_tomorrow) * self.dist_share(simulation.consumers_by_region[self.region], time_tomorrow)
        simulation.message_dispatcher.send(LoadPrediction(self, time_tomorrow, load_tomorrow), simulation.operator_by_region[self.region].id)
        
        return []
    
    def dist_share(self, consumers, time):
        return 1 / float(len(consumers))

class AEMOperator(Agent):
    '''
    The AEMOperator agent receives bids from generators and load requirements from
    consumers. It then schedules generators to generate power, based on the best
    cost schedule.
    '''
    
    INTERVAL_DURATION_MINUTES = 5
    INTERVALS_PER_TRADING_PERIOD = 6
    DAILY_TRADING_START_HOUR = 4
    
    def __init__(self, id, region):
        super(AEMOperator, self).__init__(id, region)
        self.bids_by_time = {} #bids stored in a dict. key = time, value = a list of bids for that time.
        self.load_predictions_by_time = {} #load predictions stored in a dict. key = time, value = load prediction for that time.
        self.interval_prices_by_time = {} #interval prices stored in a dict. key = time, value = interval price at that time.
        self.load_supplied_by_time = {} #loads supplied stored in a dict. key = time, value = load supplied at that time.
        
    def initialise(self, simulation, capacity_data_provider, load_data_provider):
        #seed the operator with day zero load and bid data
        time = simulation.start_time
        while time < simulation.start_time + timedelta(days=1):
            for generator in simulation.generators_by_region[self.region]:
                capacity = capacity_data_provider.get_capacity(generator, time)
                price = capacity_data_provider.get_cost(generator, time)
                self._handle_bid(Bid(generator, time, capacity, price * generator.markup))
            self._handle_load_prediction(LoadPrediction(None, time, load_data_provider.get_load(time)))
            time += timedelta(minutes=self.INTERVAL_DURATION_MINUTES)
    
    def process_schedule(self, simulation):
        simulation.logger.info("%s's schedule:" % self.id)
        if simulation.time in self.load_predictions_by_time and simulation.time in self.bids_by_time:
            #get the load and bids for this interval
            total_load = sum(load_prediction.watts for load_prediction in self.load_predictions_by_time[simulation.time])
            bids = self.bids_by_time[simulation.time]
            
            #determine which generators get dispatched for this interval based on their price
            simulation.logger.info(" * Generators dispatched:")
            total_load_supplied = 0
            for bid in sorted(bids, key=lambda bid: bid.price):
                load_to_supply = min(bid.watts, total_load - total_load_supplied)
                total_load_supplied += load_to_supply
                simulation.logger.info("   * %s for %dMW" % (bid.sender.id, load_to_supply))
                simulation.message_dispatcher.send(Dispatch(self, simulation.time, load_to_supply), bid.sender.id)
                if total_load_supplied >= total_load:
                    break
            
            simulation.logger.info(" * Total load supplied: %dMW of %dMW (%.2f%%)" % (total_load_supplied, total_load, (100*total_load_supplied / total_load)))
            self.load_supplied_by_time[simulation.time] = total_load_supplied
            
            simulation.logger.info(" * Interval price: $%.2f" % bid.price)
            self.interval_prices_by_time[simulation.time] = bid.price
            
            #calculate the spot price (average interval price) if this is the last interval in the trading period
            if (simulation.time.minute / self.INTERVAL_DURATION_MINUTES) % self.INTERVALS_PER_TRADING_PERIOD == 0:
                interval_prices = set()
                sufficient_interval_prices = True
                for i in range(self.INTERVALS_PER_TRADING_PERIOD):
                    interval_time = simulation.time - timedelta(minutes=self.INTERVAL_DURATION_MINUTES * i)
                    if interval_time in self.interval_prices_by_time:
                        interval_prices.add(self.interval_prices_by_time[interval_time])
                    else:
                        sufficient_interval_prices = False
                        break
                        
                if sufficient_interval_prices:
                    spot_price = sum(interval_prices) / self.INTERVALS_PER_TRADING_PERIOD
                    simulation.logger.info(" * Trading period finished, spot price: $%.2f" % spot_price)
                else:
                    simulation.logger.info(" * Trading period %d finished, insufficient interval price data to calculate spot price" % (simulation.time.minute / self.INTERVALS_PER_TRADING_PERIOD))
        else:
            simulation.logger.info("No load and/or bid data for this time interval.")
            
    
    def step(self, simulation):
        messages = simulation.message_dispatcher.fetch_messages(self.id)
        #simulation.logger.debug("%s: I got %d messages!" % (self.id, len(messages)))
        for message in messages:
            if isinstance(message, Bid):
                self._handle_bid(message)
            elif isinstance(message, GenerationAmendment):
                self._handle_generation_amendment(message)
            elif isinstance(message, LoadPrediction):
                self._handle_load_prediction(message)
            else:
                #unrecognised!
                self.simulation.logger.warning("%s received unknown message type, " % (self.id) + type(message))
            
        return []
    
    def _handle_generation_amendment(self, generation_amendment):
        pass
    
    def _handle_bid(self, bid):
        self.bids_by_time.setdefault(bid.time, set()).add(bid)
    
    def _handle_load_prediction(self, load_prediction):
        self.load_predictions_by_time.setdefault(load_prediction.time, set()).add(load_prediction)