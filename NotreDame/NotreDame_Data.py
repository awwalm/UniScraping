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


def webdriver_wait(xpath__):
    try:
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f"{xpath__}"))
        )
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        print(e.traceback)


def remove_banned_words(to_print, database_regex):
    pattern = re.compile(r"\b(" + "|".join(database_regex) + ")\\W", re.I)
    return pattern.sub("", to_print)


def save_data_json(title__, data__):
    with open(title__, 'w', encoding='utf-8') as f:
        json.dump(data__, f, ensure_ascii=False, indent=2)


def tag_text(tag):
    return tag.get_text().__str__().strip()


def has_numbers(input_string):
    return any(char.isdigit() for char in input_string)


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
delay = 1

option2 = option
option2.add_argument("headless")
browser2 = webdriver.Chrome(executable_path=exec_path, chrome_options=option2)

# read the url from each file into a list
course_links_file_path = Path(os.getcwd().replace('\\', '/'))
course_links_file_path = course_links_file_path.__str__() + '/notre_dame_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'NotreDame_All_Data.csv'

with open('LocalData/2020-Indicative-Domestic-Fees.html', encoding='utf8') as dom_file:  # Domestic Fees local HTML
    soup_dom_fees = bs4.BeautifulSoup(dom_file, 'html.parser')
with open('LocalData/2020-Indicative-International-Fees.html',
          encoding='utf8') as int_file:  # International Fees local HTML
    soup_int_fees = bs4.BeautifulSoup(int_file, 'html.parser')

browser2.get('file:///LocalData/2020-Indicative-Domestic-Fees.html')
time.sleep(1)

level_key = TemplateData.level_key  # dictionary of course levels

faculty_key = TemplateData.faculty_key  # dictionary of course levels

currency_pattern = "(?:[\£\$\€\(RM)\]{1}[,\d]+.?\d*)"  # regex pattern for finding currency or cash amount strings

course_data_all = []

city_set = set()

bar = ' | '

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

possible_cities = {'Sydney': 'Sydney',
                   'Fremantle': 'Fremantle',
                   'Broome': 'Kimberly (Western Australia)',
                   'Online': 'Sydney'}

other_cities = {}

sample = [
    "https://www.notredame.edu.au/programs/fremantle/school-of-education/undergraduate/bachelor-of-education-ec-bachelor-of-science"]

