'''
This module defines classes for providing data, such as bidding and demand forecasts,
to a simulation. 
'''

from agents import AEMOperator
from messaging import GeneratorDispatchOffer, GeneratorAvailabilityRebid, GeneratorAvailabilityBid
from datetime import datetime, timedelta
from collections import namedtuple
from csv import reader

class CSVPublicYestBidDataProvider(object):
    '''Provides bid data from a specified PUBLIC_YESTBID file, found at
    http://www.nemweb.com.au/REPORTS/CURRENT/Yesterdays_Bids_Reports/'''
    
    FILE_PUBLISH_DATE_FORMAT = '%Y/%m/%d'
    BID_DATE_FORMAT = '%Y/%m/%d %H:%M:%S'
    REPORT_CONTAINER_ROW_ID_CHAR = 'C'
    HEADER_ROW_ID_CHAR = 'I'
    DATA_ROW_ID_CHAR = 'D'
    END_OF_REPORT_STR = 'END OF REPORT'
    TRADING_DAY_OFFER_TYPE = 'BIDDAYOFFER'
    TRADING_INTERVAL_OFFER_TYPE = 'BIDPEROFFER'
    ENERGY_BID_TYPE = 'ENERGY'
    DAILY_OFFER_ENTRY_TYPE = 'DAILY'
    REBID_OFFER_ENTRY_TYPE = 'REBID'
    DEFAULT_OFFER_ENTRY_TYPE = 'DEFAULT'
    
    ROW_ID_INDEX = 0
    END_OF_REPORT_INDEX = 1
    BID_OFFER_TYPE_INDEX = 2
    SETTLEMENT_DATE_INDEX = 4
    DUID_INDEX = 5
    FILE_PUBLISH_DATE_INDEX = 5
    BID_TYPE_INDEX = 6
    BID_SETTLEMENT_DATE_INDEX = 7
    BID_OFFER_DATE_INDEX = 8
    TRADING_INTERVAL_DATE_INDEX = 9
    MAX_AVAILABILITY_INDEX = 10
    RATE_OF_CHANGE_UP_PER_MIN_INDEX = 12
    RATE_OF_CHANGE_DOWN_PER_MIN_INDEX = 13
    REBID_EXPLANATION_INDEX = 12
    PRICE_BAND1_INDEX = 13
    PRICE_BAND10_INDEX = 22
    AVAILABILITY_BAND1_INDEX = 18
    AVAILABILITY_BAND10_INDEX = 27
    PASAAVAILABILITY_INDEX = 28
    BID_VERSION_NO_INDEX = 30
    BID_ENTRY_TYPE_INDEX = 32
        
    def __init__(self, file_location, replace_earliest_offer_if_rebid=True):
        self.file_trading_day_start_date = None
        self.file_trading_day_end_date = None
        self.bid_by_offer_date_by_duid = {} #duid mapped to an offer date mapped to a dispatch offer or availability re-bid.
        
        #maintain a dictionary of duids mapped to a tuple of earliest offer date and earliest dispatch offer
        #this is required in the case where a generator has rebid entries but no daily or default entries in the data file.
        #since a rebid has no pricing info, it becomes necessary to pretend that the earliest rebid is a dispatch offer by
        #replacing it in the bid_by_offer_date_by_duid dictionary (done at the end). 
        #TODO: this is a temporary fix until it can be determined why PUBLIC_YESTBID files contain some generators without
        #daily or default entries.
        earliest_offer_date_and_offer_by_duid = {}
        
        #read each row in the data file
        for row in reader(open(file_location, 'rb')):
            if row[self.ROW_ID_INDEX] == self.REPORT_CONTAINER_ROW_ID_CHAR and row[self.END_OF_REPORT_INDEX] != self.END_OF_REPORT_STR:
                self.file_trading_day_end_date = datetime.strptime(row[self.FILE_PUBLISH_DATE_INDEX], self.FILE_PUBLISH_DATE_FORMAT).replace(hour=AEMOperator.TRADING_DAY_START_HOUR, minute=AEMOperator.TRADING_DAY_START_MINUTE, second=0, microsecond=0)
                self.file_trading_day_start_date = self.file_trading_day_end_date - timedelta(days=1)
            
            elif row[self.ROW_ID_INDEX] == self.DATA_ROW_ID_CHAR:
                if row[self.BID_TYPE_INDEX] == self.ENERGY_BID_TYPE:
                    duid = row[self.DUID_INDEX]
                    bid_offer_date = datetime.strptime(row[self.BID_OFFER_DATE_INDEX], self.BID_DATE_FORMAT).replace(second=0) #strip seconds, since the simulation can't handle that granularity. it is unlikely two bids in a single minute would occur anyway.
                    bid_offer_type = row[self.BID_OFFER_TYPE_INDEX]
                    settlement_date = datetime.strptime(row[self.SETTLEMENT_DATE_INDEX], self.BID_DATE_FORMAT)
                    
                    #if duid == 'MOR3':
                        
                    #is it a row containing daily bid data?
                    if bid_offer_type == self.TRADING_DAY_OFFER_TYPE:
                        bid_entry_type = row[self.BID_ENTRY_TYPE_INDEX]
                        
                        #is it a daily dispatch offer? (i.e. submitted before yesterday's 12:30pm cut-off time)
                        #or is it a default dispatch bid? (i.e. an offer that applies where no daily bid has been made)
                        if bid_entry_type == self.DAILY_OFFER_ENTRY_TYPE or bid_entry_type == self.DEFAULT_OFFER_ENTRY_TYPE:
                            price_per_band = [ float(row[i]) for i in xrange(self.PRICE_BAND1_INDEX, self.PRICE_BAND10_INDEX + 1) ]
                            dispatch_offer = GeneratorDispatchOffer(duid, settlement_date, price_per_band, {})
                            self.bid_by_offer_date_by_duid.setdefault(duid, {})[bid_offer_date] = dispatch_offer
                            
                            if replace_earliest_offer_if_rebid and (duid not in earliest_offer_date_and_offer_by_duid or bid_offer_date < earliest_offer_date_and_offer_by_duid[duid][0]):
                                earliest_offer_date_and_offer_by_duid[duid] = (bid_offer_date, dispatch_offer)
                        
                        #is it an availability rebid? (i.e. submitted after yesterday's 12:30pm cut-off time)
                        elif bid_entry_type == self.REBID_OFFER_ENTRY_TYPE:
                            rebid_explanation = row[self.REBID_EXPLANATION_INDEX]
                            availability_rebid = GeneratorAvailabilityRebid(duid, settlement_date, rebid_explanation, {})
                            self.bid_by_offer_date_by_duid.setdefault(duid, {})[bid_offer_date] = availability_rebid
                            
                            if replace_earliest_offer_if_rebid and (duid not in earliest_offer_date_and_offer_by_duid or bid_offer_date < earliest_offer_date_and_offer_by_duid[duid][0]):
                                #create a dispatch offer in the event that this generator has no daily or default offers. it will replace this rebid.
                                price_per_band = [ float(row[i]) for i in xrange(self.PRICE_BAND1_INDEX, self.PRICE_BAND10_INDEX + 1) ]
                                dispatch_offer = GeneratorDispatchOffer(duid, settlement_date, price_per_band, {})
                                earliest_offer_date_and_offer_by_duid[duid] = (bid_offer_date, dispatch_offer)
                    
                    #is it a row containing availability bid per trading interval data?
                    elif bid_offer_type == self.TRADING_INTERVAL_OFFER_TYPE:
                        availability_per_band = [ float(row[i]) for i in xrange(self.AVAILABILITY_BAND1_INDEX, self.AVAILABILITY_BAND10_INDEX + 1) ]
                        trading_interval_date = datetime.strptime(row[self.TRADING_INTERVAL_DATE_INDEX], self.BID_DATE_FORMAT)
                        max_availability = float(row[self.MAX_AVAILABILITY_INDEX])
                        physical_availability = float(row[self.PASAAVAILABILITY_INDEX])
                        rate_of_change_up_per_min = float(row[self.RATE_OF_CHANGE_UP_PER_MIN_INDEX])
                        rate_of_change_down_per_min = float(row[self.RATE_OF_CHANGE_DOWN_PER_MIN_INDEX])
                        availability_bid = GeneratorAvailabilityBid.TradingIntervalAvailabilityBid(availability_per_band, trading_interval_date, max_availability, physical_availability, rate_of_change_up_per_min, rate_of_change_down_per_min)
                        #add a reference to this trading interval availability bid to the bid at this offer date
                        self.bid_by_offer_date_by_duid[duid][bid_offer_date].availability_bid_by_trading_interval_date[trading_interval_date] = availability_bid
        
        #replace each generator's earliest offer with a dispatch offer if it is a rebid
        #as explained earlier, this is a temporary fix for generators that have no daily or default entries, only rebids
        if replace_earliest_offer_if_rebid:
            for duid,(earliest_offer_date, dispatch_offer) in earliest_offer_date_and_offer_by_duid.items():
                bid_at_earliest_offer_date = self.bid_by_offer_date_by_duid[duid][earliest_offer_date]
                if isinstance(bid_at_earliest_offer_date, GeneratorAvailabilityRebid):
                    #set a reference to the rebid's individual trading interval availability bids
                    dispatch_offer.availability_bid_by_trading_interval_date = bid_at_earliest_offer_date.availability_bid_by_trading_interval_date
                    #replace the rebid with the dispatch offer
                    self.bid_by_offer_date_by_duid[duid][earliest_offer_date] = dispatch_offer
    
    def get_bids_at_offer_date(self, generator_id, offer_date):
        '''Gets all of a generator's dispatch bids and rebids at this offer date.
        Since a PUBLIC_YESTBID file only contains bid data for a single trading day, 
        there is never more than one bid per offer date. But other data providers may 
        provide this functionality, hence a list is returned.'''
        
        if generator_id in self.bid_by_offer_date_by_duid and offer_date in self.bid_by_offer_date_by_duid[generator_id]:
            return [ self.bid_by_offer_date_by_duid[generator_id][offer_date] ]
        else:
            return None
        
    def get_bids_by_offer_date_before_date(self, generator_id, date):
        '''Gets all of a generator's dispatch bids and rebids before a specified offer date,
        returned as a dictionary of offer dates mapped to bids. Since a PUBLIC_YESTBID file 
        only contains bid data for a single trading day, there is never more than one bid 
        per offer date. But other data providers may provide this functionality, hence each 
        offer date key in the dictionary has a list value.'''
        
        if generator_id in self.bid_by_offer_date_by_duid:
            return { offer_date: [ bid ] for offer_date,bid in self.bid_by_offer_date_by_duid[generator_id].items() if offer_date < date }
        else:
            return {}

