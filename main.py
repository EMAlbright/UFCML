from dataclasses import dataclass
import re
from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests

class WEIGHT_CLASSES:
    FLYWEIGHT = "Flyweight"
    BANTAMWEIGHT = "Bantamweight"
    FEATHERWEIGHT = "Featherweight"
    LIGHTWEIGHT = "Lightweight"
    WELTERWEIGHT = "Welterweight"
    MIDDLEWEIGHT = "Middleweight"
    LIGHT_HEAVYWEIGHT = "Light Heavyweight"
    HEAVYWEIGHT = "Heavyweight"
    WOMENS_STRAWWEIGHT = "Women's Strawweight"
    WOMENS_FLYWEIGHT = "Women's Flyweight"
    WOMENS_BANTAMWEIGHT = "Women's Bantamweight"

@dataclass
class FighterPhysicalStats:
    height_inches: float
    weight_lbs: float
    reach_inches: float
    stance: str
    dob: datetime

@dataclass
class Fighter:
    name: str
    wins: int
    losses: int
    physical_stats: FighterPhysicalStats
    #Significant Strikes Landed per Minute
    slpm: float
    #Significant Striking Accuracy
    str_acc: float
    #Significant Strikes Absorbed per Minute
    sapm: float
    #Significant Strike Defence (the % of opponents strikes that did not land)
    str_def: float
    #Average Takedowns Landed per 15 minutes
    td_avg: float
    #Takedown Accuracy
    td_acc: float
    #Takedown Defense (the % of opponents TD attempts that did not land)
    td_def: float
    #Average Submissions Attempted per 15 minutes
    sub_avg: float

@dataclass
class Location:
    city: str
    state: Optional[str]
    country: str

@dataclass 
class Event:
    name: str
    date: datetime
    location: Location
    fights: List['Fight']

@dataclass
class StrikeStats:
    landed: int
    attempted: int

@dataclass
class FighterPerformance:
    knockdowns: int
    significant_strikes: StrikeStats
    total_strikes: StrikeStats
    takedowns: StrikeStats
    submission_attempts: int
    reversals: int
    control_time_seconds: int
    head_significant_strikes: StrikeStats
    body_significant_strikes: StrikeStats
    leg_significant_strikes: StrikeStats
    distance: StrikeStats
    clinch: StrikeStats
    ground: StrikeStats


@dataclass
class RoundStats:
    roundNumber: int
    fighter_stats: Dict[Fighter, FighterPerformance]
    
@dataclass
class FightResult:
    winner: Fighter
    loser: Fighter
    method: str  
    details: Optional[str]  
    round: int
    time: str
    referee: str


@dataclass
class Fight:
    fight_id: str
    event_id: str
    weight_class: str
    fighters: Dict[Fighter, List[RoundStats]]
    result: FightResult

# try to clean the text lumped together 
def clean_text(text):
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    # Add a space before and after capitalized words (handles some clumping issues)
    text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)
    # Return cleaned text
    return text.strip()


# grab all event URLs
# http://www.ufcstats.com/statistics/events/completed
# http://www.ufcstats.com/statistics/events/completed/page=2
class UFCScraper:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.events = [] 

    def grab_event_urls(self):
        """Scrape the event URLs and details."""
        try:
            response = requests.get(self.base_url)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching URL: {self.base_url}, {e}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all("tr", class_="b-statistics__table-row")

        for row in rows:
            event_link = row.find("a", class_="b-link b-link_style_black")
            if not event_link:
                continue

            event_name = event_link.text.strip()
            event_url = event_link["href"]

            event_date_span = row.find("span", class_="b-statistics__date")
            if not event_date_span:
                continue
            event_date = event_date_span.text.strip()

            event_location_td = row.find("td", class_="b-statistics__table-col b-statistics__table-col_style_big-top-padding")
            if not event_location_td:
                continue
            event_location = event_location_td.text.strip()


            # Add the event to the list
            self.events.append({
                "name": event_name,
                "url": event_url,
                "date": event_date,
                "location": event_location
            })

    def grab_fight_urls(self):
        for event in self.events:
            try:
                response = requests.get(event['url'])
            except requests.RequestException as e:
                print(f"Error fetching URL: {self.base_url}, {e}")
                return
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.find_all("tr", class_="b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click")
            fight_urls = []
            for row in rows:
                fight_url = row.get('data-link')
                if fight_url:
                    fight_urls.append(fight_url)
        
            # Append the fight URLs to the event
            event['fight_urls'] = fight_urls
            

    def grab_fight_data(self):
        for event in self.events:
            for fight_url in event['fight_urls']:

                    # use selenium to click the expandable round, then use bs
                    driver = webdriver.Chrome()
                    driver.get(fight_url)
                    by_round_link = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "b-fight-details__collapse-link_rnd js-fight-collapse-link"))
                    )
                    by_round_link.click()

                    # wait until the new element appears with the round by round stats
                    WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.CLASS_NAME, "b-fight-details__table js-fight-table"))
                    )

                    html = driver.page_source

                    soup = BeautifulSoup(html, 'html.parser')
                    round_data = soup.select('.b-fight-details__table')
                    print(round_data)
                    # grab the winner, loser 
                    # weight class
                    # method , time , referee, details
                    # need selenium for this to get round by round stats

    # this will grab stats of every fighter (fighters page)
    def grab_fighter_stats(self):
        return
    


if __name__ == "__main__":
    #scraper = UFCScraper("http://www.ufcstats.com/statistics/events/completed")
    #scraper.grab_event_urls()
    #scraper.display_events()
    #scraper.grab_fight_urls()
    #scraper.grab_fight_data()
    chrome_options = Options()
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get("http://www.ufcstats.com/fight-details/00c6a2ef07ca51da")

    # click the link to expand the fight to see round by round stats
    by_round_link = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".b-fight-details__collapse-link_rnd"))
    )
    by_round_link.click()

    # wait until the new element appears with the round by round stats
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".b-fight-details__table"))
    )

    html = driver.page_source

    soup = BeautifulSoup(html, 'html.parser')

    # this returns winner/loser names, nicknames
    fight_outcome = soup.select('.b-fight-details__persons')

    # this return method of victory, referee, time, etc.     
    fight_details = soup.select('.b-fight-details__fight')
  
    # this grabs round 1 - 3 oftotals/significant strikes of both fighters
    round_data = soup.select('.b-fight-details__table')
    for round in round_data:
        print(clean_text(round.get_text(strip=True)))
    
    driver.quit()
