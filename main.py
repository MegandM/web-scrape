from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pandas as pd
import yaml
from yaml.loader import SafeLoader
import argparse
from pathlib import Path  
import logging
from typing import List

logging.basicConfig(filename='web-scrape.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

def instantiate_parser():

    parser = argparse.ArgumentParser(description='Web Scraper')
    parser.add_argument('-w', '--website', choices=['nba', 'other'], type=str, required=True,
                        help='an integer for the accumulator')
    parser.add_argument('-fy', '--first_year', type=int, choices=range(1990, 2020), required=True,
                        help='First year from which data should be collected (e.g. 1990)')
    parser.add_argument('-ly', '--last_year', required=True, type=int, choices=range(1990, 2020),
                        help='Last year from which data should be collected (e.g. 2000)')

    return parser.parse_args()

def set_xpath(v_name:str) -> str:
    """
    set xpath given the variable name
    """
    xpath = '//td[@class=""]'
    index = xpath.find('"]')
    completed_xpath = xpath[:index] + v_name + xpath[index:]
    return completed_xpath

def get_url(w:str, yr:int) -> str:
    """
    Add subpath to url containing range of consecutive years
    """
    page_num = str(yr) + '-' + str(yr+1) +'/'
    return w + page_num

class WebDriver:
    def __init__(self, wp:str):
        self.webdriver_path = wp

    def start(self):
        """
        Instantiates webdriver
        """
        self.wd = webdriver.Chrome(self.webdriver_path)
        logging.info('Web Driver started')
        return self.wd
    
    def stop(self):
        """
        Closes webdriver
        """
        self.wd.close()
        logging.info('Web Driver closed')
    
class InspectWeb:
    """
    Inspects website elements via webdriver
    """
    def __init__(self, wd: WebDriver, ws: str) -> None:
        self.webdriver = wd
        self.website = ws
    
    def _open_website(self):
        """
        Opens website
        """
        self.webdriver.get(self.website)
        logging.debug(f'Opening {self.website}')

    def get_list_xpath_values(self, xpath: str) -> List[str]:
        """
        Gets a list of values given an xpath
        """
        self._open_website()

        elements = self.webdriver.find_elements('xpath', xpath)

        elements_list = []
        for p in range(len(elements)):
            elements_list.append(elements[p].text)
        
        return elements_list
    

if __file__ == 'main.py':
    # read config file
    with open('config.yml') as f:
        config = yaml.load(f, Loader = SafeLoader)

    # get arguments
    args = instantiate_parser()
    website = args.website
    first_year = args.first_year
    last_year = args.last_year

    # get common configuration
    webdriver_path = config['webdriver_path']
    custom_config = config[website]

    # set nba outputpath
    nba_filepath = Path(website + '/' + str(first_year) + '-' + str(last_year) + '/results.csv')  
    nba_filepath.parent.mkdir(parents=True, exist_ok=True)  
    
    # start webdriver
    i_wd = WebDriver(wp=webdriver_path)
    wd = i_wd.start()

    # get data according to website name
    
    if website == 'nba':
        #create empty ouput df
        nba_df = pd.DataFrame(columns=['PlayerName','PlayerSalary','Season'])

        for yr in range(first_year,last_year):
            url = get_url(w=custom_config['website'], yr=yr)

            # instantiate web inspection for NBA site
            iw_nba = InspectWeb(wd=wd, ws=url)

            # set xpaths
            players_names_xpath = set_xpath(custom_config['xpath_players_name'])
            players_salaries_xpath = set_xpath(custom_config['xpath_players_salaries'])

            # store players info in lists
            players_names = iw_nba.get_list_xpath_values(players_names_xpath)
            players_salaries = iw_nba.get_list_xpath_values(players_salaries_xpath)

            # store players info in df
            players_tuple = list(zip(players_names[1:],players_salaries[1:]))
            players_season_df = pd.DataFrame(players_tuple, columns=['PlayerName','PlayerSalary'])
            players_season_df['Season'] = yr
            nba_df = pd.concat([nba_df, players_season_df], sort=False)
            logging.debug(f'Concatenated data from {yr}')

        # store data in csv file
        nba_df.to_csv(nba_filepath)
        logging.info(f'Data stored to {nba_filepath}')

    else:
        pass
    
    # stop webdriver
    i_wd.stop()




