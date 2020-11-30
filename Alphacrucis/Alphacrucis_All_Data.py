import copy
import csv
import json
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
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, NoSuchElementException
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
        pu = args[0] if args[0] else cd['Website']
        if len(cd['Course']) < 5:
            if pu.endswith('/'):
                pu = pu[:-1]
            last_slash_index = pu.rfind('/')
            cd['Course'] = pu[last_slash_index + 1:].replace('-', ' ').replace('.html', '').title()
            return cd
    except (AttributeError, TypeError, IndexError, TypeError) as e:
        return e.traceback


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

with open('LocalData/2021_HE_Indicative_Fee_Schedule_v1.html', encoding='utf8') as dom_file:  # Fees local HTML
    soup_fees = bs4.BeautifulSoup(dom_file, 'html.parser')
option2 = webdriver.ChromeOptions()
option2.add_argument(" - incognito")
option2.add_argument("headless")
browser2 = webdriver.Chrome(executable_path=exec_path, chrome_options=option2)
browser2.get("file:///"+os.getcwd()+"/LocalData/2021_HE_Indicative_Fee_Schedule_v1.html")
time.sleep(1)
fee_webpage = browser2.page_source


# read the url from each file into a list
course_links_file_path = Path(os.getcwd().replace('\\', '/'))
course_links_file_path = course_links_file_path.__str__() + '/alphacrucis_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'Alphacrucis_All_Data.csv'

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
                        'Subject_or_Unit_20': '', 'Subject_Objective_20': '', 'Subject_Description_20': ''
                        }

# noinspection SpellCheckingInspection
possible_cities = {'Sydney': 'Sydney',
                   'Brisbane': 'Brisbane',
                   'Melbourne': 'Melbourne',
                   'Perth': 'Perth',
                   'Adelaide': 'Adelaide',
                   'Hobart': 'Hobart'}

other_cities = {}

sample = [""]

