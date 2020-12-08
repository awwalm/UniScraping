import copy
import csv
import json
import re
import sre_constants
import time
from pathlib import Path

# noinspection PyProtectedMember
from urllib.parse import urljoin

from bs4 import Comment
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import *
from CustomMethods import DurationConverter, TemplateData
import bs4 as bs4
import requests
import os

from CustomMethods.DurationConverter import convert_duration


def get_page(url):
    """Will download the contents of the page using the requests library.
    :return: a BeautifulSoup object i.e. the content of the webpage related to the given URL.
    """
    # noinspection PyBroadException,PyUnusedLocal
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return bs4.BeautifulSoup(r.content, 'html.parser')
    except Exception:
        pass
    return None


def remove_banned_words(to_print, database_regex):
    pattern = re.compile(r"\b(" + "|".join(database_regex) + ")\\W", re.I)
    return pattern.sub("", to_print)


def save_data_json(title__, data__):
    with open(title__, 'w', encoding='utf-8') as f:
        json.dump(data__, f, ensure_ascii=False, indent=2)


def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title__', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True


def text_from_html(body_):
    soup__ = bs4.BeautifulSoup(body_, 'html.parser')
    texts = soup__.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    return u" ".join(t_.strip() for t_ in visible_texts)


def tag_text(tag):
    try:
        return tag.get_text().__str__().strip()
    except (AttributeError, TypeError):
        print('trouble processing tag')


def has_numbers(input_string):
    return any(char.isdigit() for char in input_string)


# selenium web driver
# we need the Chrome driver to simulate JavaScript functionality
# thus, we set the executable path and driver options arguments
# ENSURE YOU CHANGE THE DIRECTORY AND EXE PATH IF NEEDED (UNLESS YOU'RE NOT USING WINDOWS!)
option = webdriver.ChromeOptions()
option.add_argument(" - incognito")
option.add_argument("headless")
exec_path = Path(os.getcwd().replace('\\', '/'))
exec_path = exec_path.parent.parent.parent.__str__() + '/Libraries/Google/v86/chromedriver.exe'
# browser = webdriver.Chrome(executable_path=exec_path, chrome_options=option)

# read the url from each file into a list
course_links_file_path = Path(os.getcwd().replace('\\', '/'))
course_links_file_path = course_links_file_path.__str__() + '/uo_melbourne_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'UOMelbourne_All_Data.csv'

delay_ = 5
delay = 2
browser = webdriver.Chrome(executable_path=exec_path)
# browser_ = webdriver.Chrome(executable_path=exec_path)

level_key = TemplateData.level_key  # dictionary of course levels

faculty_key = TemplateData.faculty_key  # dictionary of course levels

currency_pattern = "(?:[\£\$\€\(RM)\]{1}[,\d]+.?\d*)"  # regex pattern for finding currency or cash amount strings

course_data_all = []

city_set = set()

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

possible_cities = {'Creswick': 'Creswick',
                   'Parkville': 'Melbourne',
                   'Burnley': 'Melbourne',
                   'Southbank': 'Southbank'}

other_cities = {}

sample = ['https://study.unimelb.edu.au/find/courses/undergraduate/bachelor-of-science-extended/']

