from asyncio import ensure_future
import time

import base64
import json
import logging
import os
import random
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
import collections
import simplejson

collections.Callable = collections.abc.Callable

MILLESIMES = list(range(1982, 2016))
WINES = json.load(open("../../data/wines.json", "r"))
logger = logging.getLogger(__name__)


def scrap_page_all_wine(driver):
    try:
        url = ""
        # Scrol on the page to load all the wine we want to scrap
        scroll_pause_time = 0.5

        # Get scroll height
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(scroll_pause_time)

            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    except Exception as e:
        print(e)


def forge_url(wine_id, wine_name, millesime):
    return "https://www.idealwine.com/fr/prix-vin/{0}-{1}-Bouteille-{2}.jsp".format(
        wine_id, millesime, wine_name
    )


def get_filename(millesime, wine_name):
    photo_id = "{}_{}".format(millesime, wine_name)
    return "{}.json".format(photo_id)


def process_and_return_price(
    wine_id, wine_name, millesime, driver, waiting_time_multiplier=1
):
    url = forge_url(wine_id, wine_name, millesime)
    logger.info(url)
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    script = BeautifulSoup(str(soup.find_all("script")), "html.parser")

    wine_li = BeautifulSoup(
        str(soup.find_all("ul", {"class": "property"})), "html.parser"
    )
    data = wine_li.find_all("strong")
    description_dico = {}
    i = 0
    for title in wine_li.find_all("span"):
        if title.text not in description_dico:
            title_replace = title.text.replace("\u00e9", "e")
            description_dico[title_replace] = data[i].text
            i += 1
    print(description_dico)

    str_script = str(script)
    year_search_str = "labels: [\n"
    year_posi = str_script.find(year_search_str)
    year_end_posi = str_script.find(",\n],\ndatasets")
    year = str_script[year_posi + len(year_search_str) : year_end_posi].replace('"', "")
    l_year = year.split(",")
    price_search_str = "data: ["
    price_posi = str_script.find(price_search_str)
    price_end_podi = str_script.find(",],\npointRadius")
    price = str_script[price_posi + len(price_search_str) : price_end_podi].replace(
        '"', ""
    )
    l_price = price.split(",")
    print(l_price)
    print(l_year)

    tmp_dict = {}
    final_list = []

    for i, val in enumerate(l_year):
        tmp_dict["year"] = val
        tmp_dict["price"] = l_price[i]
        final_list.insert(i, tmp_dict.copy())
    placement_plus_price = {"placement": description_dico, "price": final_list}
    return placement_plus_price


def get_wine_processing_list():
    total_possible_count = 0
    wine_processing_list = []
    for millesime in MILLESIMES:
        for technical_name, wine_id, wine_name in WINES:
            total_possible_count += 1
            output_filename = get_filename(millesime, wine_name)[:-4] + "json"
            if not os.path.isfile(output_filename):
                wine_processing_list.append(
                    (millesime, technical_name, wine_id, wine_name)
                )
    random.shuffle(wine_processing_list)
    return wine_processing_list, total_possible_count


def main():
    print("Initialization of Chrome...")
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    driver = webdriver.Chrome(
        executable_path="/home/adrien/Downloads/chromedriver_linux64 /chromedriver",
        chrome_options=options,
    )

    wine_processing_list, total_possible_count = get_wine_processing_list()

    while len(wine_processing_list) > 0:
        # wine_processing_list, total_possible_count = get_wine_processing_list()
        progress_pct = (
            (total_possible_count - len(wine_processing_list))
            / total_possible_count
            * 100
        )
        logger.info(
            "{0} wines left to quey [{1:.3f} % done].".format(
                len(wine_processing_list), progress_pct
            )
        )
        (millesime, technical_name, wine_id, wine_name) = wine_processing_list[0]
        waiting_time_multiplier = 1
        while True:
            output_filename = get_filename(millesime, wine_name)[:-4] + ".json"
            if not os.path.isfile("/JSON_PRICE" + output_filename):
                try:
                    prices = process_and_return_price(
                        wine_id,
                        wine_name,
                        millesime,
                        driver,
                        waiting_time_multiplier,
                    )
                    json_price = simplejson.dumps(prices, indent=4, ensure_ascii=True)
                    line = "".join([technical_name, str(millesime)])
                    with open("./JSON_PRICE/" + output_filename, "w") as f:
                        f.write(json_price)
                        wine_processing_list.remove(
                            (millesime, technical_name, wine_id, wine_name)
                        )
                    break
                except IndexError:
                    logger.info(
                        "Millesime {0} does not exist for wine {1}.".format(
                            millesime, technical_name
                        )
                    )
                    wine_processing_list.remove(
                        (millesime, technical_name, wine_id, wine_name)
                    )
                    break
                except TimeoutException:
                    logger.info("TimeOut exception occurred. Resuming.")
                except FileNotFoundError:
                    logger.warning(
                        "Blank page detected. Retrying after 5 seconds. "
                        "Waiting time multiplier {}.".format(waiting_time_multiplier)
                    )
                    waiting_time_multiplier *= 2

                    if waiting_time_multiplier == 16:
                        logger.warning("Critical.")

                    if waiting_time_multiplier >= 32:
                        logger.error("Could not get it after a while. Giving up.")
                        wine_processing_list.remove(
                            (millesime, technical_name, wine_id, wine_name)
                        )
                        break

                    time.sleep(1)
            else:
                logger.info("Already there: {}.".format(output_filename))
                wine_processing_list.remove(
                    (millesime, technical_name, wine_id, wine_name)
                )
                break

    driver.quit()


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    main()
