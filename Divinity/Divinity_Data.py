import copy
import csv
import json
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
browser.maximize_window()
delay = 1

# collect page source for fees
browser2.get("https://divinity.edu.au/study/fees/tuition-fees/")
fee_url = browser2.page_source
soup_fees = bs4.BeautifulSoup(fee_url, 'lxml')

# read the url from each file into a list
course_links_file_path = Path(os.getcwd().replace('\\', '/'))
course_links_file_path = course_links_file_path.__str__() + '/divinity_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'Divinity_All_Data.csv'

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
                        'Blended': 'No', 'Remarks': ''}

# noinspection SpellCheckingInspection
possible_cities = {'Melbourne': 'Melbourne',
                   'Australian Lutheran College': 'Adelaide',
                   'Catholic Theological College': 'Melbourne',
                   'Eva Burrows College': 'Melbourne',
                   'Morling College': 'Sydney',
                   'Pilgrim Theological College': 'Melbourne',
                   'St Athanasius College': 'Donvale',
                   'Stirling Theological College': 'Mulgrave',
                   'Trinity College Theological School': 'Melbourne',
                   'Whitley College': 'Melbourne',
                   'Yarra Theological Union': 'Melbourne'}

other_cities = {}

sample = ["https://divinity.edu.au/courses/graduate-certificate-teaching-meditation/"]

# MAIN ROUTINE
for each_url in course_links_file:

    course_data = {'Level_Code': '', 'University': 'University of Divinity', 'City': '', 'Course': '',
                   'Faculty': '',
                   'Int_Fees': '', 'Local_Fees': '', 'Currency': 'AUD', 'Currency_Time': 'Course', 'Duration': '',
                   'Duration_Time': '', 'Full_Time': 'Yes', 'Part_Time': 'No',
                   'Prerequisite_1': '', 'Prerequisite_1_grade_1': '',  # ATAR
                   'Prerequisite_2': 'VCE', 'Prerequisite_2_grade_2': '',  # IELTS or anything else
                   'Prerequisite_3': 'AQF', 'Prerequisite_3_grade_3': '',  # GPA or IB
                   'Website': '', 'Course_Lang': 'English', 'Availability': 'A', 'Description': '',
                   'Career_Outcomes': '',
                   'Country': 'Australia', 'Online': 'No', 'Offline': 'Yes', 'Distance': 'No', 'Face_to_Face': 'Yes',
                   'Blended': 'No', 'Remarks': ''}

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
    title = soup.find('h1', {'class': 'entry-title'})
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
    try:
        THE_XPATH = "(//*[contains(text(), 'Detailed information')]/following-sibling::p)[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Description'] = value + bar
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('cant extract description')

    # FEES
    name_course = course_data['Course']
    try:
        THE_XPATH = f"//td[contains(text(), '{name_course}')]/following-sibling::*[last()]"
        WebDriverWait(browser2, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser2.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Int_Fees'] = value.replace(',', '')
        course_data['Local_Fees'] = value.replace(',', '')
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('cant extract fees')

    # OUTCOMES
    try:
        THE_XPATH = "(//*[contains(text(), 'learning outcomes')]/following-sibling::ol)[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Career_Outcomes'] = value + bar
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        try:
            out_tag = soup.find('h5', text=re.compile('course learning outcomes', re.IGNORECASE)).find_next()
            if out_tag:
                course_data['Career_Outcomes'] = tag_text(out_tag) + bar\
                                                 + tag_text(out_tag.find_next()) + bar \
                                                 + tag_text(out_tag.find_next().find_next()) + bar \
                                                 + tag_text(out_tag.find_next().find_next().find_next()) + bar\
                                                 + tag_text(out_tag.find_next().find_next().find_next().find_next()) + bar
        except AttributeError:
            print('cant extract outcomes')

    # REMARKS 1
    try:
        THE_XPATH = "(//*[contains(text(), 'Follow on s')]/following-sibling::*[1])[1]"
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
        THE_XPATH = "(//*[contains(text(), 'Overseas students')]/following::*[1])[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Availability'] = 'D' if 'No' in value else 'A'
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('cant extract availability')

    # STUDY MODE
    try:
        THE_XPATH = "(//*[contains(text(), 'Study mode')]/following::*[1])[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        if 'Online' in value:
            course_data['Online'] = 'Yes'
        if 'Blended' in value:
            course_data['Blended'] = 'Yes'
        if 'Face-to-face' in value:
            course_data['Face_to_Face'] = 'Yes'
            course_data['Offline'] = 'Yes'
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('cant extract study mode')

    # DURATION
    try:
        THE_XPATH = "(//*[contains(text(), 'Duration')]/following::*[1])[1]"
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

    # STUDY LOAD (PART TIME/FULL TIME)
    try:
        THE_XPATH = "(//*[contains(text(), 'Study load')]/following::*[1])[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        if 'part-time' in value.lower() or 'part time' in value.lower():
            course_data['Part_Time'] = 'Yes'
        if 'full-time' in value.lower() or 'full time' in value.lower():
            course_data['Full_Time'] = 'Yes'
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('cant extract part-time/full time')

    # CITIES
    for i in possible_cities:
        try:
            THE_XPATH = f"//article/ul/li[contains(text(), '{i}')]"
            WebDriverWait(browser, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{THE_XPATH}'))
            )
            value = browser.find_element_by_xpath(f'{THE_XPATH}').text
            if i not in actual_cities:
                actual_cities.add(i)
        except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
            print(f'not available in {i}')
    if len(actual_cities) is 0 and 'Melbourne' not in actual_cities:
        actual_cities.add('Melbourne')

    # FEES
    """
    * https://divinity.edu.au/study/fees/tuition-fees/
    * Tuition fees are given in Australian Dollars, unless otherwise indicated.
    * Tuition fees are consistent for Domestic and Overseas students.
    * Overseas students are charged a separate application fee of AUD$300.
    """

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
    print('IB: ', course_data['Prerequisite_3_grade_3'])
    print('STAT: ', course_data['Prerequisite_2_grade_2'])
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
