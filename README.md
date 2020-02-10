# bestplaces.net-scraper

Scrape [bestplaces.net](https://www.bestplaces.net/) for zip code real estate 
statistics.

I wrote this to download certain statistics that I was personally interested 
in, so it doesn't grab everything. It will download and save to an sqlite 
database the following information for every zip code on the site:
* Population
* Population growth since the last census as a percentage
* Overall cost of living
* Utilities cost of living
* Median home cost
* Median home age
* Average rent for studios, 1BR, 2BR, 3BR, and 4BR apartments/houses
* Average overall rent
* Unemployment
* Job growth in the last year as a percentage
* Violent crime index
* Property crime index
* Percent of population that are renters
* Percent of properties that are vacant and available for rent
* Property tax rate
* Home appreciation in the last 12 months, 5 years, and 10 years

At the time of writing, bestplaces has 32,989 out of the 41,702 zip codes in 
the US. However, some very small zip codes may not have all of the information 
listed above. Anything that is not found will simply be entered into the 
database as empty columns.

## Prerequisites
* Python 3
* BeautifulSoup
* python-lxml
* sqlite3

## Installation
Install the [prerequisites](#prerequisites), then clone this repo:
```
git clone https://github.com/codeclem/bestplaces.net-scraper
```

## Usage
Simply run the script:
```
./scrape.py
```
The script takes no arguments. It will automatically create a `bestplaces.db` 
sqlite database in the current working directory, and begin scraping every 
zip code.

On my connection, it took 2-3 days to download everything with an average rate 
of about 1 request per second. The script will skip any zip codes that already 
exist in the database, so you can stop and restart as needed.

To query the database, open it with sqlite3:
```
sqlite3 bestplaces.db
```
Everything is stored in a single table called `stats` with the following schema:
```
CREATE TABLE stats (
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
                state text);
```
## Examples
Brush up on some basic SQL and you'll be able to run queries like...

Find me zip codes with at least 5000 people, showing population growth, 
with lower than average crime, affordable homes, and that has seen some job 
growth in the last year:
```
sqlite> select zip_code, city, state from stats where population > 5000 and population_growth > 10 and violent_crime < 23 and property_crime < 36 and median_home_cost < 170000 and job_growth > 1.5;
35040|Calera|Alabama
30628|Colbert|Georgia
31632|Hahira|Georgia
46184|New Whiteland|Indiana
24538|Concord|Virginia
73049|Jones|Oklahoma
74014|Broken Arrow|Oklahoma
74021|Collinsville|Oklahoma
57013|Canton|South_Dakota
57718|Blackhawk|South_Dakota
75410|Alba|Texas
75459|Howe|Texas
75754|Ben Wheeler|Texas
79934|El Paso|Texas
79938|El Paso|Texas
```

Find zip codes with at least 5000 people, lower than average crime, where over 
50% of the population rents their homes, and a lower than average cost of 
living:
```
sqlite> select zip_code,city,state from stats where population > 5000 and violent_crime < 23 and rental_market_percent > 50 and cost_of_living < 100;
80310|Boulder|Colorado
77380|The Woodlands|Texas
```
etc...
