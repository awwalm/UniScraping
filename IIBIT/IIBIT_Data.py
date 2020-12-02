import copy
import csv
import json
import os
import re
import sre_constants
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
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as _e_:
        print(_e_.traceback)


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


# selenium web driver
# we need the Chrome driver to simulate JavaScript functionality
# thus, we set the executable path and driver options arguments
# ENSURE YOU CHANGE THE DIRECTORY AND EXE PATH IF NEEDED (UNLESS YOU'RE NOT USING WINDOWS!)
option = webdriver.ChromeOptions()
option.add_argument(" - incognito")
option2 = webdriver.ChromeOptions()
option2.add_argument(" - incognito")
option2.add_argument("headless")
# option.add_argument("headless")
exec_path = Path(os.getcwd().replace('\\', '/'))
exec_path = exec_path.parent.parent.parent.__str__() + '/Libraries/Google/v86/chromedriver.exe'
browser = webdriver.Chrome(executable_path=exec_path, chrome_options=option)
browser2 = webdriver.Chrome(executable_path=exec_path, chrome_options=option2)
# browser.maximize_window()
delay = 1

# collect page source for fees
browser2.get("https://www.iibit.edu.au/course-fees-living-costs/")
fee_url = browser2.page_source
soup_fees = bs4.BeautifulSoup(fee_url, 'lxml')

# read the url from each file into a list
course_links_file_path = Path(os.getcwd().replace('\\', '/'))
course_links_file_path = course_links_file_path.__str__() + '/iibit_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'IIBIT_All_Data.csv'

level_key = TemplateData.level_key  # dictionary of course levels

faculty_key = TemplateData.faculty_key  # dictionary of course levels

currency_pattern = "(?:[\£\$\€\(RM)\]{1}[,\d]+.?\d*)"  # regex pattern for finding currency or cash amount strings

course_data_all = []

city_set = set()

bar = ' | '  # generic text separator for tidiness

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
                        'Blended': 'No', 'Remarks': '',
                        'Subject_or_Unit_1': '', 'Subject_Objective_1': '', 'Subject_Description_1': '',
                        'Subject_or_Unit_2': '', 'Subject_Objective_2': '', 'Subject_Description_2': '',
                        'Subject_or_Unit_3': '', 'Subject_Objective_3': '', 'Subject_Description_3': '',
                        'Subject_or_Unit_4': '', 'Subject_Objective_4': '', 'Subject_Description_4': '',
                        'Subject_or_Unit_5': '', 'Subject_Objective_5': '', 'Subject_Description_5': '',
                        'Subject_or_Unit_6': '', 'Subject_Objective_6': '', 'Subject_Description_6': '',
                        'Subject_or_Unit_7': '', 'Subject_Objective_7': '', 'Subject_Description_7': '',
                        'Subject_or_Unit_8': '', 'Subject_Objective_8': '', 'Subject_Description_8': '',
                        'Subject_or_Unit_9': '', 'Subject_Objective_9': '', 'Subject_Description_9': '',
                        'Subject_or_Unit_10': '', 'Subject_Objective_10': '', 'Subject_Description_10': '',
                        'Subject_or_Unit_11': '', 'Subject_Objective_11': '', 'Subject_Description_11': '',
                        'Subject_or_Unit_12': '', 'Subject_Objective_12': '', 'Subject_Description_12': '',
                        'Subject_or_Unit_13': '', 'Subject_Objective_13': '', 'Subject_Description_13': '',
                        'Subject_or_Unit_14': '', 'Subject_Objective_14': '', 'Subject_Description_14': '',
                        'Subject_or_Unit_15': '', 'Subject_Objective_15': '', 'Subject_Description_15': '',
                        'Subject_or_Unit_16': '', 'Subject_Objective_16': '', 'Subject_Description_16': '',
                        'Subject_or_Unit_17': '', 'Subject_Objective_17': '', 'Subject_Description_17': '',
                        'Subject_or_Unit_18': '', 'Subject_Objective_18': '', 'Subject_Description_18': '',
                        'Subject_or_Unit_19': '', 'Subject_Objective_19': '', 'Subject_Description_19': '',
                        'Subject_or_Unit_20': '', 'Subject_Objective_20': '', 'Subject_Description_20': '',
                        'Subject_or_Unit_21': '', 'Subject_Objective_21': '', 'Subject_Description_21': '',
                        'Subject_or_Unit_22': '', 'Subject_Objective_22': '', 'Subject_Description_22': '',
                        'Subject_or_Unit_23': '', 'Subject_Objective_23': '', 'Subject_Description_23': '',
                        'Subject_or_Unit_24': '', 'Subject_Objective_24': '', 'Subject_Description_24': '',
                        'Subject_or_Unit_25': '', 'Subject_Objective_25': '', 'Subject_Description_25': '',
                        'Subject_or_Unit_26': '', 'Subject_Objective_26': '', 'Subject_Description_26': '',
                        'Subject_or_Unit_27': '', 'Subject_Objective_27': '', 'Subject_Description_27': '',
                        'Subject_or_Unit_28': '', 'Subject_Objective_28': '', 'Subject_Description_28': '',
                        'Subject_or_Unit_29': '', 'Subject_Objective_29': '', 'Subject_Description_29': '',
                        'Subject_or_Unit_30': '', 'Subject_Objective_30': '', 'Subject_Description_30': '',
                        'Subject_or_Unit_31': '', 'Subject_Objective_31': '', 'Subject_Description_31': '',
                        'Subject_or_Unit_32': '', 'Subject_Objective_32': '', 'Subject_Description_32': '',
                        'Subject_or_Unit_33': '', 'Subject_Objective_33': '', 'Subject_Description_33': '',
                        'Subject_or_Unit_34': '', 'Subject_Objective_34': '', 'Subject_Description_34': '',
                        'Subject_or_Unit_35': '', 'Subject_Objective_35': '', 'Subject_Description_35': '',
                        'Subject_or_Unit_36': '', 'Subject_Objective_36': '', 'Subject_Description_36': '',
                        'Subject_or_Unit_37': '', 'Subject_Objective_37': '', 'Subject_Description_37': '',
                        'Subject_or_Unit_38': '', 'Subject_Objective_38': '', 'Subject_Description_38': '',
                        'Subject_or_Unit_39': '', 'Subject_Objective_39': '', 'Subject_Description_39': '',
                        'Subject_or_Unit_40': '', 'Subject_Objective_40': '', 'Subject_Description_40': ''}

