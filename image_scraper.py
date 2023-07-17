import json
import time
import concurrent.futures

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup


class CityImageScraper:
    def __init__(self):
        chrome_options = Options()
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.javascript": 2,
            "profile.managed_default_content_settings.cookies": 2,
            "profile.managed_default_content_settings.plugins": 2,
            "profile.managed_default_content_settings.popups": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        # chrome_options.add_argument("--headless")  # Run in headless mode
        self.driver = webdriver.Chrome(options=chrome_options)

    def close(self):
        self.driver.close()

    def get_city_image(self, city_url):
        self.driver.get(city_url)
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.new-intro-banner__image-container img')))
        except TimeoutException:
            print("Timed out waiting for page to load", city_url)

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        image_container = soup.find('div', {'class': 'new-intro-banner__image-container'})
        if image_container is None:
            print("Could not find image container on page", city_url)
            return

        image = image_container.find('img')
        if image is None or 'src' not in image.attrs:
            print("Could not find image on page", city_url)
            return

        return {
            'city_url': city_url,
            'image_url': image['src']
        }


def get_image(city_url):
    print(f"Handling URL {city_url}")
    scraper = CityImageScraper()
    start_time = time.time()
    image_info = scraper.get_city_image(city_url)
    end_time = time.time()
    scraper.close()
    return image_info, end_time - start_time  # return the image info and time taken


if __name__ == "__main__":
    # read json file
    with open('city.json', 'r') as f:
        data = json.load(f)

    city_urls = [city.get('url') for continent in data for city in continent.get('cities', [])]

    # city_urls = city_urls[:5]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:  # Use less workers
        results = list(executor.map(get_image, city_urls))

    city_img_result = {result[0]['city_url']: result[0]['image_url'] for result in results if result[0] is not None}
    total_time = sum(result[1] for result in results if result[0] is not None)
    average_time = total_time / len(city_img_result)

    print(f"Average time taken per operation: {average_time} seconds")

    # merge city image with city data
    for continent_index, continent in enumerate(data):
        for city_index, city in enumerate(continent.get('cities', [])):
            if city.get('url') in city_img_result:
                city['image'] = city_img_result[city.get('url')]

    with open('new_city.json', 'w') as f:
        json.dump(data, f, indent=4)
