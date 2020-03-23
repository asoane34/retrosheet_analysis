from dataclasses import dataclass, field
from random import choice
import requests
from requests import HTTPError, RequestException
from bs4 import BeautifulSoup
import sys
import os
import pandas as pd 
import json

USER_AGENT = [
    r"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"
]

CONSTANTS = r"https://www.fangraphs.com/guts.aspx?type=cn"

CONSTANT_JSON = r"./adv_metrics/wOBA_weights.json"

@dataclass
class FanGraphScraper():
    user_agents: list = None
    proxy: str = None
    constant_url: str = CONSTANTS
    constant_table: list = field(default_factory = list)
    output_file: str = CONSTANT_JSON

    def scrape_constants(self):

        constants_page = self.request_URL(self.constant_url)

        constants_soup = BeautifulSoup(constants_page, "html.parser")

        table = constants_soup.find("table", {"class" : "rgMasterTable"})

        table_header = table.find("thead").find("tr")

        header = [i.get_text() for i in table_header.findAll("th")]

        all_rows = table.findAll("tr", {"class" : "rgRow"}) + table.findAll("tr", {"class" : "rgAltRow"})

        for row in all_rows:
            
            d = {}
            
            row_text = [i.get_text() for i in row.findAll("td")]
            
            for k in range(len(header)):
                
                d[header[k]] = row_text[k]
                
            self.constant_table.append(d)

        with open(self.output_file, "w+") as f:

            json.dump(self.constant_table, f)

        print("Successfully written to JSON")

    def random_agent(self):
        
        if self.user_agents and isinstance(self.user_agents, list):
        
            return(choice(self.user_agents))

        return(choice(USER_AGENT))

    def request_URL(self, url):

        agent = self.random_agent()

        try:

            response = requests.get(url, headers = {

                "User-Agent" : agent

            },

            proxies = {

                "http" : self.proxy,

                "https" : self.proxy
            })

            response.raise_for_status()

        except HTTPError:

            raise

        except RequestException:

            raise

        else:

            return(response.content)

if __name__ == "__main__":

    scraper = FanGraphScraper()

    scraper.scrape_constants()