class CSVPublicPricesDataProvider(object):
    '''Provides pricing and demand data from a specified PUBLIC_PRICES file, found at
    http://www.nemweb.com.au/REPORTS/CURRENT/Public_Prices/'''
    
    DispatchPriceInfo = namedtuple('DispatchPriceInfo', 'price settlement_date total_demand demand_forecast dispatchable_generation dispatchable_load')
    
    FILE_PUBLISH_DATE_FORMAT = '%Y/%m/%d'
    BID_DATE_FORMAT = '%Y/%m/%d %H:%M:%S'
    REPORT_CONTAINER_ROW_ID_CHAR = 'C'
    HEADER_ROW_ID_CHAR = 'I'
    DATA_ROW_ID_CHAR = 'D'
    END_OF_REPORT_STR = 'END OF REPORT'
    DISPATCH_INTERVAL_ROW_TYPE = 'DREGION'
    TRADING_INTERVAL_ROW_TYPE = 'TREGION'
    
    ROW_ID_INDEX = 0
    ROW_TYPE_INDEX = 1
    END_OF_REPORT_INDEX = 1
    FILE_PUBLISH_DATE_INDEX = 5
    REGION_ID_INDEX = 6
    DISPATCH_INTERVAL_DATE_INDEX = 4
    DISPATCH_INTERVAL_PRICE_INDEX = 8
    DISPATCH_INTERVAL_DEMAND_INDEX = 13
    DISPATCH_INTERVAL_DEMAND_FORECAST_INDEX = 14
    DISPATCH_INTERVAL_DISPATCHABLE_GENERATION_INDEX = 15
    DISPATCH_INTERVAL_DISPATCHABLE_LOAD_INDEX = 16
    TRADING_INTERVAL_DATE_INDEX = 4
    TRADING_INTERVAL_SPOT_PRICE_INDEX = 7
    TRADING_INTERVAL_DEMAND_INDEX = 10
    TRADING_INTERVAL_DEMAND_FORECAST_INDEX = 11
    TRADING_INTERVAL_DISPATCHABLE_GENERATION_INDEX = 12
    TRADING_INTERVAL_DISPATCHABLE_LOAD_INDEX = 13
    
    def __init__(self, file_location):
        self.file_trading_day_start_date = None
        self.file_trading_day_end_date = None
        self._price_info_by_dispatch_interval_date_by_region_id = {} #region id mapped to dispatch interval date mapped to demand
        self._price_info_by_trading_interval_date_by_region_id = {} #region id mapped to trading interval date mapped to demand
        
        for row in reader(open(file_location, 'rb')):
            if row[self.ROW_ID_INDEX] == self.REPORT_CONTAINER_ROW_ID_CHAR and row[self.END_OF_REPORT_INDEX] != self.END_OF_REPORT_STR:
                self.file_trading_day_end_date = datetime.strptime(row[self.FILE_PUBLISH_DATE_INDEX], self.FILE_PUBLISH_DATE_FORMAT).replace(hour=AEMOperator.TRADING_DAY_START_HOUR, minute=AEMOperator.TRADING_DAY_START_MINUTE, second=0, microsecond=0)
                self.file_trading_day_start_date = self.file_trading_day_end_date - timedelta(days=1)
            
            elif row[self.ROW_ID_INDEX] == self.DATA_ROW_ID_CHAR:
                region_id = row[self.REGION_ID_INDEX]
                #TODO: refactor below
                if row[self.ROW_TYPE_INDEX] == self.DISPATCH_INTERVAL_ROW_TYPE:
                    dispatch_interval_date = datetime.strptime(row[self.DISPATCH_INTERVAL_DATE_INDEX], self.BID_DATE_FORMAT)
                    interval_price = float(row[self.DISPATCH_INTERVAL_PRICE_INDEX])
                    total_demand = float(row[self.DISPATCH_INTERVAL_DEMAND_INDEX])
                    demand_forecast = float(row[self.DISPATCH_INTERVAL_DEMAND_FORECAST_INDEX])
                    dispatchable_generation = float(row[self.DISPATCH_INTERVAL_DISPATCHABLE_GENERATION_INDEX])
                    dispatchable_load = float(row[self.DISPATCH_INTERVAL_DISPATCHABLE_LOAD_INDEX])
                    dispatch_price_info = self.DispatchPriceInfo(interval_price, dispatch_interval_date, total_demand, demand_forecast, dispatchable_generation, dispatchable_load)
                    self._price_info_by_dispatch_interval_date_by_region_id.setdefault(region_id, {})[dispatch_interval_date] = dispatch_price_info
                
                #un-comment the code below to read trading interval data
                '''
                elif row[self.ROW_TYPE_INDEX] == self.TRADING_INTERVAL_ROW_TYPE:
                    trading_interval_date = datetime.strptime(row[self.TRADING_INTERVAL_DATE_INDEX], self.BID_DATE_FORMAT)
                    spot_price = float(row[self.TRADING_INTERVAL_SPOT_PRICE_INDEX])
                    total_demand = float(row[self.TRADING_INTERVAL_DEMAND_INDEX])
                    demand_forecast = float(row[self.TRADING_INTERVAL_DEMAND_FORECAST_INDEX])
                    dispatchable_generation = float(row[self.TRADING_INTERVAL_DISPATCHABLE_GENERATION_INDEX])
                    dispatchable_load = float(row[self.TRADING_INTERVAL_DISPATCHABLE_LOAD_INDEX])
                    dispatch_price_info = self.DispatchPriceInfo(spot_price, trading_interval_date, total_demand, demand_forecast, dispatchable_generation, dispatchable_load)
                    self._price_info_by_trading_interval_date_by_region_id.setdefault(region_id, {})[trading_interval_date] = dispatch_price_info
                '''

    def get_demand_forecast(self, region_id, dispatch_interval_date):
        '''Gets the demand forecast for 24 hours from the specified dispatch interval date.
        Since this data provider reads PUBLIC_PRICES files with already known and 
        published actual demand data (i.e. not merely forecasts), it 'pretends' to 
        get a demand forecast for 24 hours from the specified interval date, whilst 
        really returning the actual total demand at that time.'''
        dispatch_interval_date += timedelta(days=1)
        if region_id in self._price_info_by_dispatch_interval_date_by_region_id and dispatch_interval_date in self._price_info_by_dispatch_interval_date_by_region_id[region_id]:
            return self._price_info_by_dispatch_interval_date_by_region_id[region_id][dispatch_interval_date].total_demand
        else:
            return None
    
    @property
    def region_ids(self):
        return self._price_info_by_dispatch_interval_date_by_region_id.keys()

