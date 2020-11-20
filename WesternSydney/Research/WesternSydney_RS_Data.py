import copy
import csv
import json
import logging
import os
import re
import time
from pathlib import Path

import bs4 as bs4
import requests
# noinspection PyProtectedMembe
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from CustomMethods import TemplateData
from CustomMethods.DurationConverter import convert_duration


def get_page(_url_):
    """Will download the contents of the page using the requests library.
    :return: a BeautifulSoup object i.e. the content of the webpage related to the given URL.
    """
    # noinspection PyBroadException,PyUnusedLocal
    try:
        r = requests.get(_url_)
        if r.status_code == 200:
            return bs4.BeautifulSoup(r.content, 'html.parser')
    except Exception:
        pass
    return None


def webdriver_wait(_xpath_):
    try:
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f"{_xpath_}"))
        )
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as err:
        logging.warning(err)


def remove_banned_words(to_print, database_regex):
    _pattern_ = re.compile(r"\b(" + "|".join(database_regex) + ")\\W", re.I)
    return _pattern_.sub("", to_print)


def save_data_json(title__, data__):
    with open(title__, 'w', encoding='utf-8') as f:
        json.dump(data__, f, ensure_ascii=False, indent=2)


def tag_text(_tag_):
    return _tag_.get_text().__str__().strip()


def has_numbers(_input_string_):
    return any(char.isdigit() for char in _input_string_)


# noinspection PyUnusedLocal
def get_course_name_from_url(cd, *args, **kwargs):
    try:
        pu = args[0] if len(args) > 0 else cd['Website']
        flag = args[1] if len(args) >= 1 else None
        if len(cd['Course']) < 5:
            if pu.endswith('/'):
                pu = pu[:-1]
            last_slash_index = pu.rfind('/')
            cn = pu[last_slash_index + 1:].replace('-', ' ').replace('.html', '').title()
            cd['Course'] = pu[last_slash_index + 1:].replace('-', ' ').replace('.html', '').title()
            return cd if flag is 'D' else cn if flag is 'S' else None
    except (AttributeError, TypeError, IndexError, TypeError) as err:
        logging.debug(err)
        return cd


# selenium web driver
# we need the Chrome driver to simulate JavaScript functionality
# thus, we set the executable path and driver options arguments
# ENSURE YOU CHANGE THE DIRECTORY AND EXE PATH IF NEEDED (UNLESS YOU'RE NOT USING WINDOWS!)
option = webdriver.ChromeOptions()
option.add_argument(" - incognito")
# option.add_argument("headless")
exec_path = Path(os.getcwd().replace('\\', '/'))
exec_path = exec_path.parent.parent.parent.parent.__str__() + '/Libraries/Google/v86/chromedriver.exe'
browser = webdriver.Chrome(executable_path=exec_path, chrome_options=option)
browser.maximize_window()
delay = 10

# collect page source for fees
"""
with open('LocalData/2020_INTL_Indicative_Fees_-_PG_-_7.8.20.html', encoding='utf8') as dom_file:  # Domestic Fees local HTML
    soup_fees = bs4.BeautifulSoup(dom_file, 'html.parser')
option2 = webdriver.ChromeOptions()
option2.add_argument(" - incognito")
# option2.add_argument("headless")
browser2 = webdriver.Chrome(executable_path=exec_path, chrome_options=option2)
browser2.get("file:///"+os.getcwd()+"/LocalData/2020_INTL_Indicative_Fees_-_UG_-_7.8.20.html")
time.sleep(1)
fee_webpage = browser2.page_source
"""


# read the url from each file into a list
course_links_file_path = Path(os.getcwd().replace('\\', '/'))
course_links_file_path = course_links_file_path.__str__() + '/western_sydney_rs_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'WesternSydney_RS_Data.csv'

level_key = TemplateData.level_key  # dictionary of course levels

faculty_key = TemplateData.faculty_key  # dictionary of course levels

currency_pattern = "(?:[\£\$\€\(RM)\]{1}[,\d]+.?\d*)"  # regex pattern for finding currency or cash amount strings

course_data_all = []

city_set = set()

bar = ' | '  # generic text separator for tidiness

