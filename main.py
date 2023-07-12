import json
import multiprocessing
from bs4 import BeautifulSoup
from selenium import webdriver


class GetYourGuide:

    def __init__(self):
        self.base_url = 'https://www.getyourguide.com'
        self.sitemap = f'{self.base_url}/destinations'
        self.driver = webdriver.Chrome()
        self.ret_countries = {}

    def get_country_urls(self):
        self.driver.get(self.sitemap)

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        continents = soup.find_all('h3', {'class': 'links-group__title'})

        for index, continent in enumerate(continents):
            continent_name = continent.text
            countries = soup.find_all('ul', {'class': 'links-group-list'})[index].find_all('a')
            for country in countries:
                country_name = country.text
                country_url = country['href']
                self.ret_countries.setdefault(continent_name, []).append({
                    'continent': continent_name,
                    'country': country_name,
                    'url': f'{self.base_url}/{country_url}'
                })

        return self.ret_countries

    def get_cities(self):
        get_countries = [
            country for continent in self.ret_countries.values() for country in continent
        ]
        with multiprocessing.Pool(processes=5) as pool:
            result = pool.map(self.get_city, get_countries)
        return result

    @staticmethod
    def get_city(country: dict):
        driver = webdriver.Chrome()
        driver.get(country['url'])
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        get_cities = soup.find_all('h3', {'class': 'links-group__title'})
        get_cities = [city for city in get_cities if 'cities in' in city.text.lower()]
        get_cities = get_cities[0].find_next_sibling(
            'ul', {'class': 'links-group-list'}
        ) if get_cities else []
        get_cities = get_cities.find_all('a') if get_cities else []
        for get_city in get_cities:
            city_name = get_city.text.replace(f', {country["country"]}', '').strip()
            city_url = get_city['href']
            # open city url and get image
            driver.get(f'https://www.getyourguide.com/{city_url}')
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            image = soup.find('div', {'class': 'new-intro-banner__image-container'}).find('img')['src']
            country.setdefault('cities', []).append({
                'name': city_name,
                'url': f'https://www.getyourguide.com/{city_url}',
                'image': image
            })
        return country


if __name__ == '__main__':
    g = GetYourGuide()
    g.get_country_urls()
    get_cities_data = g.get_cities()
    with open('city.json', 'w') as f:
        json.dump(get_cities_data, f, indent=4)