# MAIN ROUTINE
for each_url in course_links_file:

    if 'www.think.edu.au' in each_url:
        continue

    course_data = {'Level_Code': '', 'University': 'University of Melbourne', 'City': 'Melbourne', 'Course': '',
                   'Faculty': '',
                   'Int_Fees': '', 'Local_Fees': '', 'Currency': 'AUD', 'Currency_Time': 'Years', 'Duration': '',
                   'Duration_Time': '', 'Full_Time': 'Yes', 'Part_Time': 'No',
                   'Prerequisite_1': '', 'Prerequisite_1_grade_1': '',  # ATAR
                   'Prerequisite_2': '', 'Prerequisite_2_grade_2': '',  # IELTS
                   'Prerequisite_3': '', 'Prerequisite_3_grade_3': '',  # GPA
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

    actual_cities = set()
    actual_cities.add('Parkville')

    browser.get(each_url)
    time.sleep(0.2)
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
    title = soup.find('h1', {'id': 'page-header', 'class': 'course-header__title'})
    if title:
        course_data['Course'] = tag_text(title)
        title_ = tag_text(title)

    # AVAILABILITY
    time.sleep(0.1)
    ava_tag = soup.find('li', {'id': 'course-overview-availability'})
    if ava_tag:
        ava_string = tag_text(ava_tag).lower()
        if 'available to domestic and international students' in ava_string:
            pass
        else:
            course_data['Availability'] = 'D'
    time.sleep(0.1)

    # DECIDE THE LEVEL CODE
    for i in level_key:
        for j in level_key[i]:
            if j in course_data['Course']:
                course_data['Level_Code'] = i

    # DECIDE THE FACULTY
    for i in faculty_key:
        for j in faculty_key[i]:
            if j.lower() in course_data['Course'].lower():
                course_data['Faculty'] = i

    # DESCRIPTION
    desc1_tag = soup.find('div', {'data-test': 'course-overview-content', 'class': 'course-content'})
    desc1 = tag_text(desc1_tag)
    course_data['Description'] = desc1

    # CITY
    city_tag = soup.find('li', {'id': 'course-overview-campus'})
    if city_tag:
        city_string = tag_text(city_tag).lower()
        for i in possible_cities:
            if i.lower() in city_string and i not in actual_cities:
                actual_cities.add(i)

    # ATAR (if there is)
    time.sleep(0.1)
    try:
        atar_tag = soup.find('strong', text=re.compile('^.*Guaranteed ATAR.*$', re.IGNORECASE))\
            .find_parent('div')\
            .find_next('div')
        if atar_tag:
            atar = tag_text(atar_tag)
            course_data['Prerequisite_1'] = 'ATAR'
            course_data['Prerequisite_1_grade_1'] = atar
    except (AttributeError, TypeError, TimeoutException, NoSuchElementException, ElementNotInteractableException, IndexError):
        pass

    # DURATION
    try:    # to accept button if it hasn't been accepted
        accept_cookies_button = browser.find_element_by_xpath(
            "//button[@id='consent_prompt_submit']")
        time.sleep(0.3)
        accept_cookies_button.click()
    except (TimeoutException, NoSuchElementException):
        pass
    try:    # to close popup if it shows up
        close_modal_button_ = browser.find_element_by_xpath(
            "//button[@aria-label='Close modal' and @data-test='modal-close']")
        time.sleep(0.2)
        close_modal_button_.click()
        time.sleep(0.2)
    except (TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        pass

    try:
        aus_option = browser.find_element_by_xpath(
            "//option[@id='residency_value_aus-citizen']")
        update_button = browser.find_element_by_xpath(
            "//button[@id='update-entryreqs']")

        time.sleep(0.2)
        aus_option.click()
        update_button.click()
        time.sleep(0.2)

    except (TimeoutException, ElementNotInteractableException, ElementClickInterceptedException) as e:
        print(f'error clicking buttons: {e}')
    except NoSuchElementException:
        html_ = browser.page_source
        print('got duration source')
        soup_ = bs4.BeautifulSoup(html_, 'lxml')
        duration_tag = soup_.find('li', {'id': 'course-overview-duration'})
        if duration_tag:
            duration = tag_text(duration_tag)
            print(f'duration so far: {duration}')
            if 'part time' in duration.lower() or 'part-time' in duration.lower():
                course_data['Part_Time'] = 'Yes'
            if 'full time' in duration.lower() or 'full-time' in duration.lower():
                course_data['Full_Time'] = 'Yes'

            duration = convert_duration(duration.replace('trimester', 'semester'))
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
    else:
        html_ = browser.page_source
        print('got duration source')
        soup_ = bs4.BeautifulSoup(html_, 'lxml')
        duration_tag = soup_.find('li', {'id': 'course-overview-duration'})
        if duration_tag:
            duration = tag_text(duration_tag)
            print(f'duration so far: {duration}')
            if 'part time' in duration.lower() or 'part-time' in duration.lower():
                course_data['Part_Time'] = 'Yes'
            if 'full time' in duration.lower() or 'full-time' in duration.lower():
                course_data['Part_Time'] = 'Yes'

            duration = convert_duration(duration.replace('trimester', 'semester'))
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

    # INT FEES AND LOCAL FEES
    html_ = None
    url_ = pure_url+'fees/'
    browser.get(url_)
    time.sleep(0.2)

    try:    # to accept button if it hasn't been accepted
        accept_cookies_button = browser.find_element_by_xpath(
            "//button[@id='consent_prompt_submit']")
        time.sleep(0.2)
        accept_cookies_button.click()
    except (TimeoutException, NoSuchElementException):
        pass
    try:    # to close popup if it shows up
        close_modal_button_ = browser.find_element_by_xpath(
            "//button[@aria-label='Close modal' and @data-test='modal-close']")
        time.sleep(0.2)
        close_modal_button_.click()
    except (TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        pass

    # INT FEES
    try:
        # browser_.execute_script("utag.link({ga_EventAction: 'Accept', ga_EventCategory: 'GDPR Banner', ga_EventLabel: document.location.href});")

        change_fee_button = browser.find_element_by_xpath(
            "//a[@data-test='fee-change-student-type']")
        aus_citizen_option = browser.find_element_by_xpath(
            "//option[@value='aus-citizen']")
        int_citizen_option = browser.find_element_by_xpath(
            "//option[@value='international']")
        save_option_button = browser.find_element_by_xpath(
            "//button[@id='save-modal' and @data-test='segmentation-submit']")

        change_fee_button.click()
        time.sleep(0.2)
        int_citizen_option.click()
        time.sleep(0.2)
        save_option_button.click()

    except (TimeoutException, ElementNotInteractableException) as e:
        print(f'error clicking buttons: {e}')
    except NoSuchElementException:
        course_data['Int_Fees'] = ''
    else:
        html_ = browser.page_source
        print('got int fees page source')
        soup_ = bs4.BeautifulSoup(html_, 'lxml')
        int_fee_tag = soup_.find('span', {'data-test': 'fee-item-price'})
        if int_fee_tag:
            int_fees = tag_text(int_fee_tag).replace('$', '').replace('AUD', '').replace(',', '')
            course_data['Int_Fees'] = int_fees

    # LOCAL FEES
    try:
        # browser_.execute_script("utag.link({ga_EventAction: 'Accept', ga_EventCategory: 'GDPR Banner', ga_EventLabel: document.location.href});")

        change_fee_button = browser.find_element_by_xpath(
            "//a[@data-test='fee-change-student-type']")
        aus_citizen_option = browser.find_element_by_xpath(
            "//option[@value='aus-citizen']")
        int_citizen_option = browser.find_element_by_xpath(
            "//option[@value='international']")
        save_option_button = browser.find_element_by_xpath(
            "//button[@id='save-modal' and @data-test='segmentation-submit']")

        change_fee_button.click()
        time.sleep(0.2)
        aus_citizen_option.click()
        time.sleep(0.2)
        save_option_button.click()

    except (TimeoutException, ElementNotInteractableException, ElementClickInterceptedException) as e:
        print(f'error clicking buttons: {e}')
    except NoSuchElementException:
        course_data['Local_Fees'] = ''
    else:
        html_ = browser.page_source
        print('got local fees page source')
        soup_ = bs4.BeautifulSoup(html_, 'lxml')
        local_fee_tag = soup_.find('span', {'data-test': 'fee-item-price'})
        if local_fee_tag:
            local_fees = tag_text(local_fee_tag).replace('$', '').replace('AUD', '').replace(',', '')
            course_data['Local_Fees'] = local_fees

    # OUTCOMES
    url_ = pure_url + 'where-will-this-take-me/'
    browser.get(url_)
    time.sleep(0.2)

    html_ = browser.page_source
    print('got outcomes page source')
    soup_ = bs4.BeautifulSoup(html_, 'lxml')

    try:
        outcomes_tag = soup_.find('h3', class_='header-icon').find_next('div')
        if outcomes_tag:
            outcomes = tag_text(outcomes_tag).replace('\n', '.\t')
            course_data['Career_Outcomes'] = outcomes
    except AttributeError:
        pass

    # ATAR CHECK 2
    time.sleep(0.2)
    try:
        url_ = pure_url + 'entry-requirements/'
        browser.get(url_)
        time.sleep(1)
        html_ = browser.page_source
        print('got outcomes page source')
        soup_ = bs4.BeautifulSoup(html_, 'lxml')
        time.sleep(0.5)
        atar_tag2 = soup_.find_all('p', class_='info-card__value')[1]
        if atar_tag2:
            print('found atar through 2nd method')
            atar2 = tag_text(atar_tag2)
            course_data['Prerequisite_1'] = 'ATAR'
            course_data['Prerequisite_1_grade_1'] = atar2
    except (AttributeError, IndexError, NoSuchElementException, ElementNotInteractableException, ElementClickInterceptedException):
        pass

    try:
        THE_XPATH = "//a[@data-test='nav-link-what-will-i-study']"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        element = browser.find_element_by_xpath(f'{THE_XPATH}')
        element.click()
        time.sleep(0.2)

        # SUBJECTS
        try:
            THE_XPATH = "//a[@class='subject-programs__link' and @href]"
            WebDriverWait(browser, 1).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{THE_XPATH}'))
            )
            values = browser.find_elements_by_xpath(f'{THE_XPATH}')

            a_tags = set().union(i for i in values)
            subjects_links = []
            domain_url = "https://study.unimelb.edu.au/"
            delay = 3
            for a in a_tags:
                link = a.get_attribute('href')
                if link:
                    link_ = urljoin(domain_url, link)
                    if link_ not in subjects_links:
                        if link_ not in subjects_links:
                            subjects_links.append(link_)
                if len(subjects_links) is 40:
                    break
            i = 1
            for sl in subjects_links:
                browser.get(sl)
                try:
                    THE_XPATH = "//h1[1]"
                    WebDriverWait(browser, delay).until(
                        EC.presence_of_all_elements_located(
                            (By.XPATH, f'{THE_XPATH}'))
                    )
                    value = browser.find_element_by_xpath(f'{THE_XPATH}')
                    course_data[f'Subject_or_Unit_{i}'] = tag_text(
                        bs4.BeautifulSoup('<div>' + value.get_attribute('innerHTML') + '</div>', 'lxml'))
                except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
                    print(f'cant extract subject name {i}: {e}')
                try:
                    THE_XPATH = "//div[@class='course__overview-wrapper clearfix']/*[position() > 1 and position() < last()]"
                    WebDriverWait(browser, delay).until(
                        EC.presence_of_all_elements_located(
                            (By.XPATH, f'{THE_XPATH}'))
                    )
                    values = browser.find_elements_by_xpath(f'{THE_XPATH}')
                    time.sleep(0.2)
                    sub_desc = str()
                    for v in values:
                        sub_desc += tag_text(bs4.BeautifulSoup('<div>' + v.get_attribute('innerHTML') + '</div>', 'lxml'))
                    course_data[f'Subject_Description_{i}'] = sub_desc
                except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
                    print(f'cant extract subject description {i}: {e}')
                try:
                    THE_XPATH = "//div[@class='course__overview-wrapper clearfix']/*[last()]/*[not(self::h2)]"
                    WebDriverWait(browser, delay).until(
                        EC.presence_of_all_elements_located(
                            (By.XPATH, f'{THE_XPATH}'))
                    )
                    values = browser.find_elements_by_xpath(f'{THE_XPATH}')
                    time.sleep(0.2)
                    sub_obj = str()
                    for v in values:
                        sub_obj += tag_text(
                            bs4.BeautifulSoup('<div>' + v.get_attribute('innerHTML') + '</div>', 'lxml'))
                    course_data[f'Subject_Objective_{i}'] = sub_obj
                except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
                    print(f'cant extract subject objective {i}: {e}')
                print(f"SUBJECT {i}: {course_data[f'Subject_or_Unit_{i}']}\n"
                      f"SUBJECT OBJECTIVES {i}: {course_data[f'Subject_Objective_{i}']}\n"
                      f"SUBJECT DESCRIPTION {i}: {course_data[f'Subject_Description_{i}']}\n")
                i += 1
        except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
            print(f'cant extract subjects: {e}')

    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        print(f'cant click what will i study link: {e}')

    # duplicating entries with multiple cities for each city
    for i in actual_cities:
        course_data['City'] = possible_cities[i]
        print('repeated cities: ', possible_cities[i])
        course_data_all.append(copy.deepcopy(course_data))
    del actual_cities

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
    # print('IB: ', course_data['Prerequisite_3_grade_3'])
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
