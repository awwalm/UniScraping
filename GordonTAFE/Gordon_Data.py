import copy
import csv
import json
import re
import time
from pathlib import Path

# noinspection PyProtectedMember
from bs4 import Comment
from selenium import webdriver

from selenium.common.exceptions import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from CustomMethods import DurationConverter, TemplateData
import bs4 as bs4
import requests
import os


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
    soup_ = bs4.BeautifulSoup(body_, 'html.parser')
    texts = soup_.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    return u" ".join(t.strip() for t in visible_texts)


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
delay = 2

# read the url from each file into a list
course_links_file_path = Path(os.getcwd().replace('\\', '/'))
course_links_file_path = course_links_file_path.__str__() + '/gordon_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'Gordon_All_Data.csv'

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
                        'Course_Delivery_Mode': 'Traineeship',
                        # is this an Apprenticeship, Traineeship, or just a Normal course?
                        'FREE_TAFE': 'No',  # is this a free of charge TAFE course, supposedly sponsored by agencies?
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
possible_cities = {'east geelong campus': 'Melbourne (East Geelong Campus)',
                   'geelong city campus': 'Melbourne (Geelong City Campus)',
                   'werribee princes campus': 'Melbourne (Werribee Princes Campus)',
                   'hoppers crossing trades campus': 'Melbourne (Hoppers Crossing Trades Campus)',
                   'werribee': 'Melbourne (Werribee Campus)',
                   'off campus': '',
                   'werribee watton campus': 'Melbourne (Werribee Watton Campus)',
                   'ballarat': 'Ballarat',
                   '': 'Melbourne',
                   'melbourne': 'Melbourne',
                   'colac trade training centre': 'Colac'}

other_cities = {}

campuses = set()

sample = ['']