# MAIN ROUTINE
for each_url in course_links_file:

    # noinspection SpellCheckingInspection
    course_data = {'Level_Code': '', 'University': 'Alphacrucis College', 'City': '', 'Course': '',
                   'Faculty': '',
                   'Int_Fees': '', 'Local_Fees': '', 'Currency': 'AUD', 'Currency_Time': 'Course', 'Duration': '',
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
                   'Subject_or_Unit_20': '', 'Subject_Objective_20': '', 'Subject_Description_20': ''
                   }

    actual_cities = set()

    browser.get(each_url)
    time.sleep(1)
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
    title = soup.find('h2', {'class': 'course-short-description__title'})
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

    # fees
    name_course = course_data['Course']
    try:
        THE_XPATH = f"//p[contains(text(), '{name_course}')]/ancestor::td/following-sibling::td/*[contains(text(), 'Domestic')]/ancestor::tr/td[last()]"
        WebDriverWait(browser2, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser2.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Local_Fees'] = re.findall(currency_pattern, value)[0].replace('$', '').replace('?', '')
        course_data['Currency_Time'] = 'Subject'
        THE_XPATH = f"//p[contains(text(), '{name_course}')]/ancestor::td/following-sibling::td/*[contains(text(), 'International')]/ancestor::tr/td[last()]"
        WebDriverWait(browser2, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser2.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Int_Fees'] = re.findall(currency_pattern, value)[0].replace('$', '').replace('?', '')
        course_data['Currency_Time'] = 'Subject'
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('cant extract fees')

    # DESCRIPTION
    try:
        THE_XPATH = "//div[@class='course-description__text'][1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Description'] = value
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('cant extract description')

    course_data['Duration_Time'] = str()
    # COMBINED DATA
    try:
        THE_XPATH = "(//h2[contains(text(), 'Study Modes')]/following::*[1])[1]"
        STUDY_MODE_XPATH = "//a[contains(text(), 'Study Modes')]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{STUDY_MODE_XPATH}'))
        )
        browser.find_element_by_xpath(f'{STUDY_MODE_XPATH}').click()
        value = str()
        try:
            tag1 = soup.find('h2', text='Study Modes').find_next()
            value = tag_text(tag1)
        except AttributeError:
            tag1 = soup.find_all('div', {'class': 'block-richtext__inner'})[4]
            value = tag_text(tag1)
        print(value)
        if 'online' in value.lower():
            course_data['Online'] = 'Yes'
        for i in possible_cities:
            if i in value:
                actual_cities.add(i)
        course_data['Offline'] = 'Yes' if 'face-to-face' in value.lower() else course_data['Offline']
        course_data['Face_to_Face'] = 'Yes' if 'face-to-face' in value.lower() else course_data['Face_to_Face']
        course_data['Offline'] = 'No' if 'face-to-face' not in value.lower() else course_data['Offline']
        course_data['Face_to_Face'] = 'No' if 'face-to-face' not in value.lower() else course_data['Face_to_Face']

        # DURATION
        if 'Duration' in value and 'Intakes' in value:
            len1 = len(value)
            ind1 = value.find('Duration')
            ind2 = value.find('Intakes')
            str1 = value[ind1:ind2]
            print(str1)
            duration = convert_duration(str1.replace('trimester', 'semester').replace('yrs', 'years'))
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

        if len(course_data['Duration_Time']) < 3:
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

    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('cant extract combined data')

    # OUTCOMES
    try:
        THE_XPATH = "//*[text()='Career Opportunities']/ancestor::*[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Career_Outcomes'] = value
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('cant extract outcomes')

    # REMARKS
    course_data['Remarks'] = str()
    try:
        THE_XPATH = "//div[@id='admission']"
        ADMISSION_XPATH = "//a[contains(text(), 'Admission Criteria')]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{ADMISSION_XPATH}'))
        )
        browser.find_element_by_xpath(f'{ADMISSION_XPATH}').click()
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        soup = bs4.BeautifulSoup(browser.page_source, 'lxml')
        value = tag_text(soup.find('div', {'id': 'admission'}))
        course_data['Remarks'] = value
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('cant extract remarks')
    if len(course_data['Remarks']) < 10:
        try:
            THE_XPATH = "//div[@id='admission']"
            ADMISSION_XPATH = "//a[contains(text(), 'Entry Requirement')]"
            WebDriverWait(browser, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{ADMISSION_XPATH}'))
            )
            browser.find_element_by_xpath(f'{ADMISSION_XPATH}').click()
            WebDriverWait(browser, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{THE_XPATH}'))
            )
            soup = bs4.BeautifulSoup(browser.page_source, 'lxml')
            value = tag_text(soup.find('div', {'id': 'admission'}))
            course_data['Remarks'] = value
        except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
            print('cant extract remarks')

    # SUBJECTS
    try:
        TAB_XPATH = "//a[@id='subjects-tab']"
        THE_XPATH = "//td[@class='course-unit-table__unit-code']/a[@href]"
        WebDriverWait(browser, 1).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{TAB_XPATH}'))
        )
        WebDriverWait(browser, 1).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        sub_tab = browser.find_element_by_xpath(f'{TAB_XPATH}')
        sub_tab.click()
        values = browser.find_elements_by_xpath(f'{THE_XPATH}')

        a_tags = values
        subjects_links = []
        domain_url = "https://www.ac.edu.au/"
        delay = 2
        for a in a_tags:
            link = a.get_attribute('href')
            if link:
                link_ = urljoin(domain_url, link)
                if link_ not in subjects_links:
                    subjects_links.append(link_)
            if len(subjects_links) is 20:
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
                value = browser.find_element_by_xpath(f'{THE_XPATH}').text
                course_data[f'Subject_or_Unit_{i}'] = value
            except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
                print(f'cant extract subject name {i}: {e}')
            try:
                THE_XPATH = "//h1[1]/following::*[1]"
                WebDriverWait(browser, delay).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, f'{THE_XPATH}'))
                )
                value = browser.find_element_by_xpath(f'{THE_XPATH}').text
                course_data[f'Subject_Description_{i}'] = value
            except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
                print(f'cant extract subject description {i}: {e}')
            try:
                THE_XPATH = "//*[contains(text(), 'Module Description')]/following::*[1]"
                WebDriverWait(browser, delay).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, f'{THE_XPATH}'))
                )
                value = browser.find_element_by_xpath(f'{THE_XPATH}').text
                course_data[f'Subject_Objective_{i}'] = value
            except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
                print(f'cant extract subject objective {i}: {e}')
            print(f"SUBJECT {i}: {course_data[f'Subject_or_Unit_{i}']}\n"
                  f"SUBJECT OBJECTIVES {i}: {course_data[f'Subject_Objective_{i}']}\n"
                  f"SUBJECT DESCRIPTION {i}: {course_data[f'Subject_Description_{i}']}\n")
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