class MathApproximationDemandForecastDataProvider(object):
    '''
    This data provider uses mathematical functions to generate demand data that is
    an approximation of the typical daily demand experienced in Victoria (based on 
    observations).
    '''
    
    SECONDS_IN_A_MINUTE = 60
    
    def __init__(self):
        self.funcs = [self._base_demand, self._demand_peaks]
    
    def _base_demand(self, dispatch_interval_date):
        '''Always returns a constant base demand, irrespective of time.'''
        
        return 4000.
    
    def _demand_peaks(self, dispatch_interval_date):
        '''
        Uses formula -.22(x-192)^2+2000 to get a rough approximation of peak demand at 
        a dispatch interval. See http://fooplot.com/index.php?q0=-.22%28x-192%29^2+2000
        '''
        
        first_dispatch_interval_time_today = dispatch_interval_date.replace(hour=AEMOperator.TRADING_DAY_START_HOUR, minute=AEMOperator.DISPATCH_INTERVAL_DURATION_MINUTES)
        time_difference = dispatch_interval_date - first_dispatch_interval_time_today
        dispatch_interval_no = (time_difference.seconds / self.SECONDS_IN_A_MINUTE) / AEMOperator.DISPATCH_INTERVAL_DURATION_MINUTES
        if dispatch_interval_no < 97 or dispatch_interval_no > 287:
            return 0.
        else:
            return -0.22 * (dispatch_interval_no - 192)**2 + 2000
    
    def get_demand_forecast(self, region_id, dispatch_interval_date):
        '''Gets the demand forecast for 24 hours from the specified dispatch 
        interval date.'''
        
        return sum(func(dispatch_interval_date) for func in self.funcs)

class RandomDemandForecastDataProvider(object):
    '''
    This data provider generates random demand data within a specified range.
    '''
    
    def __init__(self, min_demand, max_demand, seed=0):
        assert 0 <= min_demand < max_demand
        import random
        self.rand = random.Random()
        self.rand.seed(seed)
        self.min_demand = float(min_demand)
        self.max_demand = float(max_demand)
    
    def get_demand_forecast(self, region_id, dispatch_interval_date):
        '''Gets the demand forecast for 24 hours from the specified dispatch 
        interval date.'''
        
        return self.rand.uniform(self.min_demand, self.max_demand)