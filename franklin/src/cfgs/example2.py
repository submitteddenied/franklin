from franklin.data_providers import MathApproximationDemandForecastDataProvider, RandomDemandForecastDataProvider, CSVPublicYestBidDataProvider
from franklin.data_monitors import CSVFileMonitor
from franklin.agents import GeneratorWithBidDataProvider, ConsumerWithDemandForecastDataProvider
from csv import reader

'''
EXAMPLE USAGE: python main.py -c cfgs/example2
'''

bid_data_provider = CSVPublicYestBidDataProvider('../data/PUBLIC_YESTBID_201110040000_20111005040507.csv')

generators = set()
for row in reader(open('../data/registered-generators.csv', 'rb')):
    if row[3] == 'Generator' and row[4] == 'Market' and row[5] == 'Scheduled':
        duid = row[13]
        region_id = row[2]
        generators.add(GeneratorWithBidDataProvider(duid, region_id, bid_data_provider))

consumers = [ ConsumerWithDemandForecastDataProvider('VIC-Consumer 1', 'VIC1', MathApproximationDemandForecastDataProvider()),
              ConsumerWithDemandForecastDataProvider('NSW-Consumer 1', 'NSW1', RandomDemandForecastDataProvider(500, 1000)), 
              ConsumerWithDemandForecastDataProvider('NSW-Consumer 2', 'NSW1', RandomDemandForecastDataProvider(800, 1500)),
              ConsumerWithDemandForecastDataProvider('NSW-Consumer 3', 'NSW1', RandomDemandForecastDataProvider(1200, 2000)),
              ConsumerWithDemandForecastDataProvider('NSW-Consumer 4', 'NSW1', RandomDemandForecastDataProvider(1500, 2500)),  ]

config = {
    'start_date': bid_data_provider.start_date,
    'end_date': bid_data_provider.end_date,
    'generators': generators,
    'consumers': consumers,
    'regions': [ 'VIC1', 'NSW1' ],
    'data_monitor': CSVFileMonitor(file_location='../results/example2.csv'),
}
            