#!/usr/bin/env python3

from bs4 import BeautifulSoup
import requests
import sqlite3
import re
from urllib.parse import urljoin
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

conn = sqlite3.connect('bestplaces.db')
session = requests.Session()
retries = Retry(total=9999,
                backoff_factor=1)
session.mount('http://', HTTPAdapter(max_retries=retries))


def init_db():
    c = conn.cursor()
    c.execute(
        """
        create table if not exists stats 
        (
            population integer,
            population_growth float,
            cost_of_living float,
            median_home_cost integer,
            median_home_age float,
            utilities_cost_of_living float,
            average_rent integer,
            rent_studio integer,
            rent_1br integer,
            rent_2br integer,
            rent_3br integer,
            rent_4br integer,
            unemployment float,
            job_growth float,
            violent_crime float,
            property_crime float,
            rental_market_percent float,
            vacancy float,
            property_tax float,
            appreciation_12mo float,
            appreciation_5yr float,
            appreciation_10yr float,
            zip_code integer,
            city text,
            state text
        )
        """
    )

    conn.commit()


def scrape_stats(zip):
    c = conn.cursor()
    c.execute('select zip_code from stats where zip_code = ?', (zip['code'],))
    if c.fetchone():
        print(zip['code'] + ' already in database')
        return

    print('Downloading statistics for ' + zip['code'])
    print('requesting zip page ' + zip['link'])
    zip_page = BeautifulSoup(session.get(zip['link']).text, 'lxml')
    print('parsing zip page')
    population = zip_page.find('u', string='Population') \
        .parent.parent.next_sibling.next_sibling.string.replace(',', '')

    population_growth = zip_page.find(
        'p', string=re.compile('.{0,1}[0-9]{1,2}.[0-9]{1}%')).string
    population_growth = re.findall(
        '.{0,1}[0-9]{1,2}.[0-9]{1}%', population_growth
    )[0].replace('%', '').replace('+', '')

    menu = zip_page.find('ul', class_='list-group')
    url = menu.find('a', string='Housing Stats')['href']

    print('requesting Housing Stats ' + url)
    housing_page = BeautifulSoup(session.get(url).text, 'lxml')

    print('parsing Housing Stats')
    housing_table = housing_page.find('table', id='mainContent_dgHousing')
    if housing_table:
        median_home_age = housing_table.find('u', string='Median Home Age')
        if median_home_age:
            median_home_age = median_home_age.parent.parent.next_sibling.string

        median_home_cost = housing_table.find('u', string='Median Home Cost')
        if median_home_cost:
            median_home_cost = median_home_cost.parent.parent.next_sibling.string
            median_home_cost = median_home_cost.replace('$', '')
            median_home_cost = median_home_cost.replace(',', '')

        appreciation_12mo = housing_table.find(
            'u', string='Home Appr. Last 12 months'
        )
        if appreciation_12mo:
            appreciation_12mo = appreciation_12mo.parent.parent \
                .next_sibling.string.replace('%', '')

        appreciation_5yr = housing_table.find(
            'u', string='Home Appr. Last 5 yrs.'
        )
        if appreciation_5yr:
            appreciation_5yr = appreciation_5yr.parent.parent \
                .next_sibling.string.replace('%', '')

        appreciation_10yr = housing_table.find(
            'u', string='Home Appr. Last 10 yrs.'
        )
        if appreciation_10yr:
            appreciation_10yr = appreciation_10yr.parent.parent \
                .next_sibling.string.replace('%', '')

        property_tax = housing_table.find(
            'u', string='Property Tax Rate'
        )
        if property_tax:
            property_tax = property_tax.parent.parent.next_sibling.string \
                .replace('$', '')

        average_rent = housing_table.find('u', string='Average Rent')
        if average_rent:
            average_rent = average_rent.parent.parent.next_sibling.string \
                .replace('$', '').replace(',', '')

        rent_studio = housing_table.find('u', string='Studio Apartment')
        if rent_studio:
            rent_studio = rent_studio.parent.parent.next_sibling.string \
                .replace('$', '').replace(',', '')

        rent_1br = housing_table.find(
            'u', string='1 Bedroom Home or Apartment')
        if rent_1br:
            rent_1br = rent_1br.parent.parent.next_sibling.string \
                .replace('$', '').replace(',', '')

        rent_2br = housing_table.find(
            'u', string='2 Bedroom Home or Apartment')
        if rent_2br:
            rent_2br = rent_2br.parent.parent.next_sibling.string \
                .replace('$', '').replace(',', '')

        rent_3br = housing_table.find(
            'u', string='3 Bedroom Home or Apartment')
        if rent_3br:
            rent_3br = rent_3br.parent.parent.next_sibling.string \
                .replace('$', '').replace(',', '')

        rent_4br = housing_table.find(
            'u', string='4 Bedroom Home or Apartment')
        if rent_4br:
            rent_4br = rent_4br.parent.parent.next_sibling.string \
                .replace('$', '').replace(',', '')

        vacancy = housing_table.find('u', string='Vacant For Rent')
        if vacancy:
            vacancy = vacancy.parent.parent.next_sibling.string \
                .replace('%', '')

    rental_market_percent = housing_page.find(
        string=re.compile('Renters make up .* of the .* population')
    )
    if rental_market_percent:
        rental_market_percent = re.findall(
            '[0-9]{0,2}.[0-9]{1}%', rental_market_percent
        )[0]
        rental_market_percent = rental_market_percent.replace('%', '')

    url = menu.find('a', string='Cost of Living')['href']
    print('requesting Cost of Living ' + url)
    cost_of_living_page = BeautifulSoup(session.get(url).text, 'lxml')

    print('parsing Cost of Living')
    cost_of_living = cost_of_living_page.find('u', string='Overall')
    if cost_of_living:
        cost_of_living = cost_of_living.parent.next_sibling.string

    utilities_cost_of_living = cost_of_living_page.find(
        'u', string='Utilities'
    )
    if utilities_cost_of_living:
        utilities_cost_of_living = utilities_cost_of_living.parent \
            .next_sibling.string

    url = menu.find('a', string='Crime')['href']
    print('requesting Crime stats ' + url)
    crime_page = BeautifulSoup(session.get(url).text, 'lxml')

    print('parsing Crime stats')
    violent_crime = crime_page.find(
        string=re.compile('.* violent crime is .*')
    )
    if violent_crime:
        violent_crime = re.findall(
            '\s[0-9]{0,2}\.[0-9]{1}', violent_crime
        )[0].strip()

    property_crime = crime_page.find(
        string=re.compile('.* property crime is .*')
    )
    if property_crime:
        property_crime = re.findall(
            '\s[0-9]{0,2}\.[0-9]{1}', property_crime
        )[0].strip()

    url = menu.find('a', string='Job Market')['href']
    print('requesting Job Market stats ' + url)
    job_market_page = BeautifulSoup(session.get(url).text, 'lxml')

    print('parsing Job Market stats')
    job_growth = job_market_page.find('u', string='Recent Job Growth')
    if job_growth:
        job_growth = job_growth.parent.parent.next_sibling.string \
            .replace('%', '')

    unemployment = job_market_page.find('u', string='Unemployment Rate')
    if unemployment:
        unemployment = unemployment.parent.parent.next_sibling.string \
            .replace('%', '')

    print('population: ', population)
    print('population_growth: ', population_growth)
    print('median_home_age: ', median_home_age)
    print('median_home_cost: ', median_home_cost)
    print('appreciation_12mo: ', appreciation_12mo)
    print('appreciation_5yr: ', appreciation_5yr)
    print('appreciation_10yr: ', appreciation_10yr)
    print('property_tax: ', property_tax)
    print('average_rent: ', average_rent)
    print('rent_studio: ', rent_studio)
    print('rent_1br: ', rent_1br)
    print('rent_2br: ', rent_2br)
    print('rent_3br: ', rent_3br)
    print('rent_4br: ', rent_4br)
    print('vacancy: ', vacancy)
    print('rental_market_percent: ', rental_market_percent)
    print('cost_of_living: ', cost_of_living)
    print('utilities_cost_of_living: ', utilities_cost_of_living)
    print('violent_crime: ', violent_crime)
    print('property_crime: ', property_crime)
    print('job_growth: ', job_growth)
    print('unemployment: ', unemployment)

    c.execute(
        """
        insert into stats
        (
            population,
            population_growth,
            median_home_age,
            median_home_cost,
            appreciation_12mo,
            appreciation_5yr,
            appreciation_10yr,
            property_tax,
            average_rent,
            rent_studio,
            rent_1br,
            rent_2br,
            rent_3br,
            rent_4br,
            vacancy,
            rental_market_percent,
            cost_of_living,
            utilities_cost_of_living,
            violent_crime,
            property_crime,
            job_growth,
            unemployment,
            zip_code,
            city,
            state
        )
            values 
        (
            ?, ?, ?, ?, ?, ?, ?, ?, 
            ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        """,
        (
            population,
            population_growth,
            median_home_age,
            median_home_cost,
            appreciation_12mo,
            appreciation_5yr,
            appreciation_10yr,
            property_tax,
            average_rent,
            rent_studio,
            rent_1br,
            rent_2br,
            rent_3br,
            rent_4br,
            vacancy,
            rental_market_percent,
            cost_of_living,
            utilities_cost_of_living,
            violent_crime,
            property_crime,
            job_growth,
            unemployment,
            zip['code'],
            zip['city'],
            zip['state']
        )
    )
    conn.commit()


if __name__ == '__main__':
    init_db()

    r = session.get('https://www.bestplaces.net/find/')
    soup = BeautifulSoup(r.text, 'lxml')
    h4 = soup.find('h4', string='Click a State and Browse')
    state_links = h4.next_sibling.next_sibling.find_all('a')
    for state in state_links:
        state_page = BeautifulSoup(
            session.get(state['href'])
            .text, 'lxml'
        )
        print('downloading zip codes in ' + state.string)
        zip_page_link = urljoin(
            state['href'], state_page.find(
                'a', string='Zip Codes'
            )['href']
        )

        zip_page = BeautifulSoup(session.get(zip_page_link).text, 'lxml')
        zip_code_links = zip_page.find_all(
            'a', string=re.compile('[0-9]{5}')
        )

        for zip_link in zip_code_links:
            zip_code = zip_link.string[0:5]
            city = re.findall('\(.*\)', zip_link.string)[0] \
                     .replace('(', '') \
                     .replace(')', '')
            scrape_stats({
                'city': city,
                'state': state.string,
                'code': zip_code,
                'link': urljoin(zip_page_link, zip_link['href'])
            })
    conn.close()
