import json
import logging
import os
import random
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
import collections
import simplejson


def get_bottle_url(driver):
    try:
        url = "https://www.idealwine.com/fr/cote/bordeaux.jsp"
        driver.get(url)
        # Scrol on the page to load all the wine we want to scrap
        scroll_pause_time = 1

        # Get scroll height
        last_height = driver.execute_script("return document.body.scrollHeight")
        i = 0
        while i < 5:
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            scrap_page(driver.page_source)
            # Wait to load page
            time.sleep(scroll_pause_time)

            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            i += 1
    except Exception as e:
        print(e)
    return BeautifulSoup(driver.page_source, "html.parser")


def scrap_page(source_page):
    soup = BeautifulSoup(source_page, "html.parser")
    section = soup.find_all("section", {"class": "section group wrapper post"})
    return print(section)


with webdriver.Firefox() as driver:
    get_bottle_url(driver)
