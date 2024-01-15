import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from threading import Thread, Semaphore
import queue


class GetYourGuide:

    def __init__(self):
        self.base_url = 'https://www.getyourguide.com'
        self.sitemap = f'{self.base_url}/en-us/destinations'
        self.ret_countries = {}

    def get_country_urls(self):
        option = Options()
        option.add_argument('--headless')
        option.add_argument('--no-sandbox')
        option.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=option)
        driver.get(self.sitemap)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
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
                    'url': f'{self.base_url}/en-us/{country_url}'
                })

        driver.close()

        return self.ret_countries

    def get_cities(self, ret_countries: dict = None):
        if not ret_countries:
            ret_countries = self.ret_countries

        get_countries = [
            country for continent in ret_countries.values() for country in continent
        ]
        get_countries = get_countries
        print(f'total countries: {len(get_countries)}')

        result_queue = queue.Queue()
        semaphore = Semaphore(2)

        def worker(country):
            with semaphore:
                result_queue.put(get_city(country))

        threads = [Thread(target=worker, args=(country,)) for country in get_countries]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        result = []
        while not result_queue.empty():
            result.append(result_queue.get())

        return result


options = Options()
options.add_argument('--headless')
options.add_argument("window-size=1920x1080")
options.add_argument("disable-gpu")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
)
options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
options.page_load_strategy = 'eager'


def get_city_detail(url: str):
    driver = webdriver.Chrome(options=options)
    try:
        req_city_url = f'https://www.getyourguide.com/{url}'
        driver.get(req_city_url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        image = soup.find('a', {'class': 'nearby-destination-card'})
        image = image.find('figure', {'class': 'gyg-location-card__image-figure'}) if image else None
        image = image.find('picture') if image else None
        image = image.find('source')['srcset'] if image else None
        city_name = soup.find('div', {'class': 'header'}).find('span', {'class': 'header-text'}).text

        return {
            'name': city_name,
            'url': driver.current_url,
            'image': image
        }
    finally:
        driver.quit()


def get_city(country: dict):
    if country['url'] == 'https://www.getyourguide.com':
        return country

    driver = webdriver.Chrome(options=options)
    driver.get(country['url'])
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    get_cities = soup.find_all('h3', {'class': 'links-group__title'})
    get_cities = [city for city in get_cities if 'cities in' in city.text.lower()]
    get_cities = get_cities[0].find_next_sibling('ul', {'class': 'links-group-list'}) if get_cities else []
    get_cities = get_cities.find_all('a') if get_cities else []

    print('total cities', len(get_cities))

    city_urls = [city['href'] for city in get_cities if city['href']]
    print('city_urls', len(city_urls))
    print('--')

    results_queue = queue.Queue()
    semaphore = Semaphore(5)  # Aynı anda en fazla 5 thread

    def worker(url):
        with semaphore:
            city_detail = get_city_detail(url)
            results_queue.put(city_detail)

    threads = [Thread(target=worker, args=(url,)) for url in city_urls]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    city_details = []
    while not results_queue.empty():
        city_details.append(results_queue.get())

    for city_detail in city_details:
        city_name = city_detail['name']
        image = city_detail['image']
        country.setdefault('cities', []).append({
            'name': city_name,
            'url': driver.current_url,
            'image': image
        })

    driver.quit()
    return country


if __name__ == '__main__':
    g = GetYourGuide()
    ret_countries = g.get_country_urls()

    # if ret_countries:
    #     with open('ret_countries.json', 'w') as f:
    #         json.dump(ret_countries, f, indent=4)

    with open('ret_countries.json', 'r') as f:
        ret_countries = json.load(f)

    get_cities_data = g.get_cities(ret_countries=ret_countries)
    if get_cities_data:
        with open('new_city.json', 'w') as f:
            json.dump(get_cities_data, f, indent=4)
