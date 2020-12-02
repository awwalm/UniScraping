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
# browser.maximize_window()
delay = 5

# collect page source for fees
with open('LocalData/Feb20-Dom-Fees.html', encoding='utf8') as dom_file:  # Domestic Fees local HTML
    soup_fees = bs4.BeautifulSoup(dom_file, 'html.parser')
option2 = webdriver.ChromeOptions()
option2.add_argument(" - incognito")
option2.add_argument("headless")
browser2 = webdriver.Chrome(executable_path=exec_path, chrome_options=option2)
browser2.get("file:///"+os.getcwd()+"/LocalData/Feb20-Dom-Fees.html")
time.sleep(1)
fee_webpage = browser2.page_source


# read the url from each file into a list
course_links_file_path = Path(os.getcwd().replace('\\', '/'))
course_links_file_path = course_links_file_path.__str__() + '/jmc_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'JMC_All_Data.csv'

level_key = TemplateData.level_key  # dictionary of course levels

faculty_key = TemplateData.faculty_key  # dictionary of course levels

UPPERCASE, LOWERCASE = TemplateData.UPPERCASE, TemplateData.LOWERCASE

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
                        'Subject_or_Unit_40': '', 'Subject_Objective_40': '', 'Subject_Description_40': ''
                        }

# noinspection SpellCheckingInspection
possible_cities = {'Sydney': 'Sydney',
                   'Brisbane': 'Brisbane',
                   'Melbourne': 'Melbourne'}

other_cities = {}

sample = ["https://www.eit.edu.au/courses/on-campus-master-of-engineering-electrical-systems/"]

