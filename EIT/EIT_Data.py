import copy
import csv
import json
import logging
import os
import re
import sre_constants
import time
from datetime import date as dt
from pathlib import Path
from urllib.parse import urljoin

import bs4 as bs4
import requests
# noinspection PyProtectedMembe
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, NoSuchElementException, \
    StaleElementReferenceException, JavascriptException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from CustomMethods import TemplateData
from CustomMethods.DurationConverter import convert_duration, convert_duration_cleanly


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
        WebDriverWait(browser, 5).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f"{_xpath_}"))
        )
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        print(e.traceback)


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
    except (AttributeError, TypeError, IndexError, TypeError) as e:
        logging.debug(e)
        return cd


# selenium web driver
# we need the Chrome driver to simulate JavaScript functionality
# thus, we set the executable path and driver options arguments
# ENSURE YOU CHANGE THE DIRECTORY AND EXE PATH IF NEEDED (UNLESS YOU'RE NOT USING WINDOWS!)
option = webdriver.ChromeOptions()
option.add_argument(" - incognito")
# option.add_argument("headless")
exec_path = Path(os.getcwd().replace('\\', '/'))
exec_path = exec_path.parent.parent.parent.__str__() + '/Libraries/Google/v86/chromedriver.exe'
browser = webdriver.Chrome(executable_path=exec_path, chrome_options=option)
browser.maximize_window()
delay = 5

# collect page source for fees
"""
with open('LocalData/excelsia-tuition-fees.html', encoding='utf8') as dom_file:  # Domestic Fees local HTML
    soup_fees = bs4.BeautifulSoup(dom_file, 'html.parser')
option2 = webdriver.ChromeOptions()
option2.add_argument(" - incognito")
option2.add_argument("headless")
browser2 = webdriver.Chrome(executable_path=exec_path, chrome_options=option2)
browser2.get("file:///"+os.getcwd()+"/LocalData/excelsia-tuition-fees.html")
time.sleep(1)
fee_webpage = browser2.page_source
"""

# read the url from each file into a list
course_links_file_path = Path(os.getcwd().replace('\\', '/'))
course_links_file_path = course_links_file_path.__str__() + '/eit_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'EIT_All_Data.csv'

level_key = TemplateData.level_key  # dictionary of course levels

faculty_key = TemplateData.faculty_key  # dictionary of course levels

currency_pattern = "(?:[\£\$\€\(RM)\]{1}[,\d]+.?\d*)"  # regex pattern for finding currency or cash amount strings

course_data_all = []

city_set = set()

bar = ' | '  # generic text separator for tidiness

months = TemplateData.months  # generic dictionary for translating worded months to numbers

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
possible_cities = {'ACT': 'Australian Capital Territory',
                   'NSW': 'New South Wales',
                   'NT': 'Norther Territory',
                   'QLD': 'Queensland',
                   'SA': 'South Australia',
                   'VIC': 'Victoria',
                   'WA': 'Western Australia',
                   'Perth': 'Perth'}

other_cities = {}

sample = ["https://www.eit.edu.au/courses/on-campus-master-of-engineering-electrical-systems/"]