# MAIN ROUTINE
for each_url in course_links_file:

    course_data = {'Level_Code': '', 'University': 'Notre Dame University', 'City': '', 'Course': '',
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
    time.sleep(0.5)
    url__ = each_url
    pure_url = each_url.strip()
    print('CURRENT LINK: ', pure_url)
    each_url = browser.page_source
    soup = bs4.BeautifulSoup(each_url, 'html.parser')

    all_text = soup.text.replace('\n', '').strip()

    # COURSE URL
    course_data['Website'] = pure_url

    # COURSE NAME
    title_ = None
    title = soup.find('h1', {'class': 'layout-page-title'})
    if title:
        course_data['Course'] = tag_text(title)
        title_ = tag_text(title)

    # DECIDE THE LEVEL CODE
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

    # INT FEES
    split_c = course_data['Course'] \
        .replace('(', '\(') \
        .replace(')', '\)') \
        .replace('&', '\&') \
        .replace('-', '\-') \
        .split()
    break_now = False
    if 'UG' in course_data['Level_Code'] or 'BA' in course_data['Level_Code'] or 'HONS' in course_data['Level_Code']:
        for i in split_c:
            pattern = f'^.*{i}.*$'
            the_tag = soup_int_fees.find('p', class_='p20 ft17', text=re.compile(pattern, re.IGNORECASE))
            if the_tag:
                try:
                    the_fee = the_tag.find_parent('td').find_parent('tr').find_all('td')[-2]
                    if the_fee and '$' in tag_text(the_fee):
                        print(f'UG int fee found: {tag_text(the_fee)}')
                        course_data['Int_Fees'] = tag_text(the_fee).replace('$', '').replace(',', '')
                        if '-' in tag_text(the_fee):
                            head, sep, tail = tag_text(the_fee).partition('-')
                            course_data['Int_Fees'] = head.replace('$', '').replace(',', '')
                        break_now = True
                except (AttributeError, IndexError):
                    pass
            if break_now:
                break
    else:  # definitely postgraduate or some other shit
        for i in split_c:
            pattern = f'^.*{i}.*$'
            the_tag = soup_int_fees.find('p', class_='p20 ft17', text=re.compile(pattern, re.IGNORECASE))
            if the_tag:
                try:
                    the_fee = the_tag.find_parent('td').find_parent('tr').find_all('td')[-1]
                    if the_fee and '$' in tag_text(the_fee):
                        print(f'PG int fee found: {tag_text(the_fee)}')
                        course_data['Int_Fees'] = tag_text(the_fee).replace('$', '').replace(',', '')
                        if '-' in tag_text(the_fee):
                            head, sep, tail = tag_text(the_fee).partition('-')
                            course_data['Int_Fees'] = head.replace('$', '').replace(',', '')
                        break_now = True
                except (AttributeError, IndexError):
                    pass
            if break_now:
                break

    # LOCAL FEES
    split_c = course_data['Course'] \
        .replace('(', '\(') \
        .replace(')', '\)') \
        .replace('&', '\&') \
        .replace('-', '\-') \
        .split()
    break_now = False
    if 'UG' in course_data['Level_Code'] or 'BA' in course_data['Level_Code'] or 'HONS' in course_data['Level_Code']:
        for i in split_c:
            pattern = f'^.*{i}.*$'
            the_tag = soup_dom_fees.find('p', class_='p20 ft17', text=re.compile(pattern, re.IGNORECASE))
            if the_tag:
                try:
                    the_fee = the_tag.find_parent('td').find_parent('tr').find_all('td')[-2]
                    if the_fee and '$' in tag_text(the_fee):
                        print(f'UG dom fee found: {tag_text(the_fee)}')
                        course_data['Local_Fees'] = tag_text(the_fee).replace('$', '').replace(',', '')
                        if '-' in tag_text(the_fee):
                            head, sep, tail = tag_text(the_fee).partition('-')
                            course_data['Local_Fees'] = head.replace('$', '').replace(',', '')
                        break_now = True
                except (AttributeError, IndexError):
                    pass
            if break_now:
                break
    else:  # definitely postgraduate or some other shit
        for i in split_c:
            pattern = f'^.*{i}.*$'
            the_tag = soup_dom_fees.find('p', class_='p20 ft17', text=re.compile(pattern, re.IGNORECASE))
            if the_tag:
                try:
                    the_fee = the_tag.find_parent('td').find_parent('tr').find_all('td')[-1]
                    if the_fee and '$' in tag_text(the_fee):
                        print(f'PG dom fee found: {tag_text(the_fee)}')
                        course_data['Local_Fees'] = tag_text(the_fee).replace('$', '').replace(',', '')
                        if '-' in tag_text(the_fee):
                            head, sep, tail = tag_text(the_fee).partition('-')
                            course_data['Local_Fees'] = head.replace('$', '').replace(',', '')
                        break_now = True
                except (AttributeError, IndexError):
                    pass
            if break_now:
                break

    # CITY AND FACULTY
    try:
        CITY_FAC_XPATH = "(//div[contains(@id, 'content_container')]/p)[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{CITY_FAC_XPATH}'))
        )
        city_fac = browser.find_element_by_xpath(f'{CITY_FAC_XPATH}').text
        for i in possible_cities:
            if i in city_fac:
                actual_cities.add(i)
        try:
            head, sep, tail = city_fac.partition(',')
            if len(course_data['Faculty']) < 5:
                course_data['Faculty'] = head.replace('School of', '').replace('&', 'and')
        except (AttributeError, TypeError, ValueError):
            pass
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        pass
    try:
        CITY_XPATH = "//strong[contains(text(), 'Campus')]/ancestor::span/following::span[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{CITY_XPATH}'))
        )
        city_fac = browser.find_element_by_xpath(f'{CITY_XPATH}').text
        if 'Online' in city_fac:
            course_data['Online'] = 'Yes'
        if 'On Campus' not in city_fac:
            course_data['Offline'] = 'No'
            course_data['Face_to_Face'] = 'No'
        for i in possible_cities:
            if i in city_fac:
                actual_cities.add(i)
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        course_data['Offline'] = 'No'
        course_data['Face_to_Face'] = 'No'
        actual_cities.add('Sydney')

    # STUDY MODE
    try:
        THE_XPATH = "//strong[contains(text(), 'Study')]/ancestor::span/following::span[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        if 'on campus' in value.lower():
            course_data['Offline'] = 'Yes'
            course_data['Face_to_Face'] = 'Yes'
        if 'online' in value.lower():
            course_data['Online'] = 'Yes'
        if 'research' in value.lower() or 'full-time' in value.lower() or 'part-time' in value.lower():
            course_data['Offline'] = 'Yes'
            course_data['Face_to_Face'] = 'Yes'
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        pass

    # DURATION
    try:
        THE_XPATH = "//strong[contains(text(), 'Duration')]/ancestor::span/following::span[1]"
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
        pass

    # ATAR
    try:
        THE_XPATH = "//h4[contains(text(), 'Entry requirements')]"
        ATAR_XPATH = "(//*[contains(text(), 'ATAR')])[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        req = browser.find_element_by_xpath(f'{THE_XPATH}')
        req.click()
        time.sleep(0.2)
        value = browser.find_element_by_xpath(f'{ATAR_XPATH}').text
        print(f'atar so far: {value}')
        atar = re.findall(r'[-+]?\d*\.\d+|\d+', value)
        course_data['Prerequisite_1'] = 'ATAR'
        if float(atar[0]) in range(30, 100):
            course_data['Prerequisite_1_grade_1'] = atar[0]
    except (
            AttributeError, IndexError, TypeError, TimeoutException, NoSuchElementException,
            ElementNotInteractableException):
        print('no atar')

    # STAT
    try:
        THE_XPATH = "//h4[contains(text(), 'Entry requirements')]"
        XPATH_MAIN = "(//*[contains(text(), 'STAT')])[1]"
        req = browser.find_element_by_xpath(f'{THE_XPATH}')
        # req.click()
        time.sleep(0.2)
        value = browser.find_element_by_xpath(f'{XPATH_MAIN}').text
        print(f'stat so far: {value}')
        data = re.findall(r'[-+]?\d*\.\d+|\d+', value)
        course_data['Prerequisite_2'] = 'STAT'
        course_data['Prerequisite_2_grade_2'] = data[0]
    except (AttributeError, IndexError, TypeError, TimeoutException, NoSuchElementException,
            ElementNotInteractableException):
        print('no stat')

    # INTERNATIONAL BACCALAUREATE
    try:
        THE_XPATH = "//h4[contains(text(), 'Entry requirements')]"
        XPATH_MAIN = "(//*[contains(text(), 'International Baccalaureate')])[1]"
        req = browser.find_element_by_xpath(f'{THE_XPATH}')
        # req.click()
        time.sleep(0.2)
        value = browser.find_element_by_xpath(f'{XPATH_MAIN}').text
        print(f'ib so far: {value}')
        data = re.findall(r'[-+]?\d*\.\d+|\d+', value)
        course_data['Prerequisite_3'] = 'IB'
        course_data['Prerequisite_3_grade_3'] = data[0]
    except (AttributeError, IndexError, TypeError, TimeoutException, NoSuchElementException,
            ElementNotInteractableException):
        print('no ib')

    # OUTCOMES 1
    try:
        THE_XPATH = "//div[starts-with(@id, 'Career_opportunities')]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        value = browser.find_element_by_xpath(f'{THE_XPATH}').text
        course_data['Career_Outcomes'] = value + bar
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        course_data['Career_Outcomes'] = course_data['Career_Outcomes'].replace(bar, '')

    # OUTCOMES2
    desc2 = str()
    desc1 = course_data['Description']
    try:
        OUT2_XPATH = "(//div[contains(@id, 'content_container')])[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{OUT2_XPATH}'))
        )
        out2 = browser.find_element_by_xpath(f'{OUT2_XPATH}').text
        desc2 = out2
        course_data['Career_Outcomes'] += out2 + bar
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        pass

    # DESCRIPTION
    try:
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "(//div[contains(@id, 'content_container')]/following::div[1]/*/*/*/following::div)[1]"))
        )
        desc = browser.find_element_by_xpath(
            "(//div[contains(@id, 'content_container')]/following::div[1]/*/*/*/following::div)[1]"
        ).text
        course_data['Description'] = desc
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        pass
    if len(desc1) < 10:
        course_data['Description'] = desc2

    # REMARKS
    try:
        rem1 = browser.find_element_by_xpath("(//span[contains(text(), 'Code')])[1]").text
        course_data['Remarks'] = rem1 + ' | '
    except (TimeoutException, NoSuchElementException, ElementNotInteractableException):
        pass
    try:
        rem2tag = soup.find('em', text=re.compile('^.*Please note.*$', re.IGNORECASE))
        rem2 = tag_text(rem2tag)
        course_data['Remarks'] += rem2 + ' | '
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        pass
    try:
        rem3tag = soup.find(True, id=re.compile('^.*Entry_requirements.*$')).find('div')
        rem3 = tag_text(rem3tag) if rem3tag else ''
        course_data['Remarks'] += rem3 + bar
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
        pass

    course_data['Remarks'].replace('\n', bar)

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