months = {'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
          'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12}

course_data_template = {'Level_Code': '', 'University': '', 'City': '', 'Course': '',
                        'Faculty': '',
                        'Int_Fees': '', 'Local_Fees': '', 'Currency': 'AUD', 'Currency_Time': 'Years', 'Duration': '',
                        'Duration_Time': '', 'Full_Time': 'Yes', 'Part_Time': 'No',
                        'Prerequisite_1': '', 'Prerequisite_1_grade_1': '',  # ATAR
                        'Prerequisite_2': '', 'Prerequisite_2_grade_2': '',  # IELTS
                        'Prerequisite_3': '', 'Prerequisite_3_grade_3': '',  # GPA
                        'Website': '', 'Course_Lang': 'English', 'Availability': 'A', 'Description': '',
                        'Career_Outcomes': '',
                        'Country': 'Australia', 'Online': 'No', 'Offline': 'Yes', 'Distance': 'No',
                        'Face_to_Face': 'Yes',
                        'Blended': 'No', 'Remarks': ''}

# noinspection SpellCheckingInspection
possible_cities = {'Parramatta City': 'Parramatta City',
                   'Liverpool City': 'Sydney',
                   'Campbelltown': 'Sydney',
                   'Bankstown': 'Sydney',
                   'Parramatta South': 'Parramatta City',
                   'Hawkesbury': 'Hawkesbury',
                   'Penrith': 'Penrith',
                   'Lithgow': 'Lithgow',
                   'Sydney Olympic Park': 'Sydney',
                   'Nirimba': 'Nirimba',
                   'Sydney City': 'Sydney',
                   'Vietnam': 'Ho Chi Minh City',
                   'Online': 'Sydney'}

other_cities = {}

sample = [""]

# MAIN ROUTINE
for each_url in course_links_file:

    course_data = {'Level_Code': '', 'University': 'Western Sydney University', 'City': '', 'Course': '',
                   'Faculty': '',
                   'Int_Fees': '', 'Local_Fees': '', 'Currency': 'AUD', 'Currency_Time': 'Years', 'Duration': '',
                   'Duration_Time': '', 'Full_Time': 'Yes', 'Part_Time': 'No',
                   'Prerequisite_1': '', 'Prerequisite_1_grade_1': '',  # ATAR
                   'Prerequisite_2': '', 'Prerequisite_2_grade_2': '',  # IELTS or anything else
                   'Prerequisite_3': '', 'Prerequisite_3_grade_3': '',  # GPA or IB
                   'Website': '', 'Course_Lang': 'English', 'Availability': 'A', 'Description': '',
                   'Career_Outcomes': '',
                   'Country': 'Australia', 'Online': 'No', 'Offline': 'Yes', 'Distance': 'No', 'Face_to_Face': 'Yes',
                   'Blended': 'No', 'Remarks': ''}

    actual_cities = set()

    browser.get(each_url)
    time.sleep(3)
    url__ = each_url
    pure_url = each_url.strip()
    print('CURRENT LINK: ', pure_url)
    each_url = browser.page_source
    soup = bs4.BeautifulSoup(each_url, 'lxml')

    all_text = soup.text.replace('\n', '').strip()

    # COURSE URL
    course_data['Website'] = pure_url

    # COURSE NAME
    title_ = str()
    title = soup.find('h1', {'class': 'title__text secondary'})
    if title:
        course_data['Course'] = tag_text(title)
        title_ = tag_text(title)
    else:
        try:
            THE_XPATH = "//h1[1]"
            WebDriverWait(browser, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{THE_XPATH}'))
            )
            value = browser.find_element_by_xpath(f'{THE_XPATH}').text
            course_data['Course'] = value
        except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
            pass

    # DECIDE THE LEVEL CODE
    lev_str = str()
    for i in level_key:
        for j in level_key[i]:
            if j in course_data['Course']:
                course_data['Level_Code'] = i

    # DECIDE THE FACULTY
    fac_str = str()
    for i in faculty_key:
        for j in faculty_key[i]:
            if j.lower() in course_data['Course'].lower():
                course_data['Faculty'] = i
                fac_str = i

        # OUTCOMES
    try:
        # THE_XPATH = "(//div[@class='tile-carousel-side']/div[@class='component component--wysiwyg']/ancestor::div[@class='tile-carousel-side'][1])[1]"
        THE_XPATH = "//h2[contains(text(), 'Your career')]/ancestor::div[@class='tile-carousel-side']"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Career_Outcomes'] = value
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('cant extract outcomes')

    # DURATION
    try:
        THE_XPATH = "(//*[text()='FULL TIME'][1]/following::*[1])[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Full_Time'] = 'Yes'

        duration = convert_duration(value.replace('trimester', 'semester').replace('yrs', 'years'))
        course_data['Duration'] = duration[0]
        course_data['Duration_Time'] = duration[1]
        if duration[0] < 2 and 'month' in duration[1].lower():
            course_data['Duration'] = duration[0]
            course_data['Duration_Time'] = 'Month'
        if duration[0] < 2 and 'year' in duration[1].lower():
            course_data['Duration'] = duration[0]
            course_data['Duration_Time'] = 'Year'
        if 'week' in duration[1].lower():
            course_data['Duration'] = duration[0]
            course_data['Duration_Time'] = 'Weeks'

    except (AttributeError, TypeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        print('cant extract full time duration')
        course_data['Full_Time'] = 'No'
        logging.warning(e)
    try:
        THE_XPATH = "(//*[text()='PART TIME'][1]/following::*[1])[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Part_Time'] = 'Yes'

        if course_data['Full_Time'] == 'No':
            duration = convert_duration(value.replace('trimester', 'semester').replace('yrs', 'years'))
            course_data['Duration'] = duration[0]
            course_data['Duration_Time'] = duration[1]
            if duration[0] < 2 and 'month' in duration[1].lower():
                course_data['Duration'] = duration[0]
                course_data['Duration_Time'] = 'Month'
            if duration[0] < 2 and 'year' in duration[1].lower():
                course_data['Duration'] = duration[0]
                course_data['Duration_Time'] = 'Year'
            if 'week' in duration[1].lower():
                course_data['Duration'] = duration[0]
                course_data['Duration_Time'] = 'Weeks'

    except (AttributeError, TypeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        print('cant extract part time duration')
        course_data['Part_Time'] = 'No'
        logging.warning(e)

    if course_data['Full_Time'] is 'No' and course_data['Part_Time'] is 'No':
        course_data['Full_Time'] = 'Yes'

    # CITIES ELEMENTS
    try:
        # THE_XPATH = "(//div[@class='tile-carousel-side']/div[@class='component component--wysiwyg']/ancestor::div[@class='tile-carousel-side'][1])[1]"
        THE_XPATH = "//div[contains(@class, 'tile-carousel__content js-tile')]/div[@class='tile-carousel__text']/h3[@class='tile-carousel__caption']"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        values = browser.find_elements_by_xpath(f'{THE_XPATH}')
        for i in possible_cities:
            for j in values:
                if i in j.text:
                    actual_cities.add(i)
        if 'Online' in actual_cities and len(actual_cities) <= 1:
            course_data['Offline'] = 'No'
            course_data['Face_to_Face'] = 'No'
            course_data['Online'] = 'Yes'

    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        logging.warning(e)
        print('cant extract cities')

    # FEES
    dom_clicked = None
    int_clicked = None
    DROPDOWN_XPATH = "//select[starts-with(@id, 'dd-tabs')]"
    DOMESTIC_XPATH = "//select[starts-with(@id, 'dd-tabs')]/option[contains(text(), 'Domestic')]"
    INTERNATIONAL_XPATH = "//select[starts-with(@id, 'dd-tabs')]/option[contains(text(), 'International')]"

    try:
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{DROPDOWN_XPATH}'))
        )
        element = browser.find_element_by_xpath(f'{DROPDOWN_XPATH}')
        element.click()
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        logging.warning(e)
        print('cant click fees dropdown')
    try:
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{DOMESTIC_XPATH}'))
        )
        element = browser.find_element_by_xpath(f'{DOMESTIC_XPATH}')
        element.click()
        time.sleep(0.2)
        dom_clicked = True
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        logging.warning(e)
        print('cant click domestic option')
    try:
        FEES_XPATH = "//p[contains(text(), '$')]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{FEES_XPATH}'))
        )
        elements = browser.find_elements_by_xpath(f'{FEES_XPATH}')
        value = str()
        for i in elements:
            value += i.text
            # print(i.text)
        try:
            course_data['Local_Fees'] = re.findall(currency_pattern, value)[0].replace('$', '').replace(',', '').replace('*', '')
            course_data['Currency_Time'] = 'Years'
        except IndexError as e:
            logging.debug(e)
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        logging.warning(e)
        print('cant find fees tag')
    try:
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{INTERNATIONAL_XPATH}'))
        )
        element = browser.find_element_by_xpath(f'{INTERNATIONAL_XPATH}')
        element.click()
        time.sleep(0.2)
        dom_clicked = True
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        logging.warning(e)
        print('cant click international option')
    try:
        FEES_XPATH = "//p[contains(text(), '$')]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{FEES_XPATH}'))
        )
        elements = browser.find_elements_by_xpath(f'{FEES_XPATH}')
        value = str()
        for i in elements:
            value += i.text
            # print(i.text)
        try:
            course_data['Int_Fees'] = re.findall(currency_pattern, value)[0].replace('$', '').replace(',', '').replace('*', '')
            course_data['Currency_Time'] = 'Years'
        except IndexError as e:
            logging.debug(e)
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        logging.warning(e)
        print('cant find fees tag')

    # AVAILABILITY
    dom_only = soup.find(True, text=re.compile('^.*This course is only available to domestic.*$', re.IGNORECASE))
    if dom_only:
        course_data['Availability'] = 'D'

    # DESCRIPTION
    try:
        THE_XPATH = "//div[@class='tile-carousel-side']/div[@class='component component--wysiwyg']"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Description'] = value
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        try:
            THE_XPATH = "(//*[@class='tile-carousel-side']/*[1])[1]"
            WebDriverWait(browser, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{THE_XPATH}'))
            )
            value = browser.find_element_by_xpath(f'{THE_XPATH}').text
            course_data['Description'] = value
        except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
            print('cant extract description')

    # duplicating entries with multiple cities for each city
    cities_covered = []
    for i in actual_cities:
        if possible_cities[i] in cities_covered:
            continue
        course_data['City'] = possible_cities[i]
        print('repeated cities: ', possible_cities[i])
        course_data_all.append(copy.deepcopy(course_data))
        cities_covered.append(possible_cities[i])

    del actual_cities, cities_covered

    print('COURSE: ', course_data['Course'])
    print('DURATION + DURATION TIME: ', course_data['Duration'], course_data['Duration_Time'])
    print('DESCRIPTION: ', course_data['Description'])
    print('LEVEL CODE: ', course_data['Level_Code'])
    print('CITY: ', course_data['City'])
    print('AVAILABILITY: ', course_data['Availability'])
    print('FACULTY: ', course_data['Faculty'])
    print('INT FEES: ', course_data['Int_Fees'])
    print('LOCAL FEES: ', course_data['Local_Fees'])
    print('ATAR: ', course_data['Prerequisite_1_grade_1'])
    # print(': ', course_data['Prerequisite_2_grade_2'])
    # print(': ', course_data['Prerequisite_3_grade_3'])
    print('FULL TIME: ', course_data['Full_Time'])
    print('PART-TIME: ', course_data['Part_Time'])
    print('DISTANCE: ', course_data['Distance'])
    print('BLENDED: ', course_data['Blended'])
    print('OFFLINE: ', course_data['Offline'])
    print('ONLINE: ', course_data['Online'])
    print('FACE TO FACE: ', course_data['Face_to_Face'])
    print('OUTCOMES: ', course_data['Career_Outcomes'])
    print('REMARKS: ', course_data['Remarks'])
    print()

print(*course_data_all, sep='\n')

# tabulate our data__
# course_dict_keys = set().union(*(d.keys() for d in course_data_all))
course_dict_keys = []
for i in course_data_template:
    course_dict_keys.append(i)

with open(csv_file, 'w', encoding='utf-8', newline='') as output_file:
    dict_writer = csv.DictWriter(output_file, course_dict_keys)
    dict_writer.writeheader()
    dict_writer.writerows(course_data_all)

browser.quit()