# MAIN ROUTINE
for each_url in course_links_file:

    course_data = {'Level_Code': '', 'University': 'Engineering Institute of Technology', 'City': '', 'Course': '',
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
    actual_cities.add('Perth')

    browser.get(each_url)
    # time.sleep(1)
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
    title = soup.find('h1')
    if title:
        course_data['Course'] = tag_text(title)
        title_ = tag_text(title)
    if len(title_) < 5:
        course_data = get_course_name_from_url(course_data)

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

    # DESCRIPTION
    try:
        THE_XPATH = "//div[@class='accordion__overview' and not(self::h2)]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Description'] = value.replace('Program Details', '')
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('cant extract description')

    # STUDY MODE
    try:
        THE_XPATH = "//div[text()='Location']/following::*[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Online'] = 'Yes' if 'Online' in value else course_data['Online']
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('cant extract study mode')

    # DURATION
    try:
        THE_XPATH = "//div[text()='Duration']/following::*[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text

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
    except (AttributeError, TypeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('cant extract duration')

    # REMARKS
    try:
        THE_XPATH = "//div[starts-with(@id, 'collapse-EntryRequirements')]"
        REQ_BUTTON_XPATH = "//button[contains(text(), 'Entry Requirements')]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{REQ_BUTTON_XPATH}'))
        )
        req_button = browser.find_element_by_xpath(f'{REQ_BUTTON_XPATH}')
        req_button.click()
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Remarks'] = value
        req_button.click()
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('cant extract remarks')

    # CHECK PART TIME OR FULL TIME
    try:
        THE_XPATH = "//div[starts-with(@id, 'collapse-TimeCommitmentDuration')]"
        BUTTON_XPATH = "//button[contains(text(), 'Time Commitment & Duration')]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{BUTTON_XPATH}'))
        )
        button = browser.find_element_by_xpath(f'{BUTTON_XPATH}')
        button.click()
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Remarks'] = value + bar + course_data['Remarks']
        if 'part-time' in value.lower() or 'part time' in value.lower():
            course_data['Part_Time'] = 'Yes'
        if 'full-time' in value.lower() or 'full time' in value.lower():
            course_data['Full_Time'] = 'Yes'
        button.click()
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException, ElementClickInterceptedException):
        print('cant extract part time/full time')

    # OUTCOMES
    try:
        THE_XPATH = "//div[starts-with(@id, 'collapse-PotentialJobOutcomes')]"
        BUTTON_XPATH = "//button[contains(text(), 'Potential Job Outcomes')]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{BUTTON_XPATH}'))
        )
        button = browser.find_element_by_xpath(f'{BUTTON_XPATH}')
        button.click()
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Career_Outcomes'] = value
        button.click()
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('cant extract outcomes')

    # CHECK FEES
    # //select[@id='eit_course_fee_country_selector']/option[contains(text(), 'Australia')]
    for i in range(0, 3):
        try:
            js = f"var aa=document.getElementsByClassName('testimonials__caption-container')[{i}];aa.parentNode.removeChild(aa)"
            browser.execute_script(js)
        except JavascriptException as j:
            logging.warning(j)
    try:
        js = f"var aa=document.getElementsByClassName('accordion__link')[0];aa.parentNode.removeChild(aa)"
        browser.execute_script(js)
    except JavascriptException as j:
        logging.warning(j)
    try:
        # FEE XPATH
        THE_XPATH = "//*[contains(text(), 'Total Course Fees')]/ancestor::*[not(self::span)][1]"

        BUTTON_XPATH = "//button[contains(text(), 'Fees & Payments')]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{BUTTON_XPATH}'))
        )
        button = browser.find_element_by_xpath(f'{BUTTON_XPATH}')
        button.click()

        # EXTRACT DOM FEES
        DROPDOWN_XPATH = "//select[@id='eit_course_fee_country_selector']"
        AUS_XPATH = "//select[@id='eit_course_fee_country_selector']/option[contains(text(), 'Australia')]"
        ANG_XPATH = "//select[@id='eit_course_fee_country_selector']/option[contains(text(), 'Angola')]"
        MAY_XPATH = "//select[@id='eit_course_fee_country_selector']/option[contains(text(), 'Malaysia')]"

        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{DROPDOWN_XPATH}'))
        )
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{AUS_XPATH}'))
        )
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{ANG_XPATH}'))
        )
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{MAY_XPATH}'))
        )
        dropdown = browser.find_element_by_xpath(f'{DROPDOWN_XPATH}')

        aus_fee = browser.find_element_by_xpath(f'{AUS_XPATH}')
        ang_fee = browser.find_element_by_xpath(f'{ANG_XPATH}')
        may_fee = browser.find_element_by_xpath(f'{MAY_XPATH}')

        dropdown.click()
        aus_fee.click()
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        value = value.replace('Total Course Fees AUD $', '').replace(',', '')
        course_data['Local_Fees'] = value
        dropdown.click()
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        logging.warning(e)
        print('problem clicking countries for fees')

    # REMARKS REVISITED
    try:
        THE_XPATH = "//div[text()='Intakes']/ancestor::*[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Remarks'] = value + bar + course_data['Remarks']
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        pass

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
