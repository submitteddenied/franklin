from franklin.data_providers import CSVPublicPricesDataProvider, CSVPublicYestBidDataProvider
from franklin.monitors import CSVFileMonitor
from franklin.agents import GeneratorWithBidDataProvider, ConsumerWithDemandForecastDataProvider
from csv import reader

'''
EXAMPLE USAGE: python main.py -c cfgs/example1
'''

csv_bid_data_provider = CSVPublicYestBidDataProvider('../data/PUBLIC_YESTBID_201110040000_20111005040507.csv')

csv_demand_forecast_data_provider = CSVPublicPricesDataProvider('../data/PUBLIC_PRICES_201110040000_20111005040503.csv')

generators = set()
for row in reader(open('../data/registered-generators.csv', 'rb')):
    if row[3] == 'Generator' and row[4] == 'Market' and row[5] == 'Scheduled':
        duid = row[13]
        region_id = row[2]
        fuel_source = row[6]
        generators.add(GeneratorWithBidDataProvider(duid, region_id, csv_bid_data_provider, fuel_source))

consumers = set()
for region_id in csv_demand_forecast_data_provider.region_ids:
    consumers.add(ConsumerWithDemandForecastDataProvider('Consumer-%s' % region_id, region_id, csv_demand_forecast_data_provider))

config = {
    'start_date': csv_bid_data_provider.file_trading_day_start_date,
    'end_date': csv_bid_data_provider.file_trading_day_end_date,
    'generators': generators,
    'consumers': consumers,
    'regions': csv_demand_forecast_data_provider.region_ids,
    'monitor': CSVFileMonitor(file_location='results/example1.csv'),
}
            