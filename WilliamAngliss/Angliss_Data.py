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
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, NoSuchElementException, \
    JavascriptException, ElementClickInterceptedException
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
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f"{_xpath_}"))
        )
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        logging.warning(e)


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
            return cn
    except (AttributeError, TypeError, IndexError, TypeError) as e_:
        logging.debug(e_)


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
delay = 2

# collect page source for fees
with open('LocalData/2021-international-course-guide.html',
          encoding='utf8') as dom_file:
    soup_fees = bs4.BeautifulSoup(dom_file, 'html.parser')
option2 = webdriver.ChromeOptions()
option2.add_argument(" - incognito")
# option2.add_argument("headless")
browser2 = webdriver.Chrome(executable_path=exec_path, chrome_options=option2)
browser2.get("file:///" + os.getcwd() + "/LocalData/2021-international-course-guide.html")
time.sleep(1)
fee_webpage = browser2.page_source

with open('LocalData/2021-higher-education-fee-schedule-melbourne.html',
          encoding='utf8') as dom_file:
    soup_fees3 = bs4.BeautifulSoup(dom_file, 'html.parser')
option3 = webdriver.ChromeOptions()
option3.add_argument(" - incognito")
# option2.add_argument("headless")
browser3 = webdriver.Chrome(executable_path=exec_path, chrome_options=option3)
browser3.get("file:///" + os.getcwd() + "/LocalData/2021-higher-education-fee-schedule-melbourne.html")
time.sleep(1)
fee_webpage3 = browser3.page_source

# read the url from each file into a list
course_links_file_path = Path(os.getcwd().replace('\\', '/'))
course_links_file_path = course_links_file_path.__str__() + '/angliss_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'WilliamAngliss_All_Data.csv'

level_key = TemplateData.level_key  # dictionary of course levels

faculty_key = TemplateData.faculty_key  # dictionary of course levels

currency_pattern = "(?:[\£\$\€\(RM)\]{1}[,\d]+.?\d*)"  # regex pattern for finding currency or cash amount strings

course_data_all = []

city_set = set()

bar = ' | '  # generic text separator for tidiness