# MAIN ROUTINE
for each_url in course_links_file:

    course_data = {'Level_Code': '', 'University': 'JMC Academy', 'City': '', 'Course': '',
                   'Faculty': '',
                   'Int_Fees': '', 'Local_Fees': '', 'Currency': 'AUD', 'Currency_Time': 'Years', 'Duration': '',
                   'Duration_Time': '', 'Full_Time': 'Yes', 'Part_Time': 'No',
                   'Prerequisite_1': '', 'Prerequisite_1_grade_1': '',  # ATAR
                   'Prerequisite_2': '', 'Prerequisite_2_grade_2': '',  # IELTS or anything else
                   'Prerequisite_3': '', 'Prerequisite_3_grade_3': '',  # GPA or IB
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
                   'Subject_or_Unit_40': '', 'Subject_Objective_40': '', 'Subject_Description_40': ''
                   }

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

    course_name_list = list()
    # COURSE NAME
    try:
        THE_XPATH = "//a[starts-with(@aria-controls, 'compare')]/p"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        values = browser.find_elements_by_xpath(f'{THE_XPATH}')
        for i in values:
            course_name_list.append(i.text)
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('cant extract course names')

    for c in course_name_list:

        actual_cities = set()

        course_data['Course'] = c

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
            THE_XPATH = "//div[@class='intro']"
            WebDriverWait(browser, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{THE_XPATH}'))
            )
            value = browser.find_element_by_xpath(f'{THE_XPATH}').text
            course_data['Description'] = value
        except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
            print('cant extract description')

        # OUTCOMES
        try:
            THE_XPATH = "//div[@class='industry-careers']"
            WebDriverWait(browser, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{THE_XPATH}'))
            )
            value = browser.find_element_by_xpath(f'{THE_XPATH}').text
            course_data['Career_Outcomes'] = value
        except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
            print('cant extract outcomes')

        # CITIES
        try:
            THE_XPATH = "//h4[contains(text(), 'on campus')]/following::ul[1]"
            WebDriverWait(browser, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{THE_XPATH}'))
            )
            values = browser.find_element_by_xpath(f'{THE_XPATH}').text
            for i in possible_cities:
                if i in values:
                    actual_cities.add(i)
        except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
            print('cant extract course names')

        # DURATION
        try:
            THE_XPATH = "//div[@role='tabpanel' and starts-with(@id, 'compare-')][1]/*/p[last()]"
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

            if 'full time' in value.lower() or 'full-time' in value.lower():
                course_data['Full_Time'] = 'Yes'
            else:
                course_data['Full_Time'] = 'No'
            if 'part time' in value.lower() or 'part-time' in value.lower():
                course_data['Part_Time'] = 'Yes'
            else:
                course_data['Part_Time'] = 'No'
        except (
                AttributeError, TypeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
            print('cant extract duration')

        # REMARKS 1
        try:
            THE_XPATH = "//div[@class='icon icon-plus']"
            WebDriverWait(browser, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{THE_XPATH}'))
            )
            elements = browser.find_elements_by_xpath(f'{THE_XPATH}')
            for element in elements:
                element.click()
        except (AttributeError, TimeoutException, NoSuchElementException,
                ElementNotInteractableException, ElementClickInterceptedException) as e:
            logging.warning(e)
        try:
            THE_XPATH = "(//div[@class='faq'])[1]"
            WebDriverWait(browser, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{THE_XPATH}'))
            )
            value = browser.find_element_by_xpath(f'{THE_XPATH}').text
            course_data['Remarks'] = value + bar
        except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
            print('cant extract remarks')

        # AVAILABILITY
        try:
            THE_XPATH = "//h4[contains(text(), 'entry requirements')]/following::ul[1]"
            WebDriverWait(browser, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{THE_XPATH}'))
            )
            values = browser.find_element_by_xpath(f'{THE_XPATH}').text
            if 'Australia' in values and 'International' in values:
                course_data['Availability'] = 'A'
            if 'Australia' in values and 'International' not in values:
                course_data['Availability'] = 'D'
            if 'Australia' not in values and 'International' in values:
                course_data['Availability'] = 'I'
        except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
            print('cant extract availability')

        # specially tailored constants
        course_data['Prerequisite_2'] = 'IELTS'
        course_data['Prerequisite_2_grade_2'] = '6.0'
        course_data['Prerequisite_3'] = 'Year 12'
        course_data['Currency_Time'] = 'Trimester'
        INT_FEE_BA = 11300
        INT_FEE_PG = 11000

        # INT FEES
        if 'BA' in course_data['Level_Code'] or 'DIP' in course_data['Level_Code'] or 'DIPLOMA' in course_data['Course']:
            course_data['Int_Fees'] = INT_FEE_BA
        else:
            course_data['Int_Fees'] = INT_FEE_PG

        # LOCAL FEES
        try:
            DEGREE_NAME = course_data['Course'].lower()
            if ' (' in DEGREE_NAME:
                DEGREE_NAME, sep, tail = DEGREE_NAME.partition(' (')
            THE_XPATH = f"//p[contains(translate(text(),'{UPPERCASE}', '{LOWERCASE}'), '{DEGREE_NAME}')]/following::td[1]"
            WebDriverWait(browser2, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{THE_XPATH}'))
            )

            value = browser2.find_element_by_xpath(f'{THE_XPATH}').text
            course_data['Local_Fees'] = value.replace('$', '').replace(',', '').replace('per trimester', '').replace('per semester', '')
        except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
            print(e, 'cant extract local fees')

        # SUBJECTS
        SUBJECTS_XPATH = "//div[@class='subject-expanded']/preceding-sibling::div[1]"
        SUBJECT_DESC_XPATH = "//div[@class='subject-expanded']"
        EXCLUDED_CHAR_XPATH = "//div[@class='subject-expanded']/h4"
        subjects = []
        subjects_desc = []
        try:
            WebDriverWait(browser, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{SUBJECTS_XPATH}'))
            )
            subjects = browser.find_elements_by_xpath(f'{SUBJECTS_XPATH}')
            time.sleep(0.2)

            WebDriverWait(browser, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{SUBJECT_DESC_XPATH}'))
            )
            subjects_desc = browser.find_elements_by_xpath(f'{SUBJECT_DESC_XPATH}')
            time.sleep(0.2)

            i = 1
            for sn, sd in zip(subjects, subjects_desc):
                course_data[f'Subject_or_Unit_{i}'] = tag_text(
                    bs4.BeautifulSoup('<html>'+sn.get_attribute('innerHTML')+'</html>', 'html.parser'))
                course_data[f'Subject_Description_{i}'] = tag_text(bs4.BeautifulSoup(
                    '<html>'+sd.get_attribute('innerHTML')+'</html>', 'html.parser'))

                print(f"SUBJECT {i}: {course_data[f'Subject_or_Unit_{i}']}\n"
                      f"SUBJECT OBJECTIVES {i}: {course_data[f'Subject_Objective_{i}']}\n"
                      f"SUBJECT DESCRIPTION {i}: {course_data[f'Subject_Description_{i}']}\n")

                if i is 40:
                    break
                i += 1
        except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
            print(f'cant extract subjects: {e}')

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