# MAIN ROUTINE
for each_url in course_links_file:

    # noinspection SpellCheckingInspection
    course_data = {'Level_Code': '', 'University': 'Gordon Geelong Institute of TAFE', 'City': 'Melbourne',
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
                   'Course_Delivery_Mode': 'Traineeship',  # is this an Apprenticeship, Traineeship, or just a Normal course?
                   'FREE_TAFE': 'No',  # is this a free of charge TAFE course, supposedly sponsored by agencies?
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

    browser.get(each_url)
    time.sleep(1)
    url__ = each_url
    pure_url = each_url.strip()
    print('CURRENT LINK: ', pure_url)
    each_url = browser.page_source

    soup = bs4.BeautifulSoup(each_url, 'html.parser')

    all_text = soup.text.replace('\n', '').strip()

    # COURSE URL
    course_data['Website'] = pure_url

    # COURSE NAME
    title = soup.find('div', {'id': 'sectionContent'}).find('h1')
    if title:
        course_data['Course'] = tag_text(title)

    # DESCRIPTION
    try:
        desc1 = soup.find('h2', text='Course Description').find_next('p')
        desc2 = soup.find('h2', text='Course Description').find_next('ul')
        if desc1 and desc2:
            desc = tag_text(desc1) + ' ' + tag_text(desc2)
            course_data['Description'] = desc
    except AttributeError:
        pass

    # REMARKS
    try:
        rem1 = soup.find('h3', text='Changes to delivery due to COVID-19').find_next('p')
        rem2 = soup.find('h3', text='Changes to delivery due to COVID-19').find_next('ul')
        if rem1 and rem2:
            rem = tag_text(rem1) + ' ' + tag_text(rem2)
            course_data['Remarks'] = rem
    except AttributeError:
        pass

    # CITY
    try:
        the_tag = soup.find('div', {'id': 'IntakesTable'}).find('div', {'class': 'row'}).find_all('span')[1]
        if the_tag:
            city = tag_text(the_tag)
            actual_cities.add(city)
            print('city so far: ', city)
    except AttributeError:
        actual_cities.add('melbourne')
        print('city not found')
    try:
        divs1 = soup.find('div', {'id': 'IntakesTable'}).find_all('div', {'class': 'row'})
        if divs1:
            cities = []
            for div in divs1:
                actual_cities.add(tag_text(div.find_all('span')[1]))
    except AttributeError:
        pass

    # DURATION
    try:
        duration_ = soup.find('div', {'id': 'IntakesTable'}).find('div', {'class': 'row'})
        if duration_:
            duration = tag_text(duration_)
            print('duration so far: ', duration)
            if 'part-time' in duration.lower() or 'part time' in duration.lower():
                course_data['Part_Time'] = 'Yes'
            if 'full time' in duration.lower() or 'full-time' in duration.lower():
                course_data['Full_Time'] = 'Yes'
            head, sep, tail = duration.replace('yrs', 'years').partition(':')
            duration = DurationConverter.convert_duration(tail)
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
    except (AttributeError, TypeError):
        print('no info on duration/full/part time mode')
    print('DURATION + DURATION TIME: ', course_data['Duration'], course_data['Duration_Time'])

    # FEES
    try:
        fee_data = soup.find('span', text=re.compile('full fee tuition', re.IGNORECASE)) \
            .find_next('span').find_next('span').find_next('span').find_next('span')
        if fee_data:
            fee = tag_text(fee_data)
            course_data['Int_Fees'] = course_data['Local_Fees'] = fee.replace('AUD', '').replace(',', '').replace('$',
                                                                                                                  '')
            print('fees so far: ', fee)
    except AttributeError:
        try:
            fee_data = soup.find('span', text=re.compile('^ Cost \(inc\. GST\):', re.IGNORECASE)).find_next('span')
            if fee_data:
                fee = tag_text(fee_data)
                course_data['Int_Fees'] = course_data['Local_Fees'] = fee.replace('AUD', '').replace(',', '').replace(
                    '$', '')
                print('fees so far: ', fee)
        except AttributeError:
            try:
                fee_data = soup.find('span', text=re.compile('Full Fee Cost', re.IGNORECASE)).find_next('span')
                if fee_data:
                    fee = tag_text(fee_data)
                    course_data['Int_Fees'] = course_data['Local_Fees'] = fee.replace('AUD', '').replace(',',
                                                                                                         '').replace(
                        '$', '')
                    print('fees so far: ', fee)
            except AttributeError:
                print('cant find fees')

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

    # CHECK IF ONLINE
    try:
        mode_tag1 = soup.find('span', text=re.compile('Room:', re.IGNORECASE)).find_parent('div')
        mode_tag2 = soup.find('span', text=re.compile('Campus:', re.IGNORECASE)).find_parent('div')
        if mode_tag1 and mode_tag2:
            mode1 = tag_text(mode_tag1)  # classroom
            mode2 = tag_text(mode_tag2)  # campus
            if 'Online - Remote Delivery' in mode2:
                course_data['Online'] = 'Yes'
            if 'Online' in 'mode1':
                course_data['Online'] = 'Yes'
                course_data['Face_to_Face'] = 'No'
                course_data['Offline'] = 'No'
    except AttributeError:
        if len(course_data['City']) < 5:
            course_data['Offline'] = 'Yes'
        print('no info on online delivery')
    try:
        if_blended = soup.find('span', text=re.compile('^Blended', re.IGNORECASE))
        if if_blended:
            course_data['Blended'] = 'Yes'
            course_data['Online'] = 'Yes'
            course_data['Offline'] = 'Yes'
    except AttributeError:
        print('info on whether blended not given')
    try:
        if_blended = soup.find('strong', text=re.compile('Blended attendance', re.IGNORECASE))
        if if_blended:
            course_data['Blended'] = 'Yes'
            course_data['Online'] = 'Yes'
            course_data['Offline'] = 'Yes'
    except AttributeError:
        pass

    # FIND FREE COURSE
    if 'this is a free tafe course' in course_data['Description'].lower():
        course_data['FREE_TAFE'] = 'Yes'

    # CHECK IF COURSE IS A NORMALLY DELIVERED COURSE
    try:
        short_course_div = soup.find('div', {'class': 'shortCourseSessions block'})
        if short_course_div:
            course_data['Course_Delivery_Mode'] = 'Normal'
    except AttributeError:
        pass

    try:
        normal_duration_div = soup.find('div', {'id': 'IntakesTable'})\
            .find('div', {'class': 'row'})\
            .find('span', {'class': 'HideS'})
        if normal_duration_div:
            val = tag_text(normal_duration_div)
            if len(val) > 3:
                course_data['Course_Delivery_Mode'] = 'Normal'
    except (TypeError, AttributeError):
        pass

    # CHECK IF COURSE IS APPRENTICESHIP
    try:
        apprentice_duration_div = soup.find('div', {'id': 'IntakesTable'}) \
            .find('div', {'class': 'row'}) \
            .find('span', {'class': 'HideA'})
        if apprentice_duration_div:
            val = tag_text(apprentice_duration_div)
            if len(val) > 3:
                course_data['Course_Delivery_Mode'] = 'Apprenticeship'
    except (TypeError, AttributeError):
        pass

    # CHECK IF COURSE IS TRAINEESHIP
    try:
        train_duration_div = soup.find('div', {'id': 'IntakesTable'}) \
            .find('div', {'class': 'row'}) \
            .find('span', {'class': 'HideT'})
        if train_duration_div:
            val = tag_text(train_duration_div)
            if len(val) > 3:
                course_data['Course_Delivery_Mode'] = 'Traineeship'
    except (TypeError, AttributeError):
        pass

    try:
        THE_XPATH = "//div[@id='UnitsTable']/div[@class='row']/span[1]"
        DROPDOWN = "//div[contains(text(), 'Units & Assessment')]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{DROPDOWN}'))
        )
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        dropdown = browser.find_element_by_xpath(f'{DROPDOWN}')
        dropdown.click()
        time.sleep(0.2)
        values = browser.find_elements_by_xpath(f'{THE_XPATH}')
        subjects = []
        for v in values:
            subjects.append(v.text)
        i = 1
        for s in subjects:
            course_data[f'Subject_or_Unit_{i}'] = s
            print(f'subject {i}: {s}')
            i += 1
            if i is 40:
                break
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        print(f'cant extract subject objective: {e}')

    # duplicating entries with multiple cities for each city
    for i in actual_cities:
        try:
            course_data['City'] = possible_cities[i.lower()]
        except KeyError:
            course_data['City'] = 'Melbourne'
        print('repeated cities: ', course_data['City'])
        course_data_all.append(copy.deepcopy(course_data))
    del actual_cities

    print('COURSE: ', course_data['Course'])
    print('DESCRIPTION: ', course_data['Description'])
    print('LEVEL CODE: ', course_data['Level_Code'])
    print('CITY: ', course_data['City'])
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