months = {'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
          'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12}

course_data_template = {'Level_Code': '', 'University': 'Gordon Geelong Institute of TAFE', 'City': 'Melbourne',
                        'Course': '',
                        'Faculty': '',
                        'Int_Fees': '', 'Local_Fees': '', 'Currency': 'AUD', 'Currency_Time': 'Course', 'Duration': '',
                        'Duration_Time': '', 'Full_Time': 'Yes', 'Part_Time': 'No',
                        'Prerequisite_1': '', 'Prerequisite_1_grade_1': '',  # ATAR
                        'Prerequisite_2': '', 'Prerequisite_2_grade_2': '',  # IELTS
                        'Prerequisite_3': '', 'Prerequisite_3_grade_3': '',  # GPA
                        'Website': '', 'Course_Lang': 'English', 'Availability': 'A', 'Description': '',
                        'Career_Outcomes': '',
                        'Country': 'Australia', 'Online': 'No', 'Offline': 'Yes', 'Distance': 'No',
                        'Face_to_Face': 'Yes',
                        'Blended': 'No', 'Remarks': '',
                        'Course_Delivery_Mode': 'Traineeship',
                        # is this an Apprenticeship, Traineeship, or just a Normal course?
                        'FREE_TAFE': 'No'  # is this a free of charge TAFE course, supposedly sponsored by agencies?
                        }

# noinspection SpellCheckingInspection
possible_cities = {'Sydney': 'Sydney', 'Melbourne': 'Melbourne'}

other_cities = {}

sample = [""]

# MAIN ROUTINE
for each_url in course_links_file:

    # noinspection SpellCheckingInspection
    course_data = {'Level_Code': '', 'University': 'William Angliss Institute', 'City': '',
                   'Course': '',
                   'Faculty': '',
                   'Int_Fees': '', 'Local_Fees': '', 'Currency': 'AUD', 'Currency_Time': 'Course', 'Duration': '',
                   'Duration_Time': '', 'Full_Time': 'Yes', 'Part_Time': 'No',
                   'Prerequisite_1': '', 'Prerequisite_1_grade_1': '',  # ATAR
                   'Prerequisite_2': '', 'Prerequisite_2_grade_2': '',  # IELTS
                   'Prerequisite_3': '', 'Prerequisite_3_grade_3': '',  # GPA
                   'Website': '', 'Course_Lang': 'English', 'Availability': 'A', 'Description': '',
                   'Career_Outcomes': '',
                   'Country': 'Australia', 'Online': 'No', 'Offline': 'Yes', 'Distance': 'No', 'Face_to_Face': 'Yes',
                   'Blended': 'No', 'Remarks': '',
                   'Course_Delivery_Mode': 'Normal',
                   # is this an Apprenticeship, Traineeship, or just a Normal course?
                   'FREE_TAFE': 'No'  # is this a free of charge TAFE course, supposedly sponsored by agencies?
                   }

    actual_cities = set()

    browser.get(each_url)
    # time.sleep(2)
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
            course_data['Course'] = get_course_name_from_url(course_data)

    # APPRENTICESHIP or TRAINEESHIP
    if 'apprentice' in course_data['Course'].lower() or 'apprentice' in pure_url.lower():
        course_data['Course_Delivery_Mode'] = 'Apprenticeship'
    if 'trainee' in course_data['Course'].lower() or 'trainee' in pure_url.lower():
        course_data['Course_Delivery_Mode'] = 'Traineeship'

    # DECIDE THE LEVEL CODE
    lev_str = str()
    for i in level_key:
        for j in level_key[i]:
            if j in course_data['Course']:
                course_data['Level_Code'] = i

    INT_OR_DOM_XPATH = "//span[@class='trigger js-trigger open']"
    INT_STUDENT_XPATH = "//input[@id='opt-2' and @name='StudentType' and @type='radio' and @value=2]/preceding::label[@for='opt-2']"
    DOM_STUDENT_XPATH = "//input[@id='opt-1' and @name='StudentType' and @type='radio' and @value=1]/preceding::label[@for='opt-1']"
    MELBOURNE_XPATH = "//input[@id='opt-1' and @name='StudentType' and @type='radio' and @value=1]/preceding::label[@for='opt-1a']"
    SUBMIT_XPATH = "(//div[@class='option-form']/following::input[@type='submit' and @value='Submit'])[1]"

    browser.find_element_by_tag_name('html').send_keys(Keys.PAGE_DOWN)
    try:
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{INT_OR_DOM_XPATH}'))
        )
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{DOM_STUDENT_XPATH}'))
        )
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{INT_STUDENT_XPATH}'))
        )
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{MELBOURNE_XPATH}'))
        )
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{SUBMIT_XPATH}'))
        )
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        logging.debug(e)
    try:
        element = browser.find_element_by_xpath(f'{INT_OR_DOM_XPATH}')
        # element.click()
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        logging.debug(e)
    try:
        element = browser.find_element_by_xpath(f'{DOM_STUDENT_XPATH}')
        element.click()
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        logging.debug(e)
    try:
        element = browser.find_element_by_xpath(f'{MELBOURNE_XPATH}')
        element.click()
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        logging.debug(e)
    try:
        element = browser.find_element_by_xpath(f'{SUBMIT_XPATH}')
        element.click()
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException, ElementClickInterceptedException) as e:
        logging.warning(e)

    # DECIDE THE FACULTY
    fac_str = str()
    for i in faculty_key:
        for j in faculty_key[i]:
            if j.lower() in course_data['Course'].lower():
                course_data['Faculty'] = i
                fac_str = i

    # REMARKS
    try:
        THE_XPATH = "//h3[text()='Electives']/ancestor::*[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Remarks'] = value
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        logging.warn(e)
        try:
            rem_tag = soup.find('section', {'id': 'entry-requirements'})
            if rem_tag:
                course_data['Remarks'] = tag_text(rem_tag)
        except AttributeError as e:
            logging.warn(e)

    # CITY
    try:
        THE_XPATH = "//*[text()='Campus']/ancestor::*[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        values = browser.find_element_by_xpath(f'{THE_XPATH}').text
        for i in possible_cities:
            if i in values:
                actual_cities.add(i)
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        logging.warning(e)

    # DURATION
    try:
        THE_XPATH = "//*[text()='Duration']/following::*[1]"
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
    except (AttributeError, TypeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('cant extract duration')

    # FULL TIME/PART-TIME
    try:
        THE_XPATH = "//*[text()='Course Mode']/ancestor::*[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        values = browser.find_element_by_xpath(f'{THE_XPATH}').text
        if 'full-time' in values.lower() or 'full time' in values.lower():
            course_data['Full_Time'] = 'Yes'
        if 'part-time' in values.lower() or 'part time' in values.lower():
            course_data['Part_Time'] = 'Yes'
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        logging.warning(e)

    # COURSE CODE
    c_code = str()
    try:
        THE_XPATH = "//*[text()='Course Code']/ancestor::*[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        if '-' in value:
            head, sep, tail = value.partition('-')
            c_code = tail.replace('COURSE', '').replace('CODE', '').replace('\n', '').replace(' ', '').strip()
        else:
            c_code = value.replace('COURSE', '').replace('CODE', '').replace('\n', '').replace(' ', '').strip()

        if ' (' in c_code or ' (' in value and len(c_code) > 0:
            head, sep, tail = value.partition(' (')
            c_code = head.replace('COURSE', '').replace('CODE', '').replace('\n', '').replace(' ', '').strip()
        if '/' in value or '/' in c_code:
            head, sep, tail = value.partition('/')
            c_code = head.replace('COURSE', '').replace('CODE', '').replace('\n', '').replace(' ', '').strip()
        print(c_code)
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        logging.warning(e)

    # DESCRIPTION
    try:
        THE_XPATH = "//section[@id='overview']/div/div[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Description'] = value
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        try:
            desc_tag = soup.find('section', {'id': 'overview'}).find('div').find('div')
            if desc_tag:
                course_data['Description'] = tag_text(desc_tag)
        except AttributeError:
            print('cant extract description')

    # LOCAL FEES
    try:
        THE_XPATH = "//*[contains(text(), 'FULL FEE COURSE FEE')]/ancestor::*[1]/following::*[1 and contains(text(), '$')][1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Local_Fees'] = value.replace('$', '').replace(',', '')
        course_data['Currency_Time'] = 'Course'
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        try:
            THE_XPATH = f"(//*[contains(text(), '{c_code}')]/ancestor::tr/td[last()-10][1])[1]"
            WebDriverWait(browser3, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{THE_XPATH}'))
            )
            value = browser3.find_element_by_xpath(f'{THE_XPATH}').text
            course_data['Local_Fees'] = value.replace('$', '').replace(',', '')
            course_data['Currency_Time'] = 'Course'
        except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
            logging.debug(e)

    # INT FEES
    try:
        THE_XPATH = f"//*[contains(text(), '{c_code}')]/ancestor::tr/td[last()-2][1]"
        WebDriverWait(browser2, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser2.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Int_Fees'] = value.replace('$', '').replace(',', '')
        course_data['Currency_Time'] = 'Course'
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        logging.debug(e)

    # ATAR
    try:
        THE_XPATH = "//*[contains(text(), 'Guaranteed Entry ATAR 2020')]/following::*[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Prerequisite_1'] = 'ATAR'
        course_data['Prerequisite_1_grade_1'] = value
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        logging.debug(e)

    # OUTCOMES
    try:
        THE_XPATH = "//*[contains(text(), 'Career Outcomes')]/ancestor::div[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Career_Outcomes'] = value
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        logging.warning(e)
    try:
        out_tag = soup.find('h3', text='Career Outcomes').find_parent()
        if out_tag:
            course_data['Career_Outcomes'] = tag_text(out_tag)
    except AttributeError:
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
    print('DESCRIPTION: ', course_data['Description'])
    print('LEVEL CODE: ', course_data['Level_Code'])
    print('CITY: ', course_data['City'])
    print('DURATION + DURATION TIME: ', course_data['Duration'], ' ', course_data['Duration_Time'])
    print('AVAILABILITY: ', course_data['Availability'])
    print('FACULTY: ', course_data['Faculty'])
    print('INT FEES: ', course_data['Int_Fees'])
    print('LOCAL FEES: ', course_data['Local_Fees'])
    print('ATAR: ', course_data['Prerequisite_1_grade_1'])
    print('OP: ', course_data['Prerequisite_2_grade_2'])
    print('IB: ', course_data['Prerequisite_3_grade_3'])
    # print('IELTS: ', course_data['Prerequisite_2_grade_2'])
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
    print('FREE TAFE: ', course_data['FREE_TAFE'])
    print('Traineeship or Apprenticeship: ', course_data['Course_Delivery_Mode'])
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
