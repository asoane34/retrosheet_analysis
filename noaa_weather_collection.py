import json
import os
from ftplib import FTP
from io import StringIO

FTP_SERVER = 'ftp.ncdc.noaa.gov'
FTP_PATH = 'pub/data/ghcn/daily/all/'
OUTPUT_DIR = 'data/noaa_station_csvs/'
NUM_LINE = 269
SKIP_LINE = 248

with open('data/new_stations.json', 'r') as f:
    all_stations = json.load(f)

class WeatherCollector():
    """ 
    Object to collect weather from NOAA global historical climatology network 
    """
    def __init__(self, station_dict, output_dir, ftp_server = FTP_SERVER, ftp_path = FTP_PATH):
        """ 
        Initialize weather collector object
            Args: 
                - station_dict (dict): A dictionary of weather stations to collect data for, indexed by location.
                - output_dir (str): Path to directory to write csv files containing station weather.
                - ftp_server (str): URL for NOAA FTP server
                - ftp_path (str): Path to directory containing .dly files for all stations in NOAA GHCN. 
            Returns:
                - None
        """
        
        self.ftp_server = ftp_server
        self.ftp_path = ftp_path
        self.station_dict = station_dict
        self.output_dir = output_dir
        self.ftp = None
    
    def collect_weather(self):
        """ 
        Top level method to collect weather for all stations in station_dict
        """
        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir)
        self.connect_to_ftp()
        for key in self.station_dict.keys():
            location_path = self.output_dir + key + '/'
            if not os.path.isdir(location_path):
                os.makedirs(location_path)
            station_list = self.station_dict[key]
            for station in station_list:
                self.scrape_station(station, location_path)
        print('All available stations collected')
        self.ftp.quit()


    def scrape_station(self, station, output_dir):
        """ 
        Retrieve .dly file from FTP and collect data
            Args: 
                - station (str): station ID of the station to be collected
                - output_dir (str): path to directory for each location in station_dict
            Returns:
                - None
        """
        file_name = station + '.dly'
        string = StringIO()
        try:
            self.ftp.retrlines('RETR ' + file_name, string.write)
            aStation = Station(station, string, output_dir)
            aStation.collect_station_data()
            print('Successful Collection {}'.format(station))
        except Exception:
            print('Unable to collect data for {}, {}'.format(station, output_dir))
        string.close()


    def connect_to_ftp(self):
        """ 
        Connect to NOAA FTP and navigate to GHCN directory
        """
        self.ftp = FTP(self.ftp_server)
        check_status = self.ftp.login()
        print(check_status)
        change_dir = self.ftp.cwd(self.ftp_path)
        print(change_dir)