# noinspection SpellCheckingInspection
possible_cities = {'Sydney': 'Sydney',
                   'Adelaide': 'Adelaide'}

other_cities = {}

sample = ["https://www.iibit.edu.au/courses/graduate-diploma-of-technology-software-engineering/"]

# MAIN ROUTINE
for each_url in course_links_file:

    course_data = {'Level_Code': '', 'University': 'International Institute of Business and Information Technology',
                   'City': '', 'Course': '',
                   'Faculty': '',
                   'Int_Fees': '', 'Local_Fees': '', 'Currency': 'AUD', 'Currency_Time': 'Years', 'Duration': '',
                   'Duration_Time': '', 'Full_Time': 'Yes', 'Part_Time': 'No',
                   'Prerequisite_1': '', 'Prerequisite_1_grade_1': '',  # ATAR
                   'Prerequisite_2': 'VCE', 'Prerequisite_2_grade_2': '',  # IELTS or anything else
                   'Prerequisite_3': 'AQF', 'Prerequisite_3_grade_3': '',  # GPA or IB
                   'Website': '', 'Course_Lang': 'English', 'Availability': 'A', 'Description': '',
                   'Career_Outcomes': '',
                   'Country': 'Australia', 'Online': 'No', 'Offline': 'Yes', 'Distance': 'No', 'Face_to_Face': 'Yes',
                   'Blended': 'No', 'Remarks': '',
                   'Subject_or_Unit_1': '', 'Subject_Objective_1': '', 'Subject_Description_1': '',
                   'Subject_or_Unit_2': '', 'Subject_Objective_2': '', 'Subject_Description_2': '',
                   'Subject_or_Unit_3': '', 'Subject_Objective_3': '', 'Subject_Description_3': '',
                   'Subject_or_Unit_4': '', 'Subject_Objective_4': '', 'Subject_Description_4': '',
                   'Subject_or_Unit_5': '', 'Subject_Objective_5': '', 'Subject_Description_5': '',
                   'Subject_or_Unit_6': '', 'Subject_Objective_6': '', 'Subject_Description_6': '',
                   'Subject_or_Unit_7': '', 'Subject_Objective_7': '', 'Subject_Description_7': '',
                   'Subject_or_Unit_8': '', 'Subject_Objective_8': '', 'Subject_Description_8': '',
                   'Subject_or_Unit_9': '', 'Subject_Objective_9': '', 'Subject_Description_9': '',
                   'Subject_or_Unit_10': '', 'Subject_Objective_10': '', 'Subject_Description_10': '',
                   'Subject_or_Unit_11': '', 'Subject_Objective_11': '', 'Subject_Description_11': '',
                   'Subject_or_Unit_12': '', 'Subject_Objective_12': '', 'Subject_Description_12': '',
                   'Subject_or_Unit_13': '', 'Subject_Objective_13': '', 'Subject_Description_13': '',
                   'Subject_or_Unit_14': '', 'Subject_Objective_14': '', 'Subject_Description_14': '',
                   'Subject_or_Unit_15': '', 'Subject_Objective_15': '', 'Subject_Description_15': '',
                   'Subject_or_Unit_16': '', 'Subject_Objective_16': '', 'Subject_Description_16': '',
                   'Subject_or_Unit_17': '', 'Subject_Objective_17': '', 'Subject_Description_17': '',
                   'Subject_or_Unit_18': '', 'Subject_Objective_18': '', 'Subject_Description_18': '',
                   'Subject_or_Unit_19': '', 'Subject_Objective_19': '', 'Subject_Description_19': '',
                   'Subject_or_Unit_20': '', 'Subject_Objective_20': '', 'Subject_Description_20': '',
                   'Subject_or_Unit_21': '', 'Subject_Objective_21': '', 'Subject_Description_21': '',
                   'Subject_or_Unit_22': '', 'Subject_Objective_22': '', 'Subject_Description_22': '',
                   'Subject_or_Unit_23': '', 'Subject_Objective_23': '', 'Subject_Description_23': '',
                   'Subject_or_Unit_24': '', 'Subject_Objective_24': '', 'Subject_Description_24': '',
                   'Subject_or_Unit_25': '', 'Subject_Objective_25': '', 'Subject_Description_25': '',
                   'Subject_or_Unit_26': '', 'Subject_Objective_26': '', 'Subject_Description_26': '',
                   'Subject_or_Unit_27': '', 'Subject_Objective_27': '', 'Subject_Description_27': '',
                   'Subject_or_Unit_28': '', 'Subject_Objective_28': '', 'Subject_Description_28': '',
                   'Subject_or_Unit_29': '', 'Subject_Objective_29': '', 'Subject_Description_29': '',
                   'Subject_or_Unit_30': '', 'Subject_Objective_30': '', 'Subject_Description_30': '',
                   'Subject_or_Unit_31': '', 'Subject_Objective_31': '', 'Subject_Description_31': '',
                   'Subject_or_Unit_32': '', 'Subject_Objective_32': '', 'Subject_Description_32': '',
                   'Subject_or_Unit_33': '', 'Subject_Objective_33': '', 'Subject_Description_33': '',
                   'Subject_or_Unit_34': '', 'Subject_Objective_34': '', 'Subject_Description_34': '',
                   'Subject_or_Unit_35': '', 'Subject_Objective_35': '', 'Subject_Description_35': '',
                   'Subject_or_Unit_36': '', 'Subject_Objective_36': '', 'Subject_Description_36': '',
                   'Subject_or_Unit_37': '', 'Subject_Objective_37': '', 'Subject_Description_37': '',
                   'Subject_or_Unit_38': '', 'Subject_Objective_38': '', 'Subject_Description_38': '',
                   'Subject_or_Unit_39': '', 'Subject_Objective_39': '', 'Subject_Description_39': '',
                   'Subject_or_Unit_40': '', 'Subject_Objective_40': '', 'Subject_Description_40': ''}

    actual_cities = set()

    browser.get(each_url)
    time.sleep(0.5)
    url__ = each_url
    pure_url = each_url.strip()
    print('CURRENT LINK: ', pure_url)
    each_url = browser.page_source
    soup = bs4.BeautifulSoup(each_url, 'lxml')

    all_text = soup.text.replace('\n', '').strip()

    # COURSE URL
    course_data['Website'] = pure_url

    # COURSE NAME
    title_ = None
    title = soup.find('h1')
    if title:
        course_data['Course'] = tag_text(title)
        title_ = tag_text(title)

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
    desc = str()
    for i in range(1, 4):
        try:
            # noinspection SpellCheckingInspection
            THE_XPATH = f"//*[contains(text(), 'Course Description')]/following::*[{i}]"
            WebDriverWait(browser, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{THE_XPATH}'))
            )
            value = browser.find_element_by_xpath(f'{THE_XPATH}').text
            desc += bar + value
        except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
            desc = str()
            for j in range(1, 5):
                try:
                    # noinspection SpellCheckingInspection
                    THE_XPATH = f"(//*[starts-with(@class, 'sc_title')]/following::table)[1]/following-sibling::*[{i}]"
                    WebDriverWait(browser, delay).until(
                        EC.presence_of_all_elements_located(
                            (By.XPATH, f'{THE_XPATH}'))
                    )
                    value = browser.find_element_by_xpath(f'{THE_XPATH}').text
                    desc += bar + value
                except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
                    pass
    course_data['Description'] = desc

    # PREREQUISITE 2 (IELTS)
    try:
        THE_XPATH = "//*[contains(text(), 'IELTS overall band score of')]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Prerequisite_2'] = 'IELTS'
        course_data['Prerequisite_2_grade_2'] = re.findall(r'[-+]?\d*\.\d+|\d+', value)[0]
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        try:
            THE_XPATH = "//*[contains(text(), 'IELTS proficiency of')]"
            WebDriverWait(browser, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{THE_XPATH}'))
            )
            value = browser.find_element_by_xpath(f'{THE_XPATH}').text
            course_data['Prerequisite_2'] = 'IELTS'
            course_data['Prerequisite_2_grade_2'] = re.findall(r'[-+]?\d*\.\d+|\d+', value)[0]
        except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
            try:
                THE_XPATH = "//*[contains(text(), 'IELTS (International English Language Testing System) overall band score:')]"
                WebDriverWait(browser, delay).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, f'{THE_XPATH}'))
                )
                value = browser.find_element_by_xpath(f'{THE_XPATH}').text
                course_data['Prerequisite_2'] = 'IELTS'
                course_data['Prerequisite_2_grade_2'] = re.findall(r'[-+]?\d*\.\d+|\d+', value)[0]
            except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
                print('cant extract ielts')

    # PREREQUISITE 3 (TOEFL)
    try:
        THE_XPATH = "//*[contains(text(), 'TOEFL PBT (Test of English as a Foreign Language Paper-Based Test) test score band')]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Prerequisite_3'] = 'TOEFL PBT'
        course_data['Prerequisite_3_grade_3'] = re.findall(r'[-+]?\d*\.\d+|\d+', value)[0]
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('cant extract toefl')

    # CITIES
    try:
        # noinspection SpellCheckingInspection
        THE_XPATH = "//div[@class='sydneybox']/h5[contains(text(), 'Sydney')]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        if value not in actual_cities:
            actual_cities.add(value)
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        pass
    try:
        # noinspection SpellCheckingInspection
        THE_XPATH = "//div[@class='adelaidebox']/h5[contains(text(), 'Adelaide')]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        if value not in actual_cities:
            actual_cities.add(value)
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        pass
    if len(actual_cities) is 0 and 'Sydney' not in actual_cities:
        actual_cities.add('Sydney')

    # CAREER OUTCOMES
    try:
        # noinspection SpellCheckingInspection
        THE_XPATH = "//*[contains(text(), 'Career Opportunities')]/following::ul[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Career_Outcomes'] = value
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        pass

    # DURATION
    try:
        THE_XPATH = "//*[contains(text(), 'Duration')]/ancestor::td/following-sibling::*[1]"
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

    # INTERNATIONAL FEES
    try:
        THE_XPATH = "//*[contains(text(), 'International Fee Paying A$')][1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        value = value.replace('International Fee Paying A$', '').replace(',', '').replace('', '')
        course_data['Int_Fees'] = re.findall(r'[-+]?\d*\.\d+|\d+', value)[0]
        if '(' in value:
            head, sep, tail = value.partition('(')
            course_data['Int_Fees'] = head.replace(',', '').replace('$', '')
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('cant extract int fees or not found')

    # LOCAL FEES ATTEMPT 1
    try:
        THE_XPATH = "//*[contains(text(), 'Fee')]/ancestor::td/following-sibling::*[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        value = value.replace(',', '').replace('$', '')
        course_data['Local_Fees'] = re.findall(r'[-+]?\d*\.\d+|\d+', value)[0]
        if '(' in value:
            head, sep, tail = value.partition('(')
            head = head.replace(',', '').replace('$', '')
            course_data['Local_Fees'] = re.findall(r'[-+]?\d*\.\d+|\d+', head)[0]
    except (AttributeError, IndexError, TypeError, sre_constants.error,
            TimeoutException, NoSuchElementException, ElementNotInteractableException):
        # CRICOS/FEES
        CRICOS_CODE = str()
        try:
            THE_XPATH = f"(//td[contains(text(), {CRICOS_CODE})]/following-sibling::*[last()-1])[1]"
            WebDriverWait(browser2, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{THE_XPATH}'))
            )
            value = browser2.find_element_by_xpath(f'{THE_XPATH}').text
            # course_data['Int_Fees'] = value.replace(',', '')
            course_data['Local_Fees'] = value.replace(',', '')
        except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
            # FEES
            try:
                THE_XPATH = f"(//td[contains(text(), '{CRICOS_CODE}')]/following-sibling::*[last()-1])[1]"
                WebDriverWait(browser2, delay).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, f'{THE_XPATH}'))
                )
                value = browser2.find_element_by_xpath(f'{THE_XPATH}').text
                course_data['Int_Fees'] = value.replace(',', '')
                course_data['Local_Fees'] = value.replace(',', '')
            except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
                try:
                    THE_XPATH = f"(//td[contains(text(), '{CRICOS_CODE}')]/following-sibling::*[last()-1])[2]"
                    WebDriverWait(browser2, delay).until(
                        EC.presence_of_all_elements_located(
                            (By.XPATH, f'{THE_XPATH}'))
                    )
                    value = browser2.find_element_by_xpath(f'{THE_XPATH}').text
                    value = value.replace(',', '')
                    course_data['Int_Fees'] = re.findall(r'[-+]?\d*\.\d+|\d+', value)[0]
                    course_data['Local_Fees'] = re.findall(r'[-+]?\d*\.\d+|\d+', value)[0]
                except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
                    print('cant extract fees')
                print('cant extract fees')
    # ==============================================================================================================
    try:
        THE_XPATH = "//*[contains(text(), 'Tuition Fee')]/ancestor::td/following-sibling::*[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Currency_Time'] = 'Course'
        value = value.replace(',', '').replace('$', '')
        course_data['Local_Fees'] = re.findall(r'[-+]?\d*\.\d+|\d+', value)[0]

        if '(' in value:
            head, sep, tail = value.partition('(')
            course_data['Currency_Time'] = 'Course'
            head = head.replace(',', '').replace('$', '')
            course_data['Local_Fees'] = re.findall(r'[-+]?\d*\.\d+|\d+', head)[0]
    except (AttributeError, IndexError, sre_constants.error, TimeoutException, NoSuchElementException,
            ElementNotInteractableException):
        pass
    try:
        THE_XPATH = "//*[contains(text(), 'Program Fee')]/ancestor::td/following-sibling::*[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text

        if '(' in value:
            head, sep, tail = value.partition('(')
            head = head.replace(',', '').replace('$', '')
            if 'Year' in course_data['Duration_Time']:
                fee = float(head) / float(course_data['Duration'])
                print('modified fees to be per year: ', fee)
                course_data['Currency_Time'] = 'Year'
                course_data['Local_Fees'] = fee
        else:
            if 'Year' in course_data['Duration_Time']:
                value = value.replace(',', '').replace('$', '')
                fee = float(value) / float(course_data['Duration'])
                print('modified fees to be per year: ', fee)
                course_data['Currency_Time'] = 'Year'
                course_data['Local_Fees'] = fee
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        pass

    try:
        # noinspection SpellCheckingInspection
        THE_XPATH = "//strong[text()='Unit Code']/ancestor::table/tbody/tr/td/*[not(self::strong)]/ancestor::td"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        values = browser.find_elements_by_xpath(f'{THE_XPATH}')
        time.sleep(0.2)
        i = 1
        for v in values:
            course_data[f'Subject_or_Unit_{i}'] = v.text
            print(f'subject {i}: {v.text}')
            if i is 40:
                break
            i += 1
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        try:
            # noinspection SpellCheckingInspection
            THE_XPATH = "//strong[text()='Credit']/ancestor::table/tbody/tr/td/strong[contains(text(), 'Credit')]/following::tr/td[1][not(self::*/strong)]"
            WebDriverWait(browser, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{THE_XPATH}'))
            )
            values = browser.find_elements_by_xpath(f'{THE_XPATH}')
            i = 1
            for v in values:
                course_data[f'Subject_or_Unit_{i}'] = v.get_attribute('innerHTML')
                print(f"subject {i}: {v.get_attribute('innerHTML')}")
                if i is 40:
                    break
                i += 1
        except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
            print(f'cant extract subjects because {e}')

    if 'Week' in course_data['Duration_Time']:
        course_data['Currency_Time'] = 'Course'

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
    # print('OP: ', course_data['Prerequisite_2_grade_2'])
    print('TOEFL: ', course_data['Prerequisite_3_grade_3'])
    print('IELTS: ', course_data['Prerequisite_2_grade_2'])
    # print('GPA: ', course_data['Prerequisite_3_grade_3'])
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
