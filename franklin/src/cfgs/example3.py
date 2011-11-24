from franklin.data_providers import CSVPublicPricesDataProvider, CSVPublicYestBidDataProvider
from franklin.data_monitors import CSVFileMonitor
from franklin.agents import AEMOperator, GeneratorWithBidDataProvider, ConsumerWithDemandForecastDataProvider
from franklin.messaging import GeneratorAvailabilityBid, GeneratorAvailabilityRebid, GeneratorDispatchOffer
from csv import reader
from datetime import datetime, timedelta

'''
EXAMPLE USAGE: python main.py -c cfgs/example3
'''

bid_data_provider = CSVPublicYestBidDataProvider('../data/PUBLIC_YESTBID_201110040000_20111005040507.csv')

demand_forecast_data_provider = CSVPublicPricesDataProvider('../data/PUBLIC_PRICES_201110040000_20111005040503.csv')

generators_by_duid = {}
for row in reader(open('../data/registered-generators.csv', 'rb')):
    if row[3] == 'Generator' and row[4] == 'Market' and row[5] == 'Scheduled':
        duid = row[13]
        region_id = row[2]
        generators_by_duid[duid] = GeneratorWithBidDataProvider(duid, region_id, bid_data_provider)

#create a dispatch offer for BLOWERNG (a NSW generator)
offer = GeneratorDispatchOffer('BLOWERNG', 
                                bid_data_provider.start_date.replace(hour=AEMOperator.TRADING_DAY_SETTLEMENT_HOUR, minute=AEMOperator.TRADING_DAY_SETTLEMENT_MINUTE),
                                price_per_band=[-1150.0,-5.0,8.0,12.0,17.0,23.0,30.0,32.0,36.0,40.0])
#the offer will be submitted at 12:29pm of the previous day
generators_by_duid['BLOWERNG'].custom_bids_by_offer_date[(bid_data_provider.start_date - timedelta(days=1)).replace(hour=12, minute=29)] = [ offer ]

#create a re-bid for TALWA1 (a NSW generator)
bid_by_trading_interval_date = {}
#create an availability bid for the trading interval ending at 4:30am
bid_by_trading_interval_date[bid_data_provider.start_date.replace(hour=4, minute=30)] = GeneratorAvailabilityBid.TradingIntervalAvailabilityBid(availability_per_band=[2500,0,0,0,0,0,0,0,0,0])
#create an availability bid for the trading interval ending at 5:00am
bid_by_trading_interval_date[bid_data_provider.start_date.replace(hour=5, minute=0)] = GeneratorAvailabilityBid.TradingIntervalAvailabilityBid(availability_per_band=[4500,0,0,0,0,0,0,0,0,0])
#create an availability bid for the trading interval ending at 5:30am
bid_by_trading_interval_date[bid_data_provider.start_date.replace(hour=5, minute=30)] = GeneratorAvailabilityBid.TradingIntervalAvailabilityBid(availability_per_band=[6500,500,0,0,0,0,0,0,0,0])
#create an availability re-bid to store the individual trading interval bids
rebid = GeneratorAvailabilityRebid('TALWA1', 
                                    bid_data_provider.start_date.replace(hour=AEMOperator.TRADING_DAY_SETTLEMENT_HOUR, minute=AEMOperator.TRADING_DAY_SETTLEMENT_MINUTE),
                                    availability_bid_by_trading_interval_date=bid_by_trading_interval_date)
#the re-bid will be submitted at 3:00am
generators_by_duid['TALWA1'].custom_bids_by_offer_date[bid_data_provider.start_date.replace(hour=3, minute=0)] = [ rebid ]

consumers = set()
for region_id in demand_forecast_data_provider.region_ids:
    consumers.add(ConsumerWithDemandForecastDataProvider('Consumer-%s' % region_id, region_id, demand_forecast_data_provider))

config = {
    'start_date': bid_data_provider.start_date,
    'end_date': bid_data_provider.end_date,
    'generators': generators_by_duid.values(),
    'consumers': consumers,
    'regions': demand_forecast_data_provider.region_ids,
    'data_monitor': CSVFileMonitor(file_location='../results/example3.csv'),
}
            