class Station():
    """ 
    Individual station object
    """
    def __init__(self, stationId, string, output_dir):
        """ 
        Initialize station object
            Args: 
                - stationId (str): station ID
                - string (StringIO object): StringIO stream containing contents of .dly file
                - output_dir (str): path to location directory for station
            Returns: 
                - None 
        """
        self.stationId = stationId
        self.string = string
        self.output_dir = output_dir
        self.elements_to_collect = ['TMAX', 'TMIN', 'PRCP', 'SNOW', 'SNWD', 'ACSC', 'ACSH', 'AWND',
        'PSUN', 'WSFG', 'WSFI', 'WSFM', 'WSF1', 'WSF2', 'WSF5']

    def collect_station_data(self):
        """ 
        Parse data from StringIO stream and write to .csv file
        """
        self.string.seek(0)
        current_station_month = None
        current_year = ''
        current_month = ''

        station_file = open(self.output_dir + self.stationId + '.csv', 'w')
        station_file.write('station_id,date,TMAX,TMIN,PRCP,SNOW,SNWD,ACSC,ACSH,AWND,PSUN,WSFG,WSFI,WSFM,WSF1,WSF2,WSF5')
        station_file.write('\n')
        while True:
            id_ = self.string.read(11)
            if not id_:
                break
            
            year = self.string.read(4)
            month = self.string.read(2)
            element = self.string.read(4)

            if element not in self.elements_to_collect:
                self.string.read(SKIP_LINE)
            else:
                pass

            if year != current_year or month != current_month:
                if current_station_month != None:
                    self.write_to_file(current_station_month, station_file)
                else:
                    pass
                current_year = year
                current_month = month

                current_station_month = StationMonth(id_, current_year, current_month)
            else:
                pass
            
            if len(current_station_month.days) == 0:
                while self.string.tell() % NUM_LINE != 0:
                    aDay = Day()
                    value = self.string.read(5)
                    aDay.element_values[element] = value
                    current_station_month.days.append(aDay)
                    self.string.read(3)

            else:
                i = 0
                while self.string.tell() % NUM_LINE != 0:
                    value = self.string.read(5)
                    current_station_month.days[i].element_values[element] = value
                    self.string.read(3)
                    i += 1
        station_file.close()
    
    @staticmethod
    def write_to_file(station_month, file_name):
        """ 
        Factory method to write station months to a .csv file
            Args:
                - station_month (obj): The station month being written to the file
                - file_name (str): Open .csv file being written to
            Returns:
                - None
        """
        day_counter = 1
        for day in station_month.days:
            file_name.write(station_month.stationId)
            file_name.write(',')
            date = '{}-{}-{}'.format(station_month.year, station_month.month, str(day_counter))
            file_name.write(date)
            file_name.write(',')
            file_name.write(day.element_values['TMAX']) if 'TMAX' in day.element_values.keys() else file_name.write('-9999')
            file_name.write(',')
            file_name.write(day.element_values['TMIN']) if 'TMIN' in day.element_values.keys() else file_name.write('-9999')
            file_name.write(',')
            file_name.write(day.element_values['PRCP']) if 'PRCP' in day.element_values.keys() else file_name.write('-9999')
            file_name.write(',')
            file_name.write(day.element_values['SNOW']) if 'SNOW' in day.element_values.keys() else file_name.write('-9999')
            file_name.write(',')
            file_name.write(day.element_values['SNWD']) if 'SNWD' in day.element_values.keys() else file_name.write('-9999')
            file_name.write(',')
            file_name.write(day.element_values['ACSC']) if 'ACSC' in day.element_values.keys() else file_name.write('-9999')
            file_name.write(',')
            file_name.write(day.element_values['ACSH']) if 'ACSH' in day.element_values.keys() else file_name.write('-9999')
            file_name.write(',')
            file_name.write(day.element_values['AWND']) if 'AWND' in day.element_values.keys() else file_name.write('-9999')
            file_name.write(',')
            file_name.write(day.element_values['PSUN']) if 'PSUN' in day.element_values.keys() else file_name.write('-9999')
            file_name.write(',')
            file_name.write(day.element_values['WSFG']) if 'WSFG' in day.element_values.keys() else file_name.write('-9999')
            file_name.write(',')
            file_name.write(day.element_values['WSFI']) if 'WSFI' in day.element_values.keys() else file_name.write('-9999')
            file_name.write(',')
            file_name.write(day.element_values['WSFM']) if 'WSFM' in day.element_values.keys() else file_name.write('-9999')
            file_name.write(',')
            file_name.write(day.element_values['WSF1']) if 'WSF1' in day.element_values.keys() else file_name.write('-9999')
            file_name.write(',')
            file_name.write(day.element_values['WSF2']) if 'WSF2' in day.element_values.keys() else file_name.write('-9999')
            file_name.write(',')
            file_name.write(day.element_values['WSF5']) if 'WSF5' in day.element_values.keys() else file_name.write('-9999')
            file_name.write(',')
            file_name.write('\n')
            day_counter += 1
    
class StationMonth():
    """ 
    NOAA GHCN .dly files are indexed by station month, object for each line in file
    """
    def __init__(self, stationId, year, month):
        """ 
        Initialize StationMonth object
            Args: 
                - stationId (str): station ID
                - year (str): year of data collected
                - month (str): month of data collected
            Returns: 
                - None
        """
        self.stationId = stationId
        self.year = year
        self.month = month
        self.days = []

class Day():
    """ 
    A single day of observations
    """
    def __init__(self):
        self.element_values = {}

if __name__ == '__main__':
    collector = WeatherCollector(all_stations, OUTPUT_DIR)
    collector.collect_weather()