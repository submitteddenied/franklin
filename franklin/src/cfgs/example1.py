from franklin.data_providers import CSVPublicPricesDataProvider, CSVPublicYestBidDataProvider
from franklin.data_monitors import CSVFileMonitor
from franklin.agents import GeneratorWithBidDataProvider, ConsumerWithDemandForecastDataProvider
from csv import reader

'''
EXAMPLE USAGE: python main.py -c cfgs/example1
'''

bid_data_provider = CSVPublicYestBidDataProvider('../data/PUBLIC_YESTBID_201110040000_20111005040507.csv')

demand_forecast_data_provider = CSVPublicPricesDataProvider('../data/PUBLIC_PRICES_201110040000_20111005040503.csv')

generators = set()
for row in reader(open('../data/registered-generators.csv', 'rb')):
    if row[3] == 'Generator' and row[4] == 'Market' and row[5] == 'Scheduled':
        duid = row[13]
        region_id = row[2]
        generators.add(GeneratorWithBidDataProvider(duid, region_id, bid_data_provider))

consumers = set()
for region_id in demand_forecast_data_provider.region_ids:
    consumers.add(ConsumerWithDemandForecastDataProvider('Consumer-%s' % region_id, region_id, demand_forecast_data_provider))

config = {
    'start_date': bid_data_provider.start_date,
    'end_date': bid_data_provider.end_date,
    'generators': generators,
    'consumers': consumers,
    'regions': demand_forecast_data_provider.region_ids,
    'data_monitor': CSVFileMonitor(file_location='../results/example1.csv'),
}
            