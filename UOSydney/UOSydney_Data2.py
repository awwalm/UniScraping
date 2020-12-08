import copy
import csv
import json
import os
import re
import time
from pathlib import Path

# noinspection PyProtectedMember
from urllib.parse import urljoin

from bs4 import Comment
import bs4 as bs4
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, \
    JavascriptException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

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
course_links_file_path = course_links_file_path.__str__() + '/uo_sydney_links_file_2'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'UOSydney_All_Data2.csv'

delay = 3
delay_ = 10
browser = webdriver.Chrome(executable_path=exec_path)
browser.maximize_window()
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
                        'Prerequisite_3': '', 'Prerequisite_3_grade_3': '',  # TOEFL
                        'Prerequisite_4': '', 'Prerequisite_4_grade_4': '',  # Pearson's Test of English
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
                   'Camperdown': 'Camperdown',
                   'Darlington': 'Darlington',
                   'Cumberland Campus': 'Lidcombe',
                   'Camden Campus': 'Sydney',
                   'Mallet Street Campus': 'Camperdown',
                   'Sydney College of the Arts': 'Sydney',
                   'Sydney Medical School Campuses and Teaching Hospitals': 'Sydney',
                   'Surry Hills Campus': 'Surry Hills',
                   'Sydney Conservatorium of Music': 'Sydney',
                   'Westmead': 'Sydney',
                   'One Tree Island Research Station': 'Queensland (Capricon Group of the Great Barrier Reef)'}

other_cities = {}

sample = ["https://www.sydney.edu.au/courses/courses/uc/bachelor-of-commerce-and-bachelor-of-advanced-studies-dalyell-scholars.html"]

# MAIN ROUTINE
for each_url in course_links_file:

    course_data = {'Level_Code': '', 'University': 'University of Sydney', 'City': 'Sydney', 'Course': '',
                   'Faculty': '',
                   'Int_Fees': '', 'Local_Fees': '', 'Currency': 'AUD', 'Currency_Time': 'Years', 'Duration': '',
                   'Duration_Time': '', 'Full_Time': 'Yes', 'Part_Time': 'Yes',
                   'Prerequisite_1': '', 'Prerequisite_1_grade_1': '',  # ATAR
                   'Prerequisite_2': '', 'Prerequisite_2_grade_2': '',  # IELTS
                   'Prerequisite_3': '', 'Prerequisite_3_grade_3': '',  # TOEFL
                   'Prerequisite_4': '', 'Prerequisite_4_grade_4': '',  # Pearson's Test of English
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

    browser.get(each_url)
    time.sleep(1.5)
    url__ = each_url
    pure_url = each_url.strip()
    print('CURRENT LINK: ', pure_url)
    each_url = browser.page_source
    soup = bs4.BeautifulSoup(each_url, 'lxml')

    course_data['Description'] = ''

    all_text = soup.text.replace('\n', '').strip()

    # remove mainNav class object - it interferes with Selenium auto-clicking
    main_nav = soup.find('div', {'class': 'mainNav'})
    if main_nav:
        js = "var aa=document.getElementsByClassName('mainNav')[0];aa.parentNode.removeChild(aa)"
        browser.execute_script(js)
        print('main nav deleted')
        each_url = browser.page_source
        soup = bs4.BeautifulSoup(each_url, 'lxml')

    # COURSE URL
    course_data['Website'] = pure_url

    # COURSE NAME
    try:
        WebDriverWait(browser, delay_).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//h1[@class='pageTitle pageTitle__course']"))
        )

    except (TimeoutException, NoSuchElementException, ElementNotInteractableException):
        pass
    try:
        title = soup.find('h1', class_='pageTitle pageTitle__course')
        if title:
            course_data['Course'] = tag_text(title)
        if not title:
            course_data['Course'] = tag_text(soup.find('h1'))
        if len(course_data['Course']) < 5:
            last_slash_index = pure_url.rfind('/')
            course_data['Course'] = pure_url[last_slash_index + 1:].replace('-', ' ').replace('.html', '').title()
    except (AttributeError, TypeError):
        pass

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

    # REMARKS
    try:
        rem_tag = soup.find('div',
                            class_='b-box--slightly-transparent b-box--compact b-box--mid-grey b-component--tighter b-text--align-centre') \
            .find_parent('div')
        if rem_tag:
            remarks = tag_text(rem_tag)
            course_data['Remarks'] = remarks
    except AttributeError:
        try:
            rem2tag = soup.find('div',
                                class_='col-xs-12 b-box--grey b-text--colour-light b-feature-figure b-feature-figure-group__item b-position__container')
            if rem2tag:
                remarks = tag_text(rem2tag)
                course_data['Remarks'] = remarks
        except AttributeError:
            try:
                rem3tag = soup.find('h3', class_='b-title b-title--module-h2 b-title--first').find_parent('div',
                                                                                                          class_='b-text--size-base')
                if rem3tag:
                    remarks = tag_text(rem3tag).replace('\n', ' | ')
                    course_data['Remarks'] = remarks
            except AttributeError:
                pass

    # CAREER PATHS
    try:
        out1tag = soup.find('h5', text=re.compile('^.*opportunities.*$', re.IGNORECASE)).find_parent('div').find_parent(
            'div')
        if out1tag:
            course_data['Career_Outcomes'] = tag_text(out1tag)
    except AttributeError:
        try:
            out2tag = soup.find('h3', text=re.compile('^.*course opportunities.*$', re.IGNORECASE)).find_parent('div')
            if out2tag:
                course_data['Career_Outcomes'] = tag_text(out2tag)
        except AttributeError:
            try:
                out3tag = soup.find('h3', text=re.compile('^.*Career Pathways.*$', re.IGNORECASE)).find_parent('div')
                if out3tag:
                    course_data['Career_Outcomes'] = tag_text(out3tag)
            except AttributeError:
                pass
    try:
        h3_tag = soup.find('h3', text=re.compile('.*Course opportunities.*', re.IGNORECASE)).find_parent()
        if h3_tag:
            # print(tag_text(h3_tag))
            course_data['Career_Outcomes'] = tag_text(h3_tag)
    except AttributeError:
        pass
    try:
        if len(course_data['Career_Outcomes']) < 5:
            out5tag = soup.find('h5', text=re.compile('^.*Career pathways.*$', re.IGNORECASE)).find_next()
            if out5tag:
                course_data['Career_Outcomes'] = tag_text(out5tag)
    except AttributeError:
        pass
    try:
        if len(course_data['Career_Outcomes']) < 5:
            out5tag = soup.find('h4', text=re.compile('^.*Career pathways.*$', re.IGNORECASE)).find_next()
            if out5tag:
                course_data['Career_Outcomes'] = tag_text(out5tag)
    except AttributeError:
        pass
    try:
        if len(course_data['Career_Outcomes']) < 5:
            out5tag = soup.find('h3', text=re.compile('^.*Career pathways.*$', re.IGNORECASE)).find_next()
            if out5tag:
                course_data['Career_Outcomes'] = tag_text(out5tag)
    except AttributeError:
        pass
    try:
        if len(course_data['Career_Outcomes']) < 5:
            out5tag = soup.find('h5', text=re.compile('^.*Graduate Opportunities.*$', re.IGNORECASE)).find_next()
            if out5tag:
                course_data['Career_Outcomes'] = tag_text(out5tag)
    except AttributeError:
        pass
    try:
        if len(course_data['Career_Outcomes']) < 5:
            out5tag = soup.find(attrs={'text': re.compile('^.*opportunities.*$', re.IGNORECASE)}).find_next()
            if out5tag:
                course_data['Career_Outcomes'] = tag_text(out5tag)
    except AttributeError:
        pass

    # FACULTY (reinforced/directly obtained from site)
    if len(course_data['Faculty']) < 5:
        try:
            fac_div = soup.find('div', class_='b-component b-box-compact b-details-panel') \
                .find_all('div', class_='b-details-panel__row')[1]
            if fac_div:
                fac_temp = tag_text(fac_div)
                head, sep, tail = fac_temp.partition(':')
                course_data['Faculty'] = tail
        except (AttributeError, IndexError, TypeError):
            try:
                fac_div = soup.find('div', text=re.compile('^.*Faculty/University School:.*$', re.IGNORECASE))
                if fac_div:
                    fac_temp = tag_text(fac_div)
                    head, sep, tail = fac_temp.partition(':')
                    course_data['Faculty'] = tail
            except (AttributeError, IndexError, TypeError):
                pass

    # DURATION
    try:
        duration_div = soup.find('div', class_='b-component b-box-compact b-details-panel') \
            .find_all('div', class_='b-details-panel__row')[6]
        if duration_div:
            d_val = tag_text(duration_div)
            print('full time duration so far: ', d_val)

            if 'full time' in d_val.lower() or 'full-time' in d_val.lower():
                course_data['Full_Time'] = 'Yes'
            if 'not available part time' in d_val.lower() or 'not available' in d_val.lower():
                course_data['Part_Time'] = 'No'
            if 'Not available to Domestic students' in d_val:
                course_data['Availability'] = 'I'
            if 'Not available to International students' in d_val:
                course_data['Availability'] = 'D'

            if ': NA' in d_val:
                course_data['Full_Time'] = 'No'
                try:
                    duration_div = soup.find('div', class_='b-component b-box-compact b-details-panel') \
                        .find_all('div', class_='b-details-panel__row')[7]
                    if duration_div:
                        d_val = tag_text(duration_div)
                        print('part-time duration so far: ', d_val)
                        course_data['Remarks'] = d_val + ' | ' + course_data['Remarks']
                        if 'Not available part time' in d_val or 'Not available' in d_val:
                            course_data['Part_Time'] = 'No'
                        if 'part time' in d_val.lower() or 'part-time' in d_val.lower():
                            colon_index = d_val.find(':')
                            duration_ = d_val[colon_index:]
                            duration = convert_duration(
                                duration_.replace('trimester', 'semester').replace('yrs', 'years'))
                            course_data['Duration'] = duration[0]
                            course_data['Duration_Time'] = duration[1]
                            if duration[0] < 2 and 'month' in duration[1].lower():
                                course_data['Duration'] = duration[0]
                                course_data['Duration_Time'] = 'Month'
                                course_data['Remarks'] = d_val + ' | ' + course_data['Remarks']
                                course_data['Part_Time'] = 'Yes'
                            if duration[0] < 2 and 'year' in duration[1].lower():
                                course_data['Duration'] = duration[0]
                                course_data['Duration_Time'] = 'Year'
                                course_data['Remarks'] = d_val + ' | ' + course_data['Remarks']
                                course_data['Part_Time'] = 'Yes'
                            if 'week' in duration[1].lower():
                                course_data['Duration'] = duration[0]
                                course_data['Duration_Time'] = 'Weeks'
                                course_data['Remarks'] = d_val + ' | ' + course_data['Remarks']
                                course_data['Part_Time'] = 'Yes'
                        if 'not available part time' in d_val.lower() or 'not available' in d_val.lower():
                            course_data['Part_Time'] = 'No'
                except (AttributeError, IndexError, TypeError):
                    pass

            if ': NA' not in d_val:
                colon_index = d_val.find(':')
                duration_ = d_val[colon_index:]
                duration = convert_duration(duration_.replace('trimester', 'semester').replace('yrs', 'years'))
                course_data['Duration'] = duration[0]
                course_data['Duration_Time'] = duration[1]
                if duration[0] < 2 and 'month' in duration[1].lower():
                    course_data['Duration'] = duration[0]
                    course_data['Duration_Time'] = 'Month'
                    course_data['Remarks'] = d_val + ' | ' + course_data['Remarks']
                if duration[0] < 2 and 'year' in duration[1].lower():
                    course_data['Duration'] = duration[0]
                    course_data['Duration_Time'] = 'Year'
                    course_data['Remarks'] = d_val + ' | ' + course_data['Remarks']
                if 'week' in duration[1].lower():
                    course_data['Duration'] = duration[0]
                    course_data['Duration_Time'] = 'Weeks'
                    course_data['Remarks'] = d_val + ' | ' + course_data['Remarks']
    except (AttributeError, IndexError, TypeError):
        print('trouble processing/extracting duration')
    # PART TIME
    try:
        duration_div = soup.find('div', class_='b-component b-box-compact b-details-panel') \
            .find_all('div', class_='b-details-panel__row')[7]
        if duration_div:
            d_val = tag_text(duration_div)
            if ': NA' in d_val or ': NA' in d_val:
                course_data['Part_Time'] = 'No'
            print('part-time duration so far: ', d_val)
            course_data['Remarks'] = d_val + ' | ' + course_data['Remarks']
            if 'Not available part time' in d_val or 'Not available' in d_val:
                course_data['Part_Time'] = 'No'
            if 'part time' in d_val.lower() or 'part-time' in d_val.lower():
                colon_index = d_val.find(':')
                duration_ = d_val[colon_index:]
                duration = convert_duration(duration_.replace('trimester', 'semester'))
                if duration[0] < 2 and 'month' in duration[1].lower():
                    course_data['Remarks'] = d_val + ' | ' + course_data['Remarks']
                    course_data['Part_Time'] = 'Yes'
                if duration[0] < 2 and 'year' in duration[1].lower():
                    course_data['Remarks'] = d_val + ' | ' + course_data['Remarks']
                    course_data['Part_Time'] = 'Yes'
                if 'week' in duration[1].lower():
                    course_data['Remarks'] = d_val + ' | ' + course_data['Remarks']
                    course_data['Part_Time'] = 'Yes'
            if 'not available part time' in d_val.lower() or 'not available' in d_val.lower():
                course_data['Part_Time'] = 'No'
    except (AttributeError, IndexError, TypeError):
        pass

    # STUDY MODE
    try:
        mode_div = soup.find('div', class_='b-component b-box-compact b-details-panel') \
            .find_all('div', class_='b-details-panel__row')[4]
        if mode_div:
            modes = tag_text(mode_div)
            print(f'study modes so far: {modes}')
            if 'online' in modes.lower():
                course_data['Online'] = 'Yes'
            if 'intensive' in modes.lower():
                course_data['Online'] = 'Yes'
                course_data[
                    'Blended'] = 'Yes'  # how do I know this? check here: https://www.sydney.edu.au/courses/courses/pc/master-of-medicine-advanced-clinical-neurophysiology.html
    except AttributeError:
        pass

    # AVAILABILITY (@todo: crude and semi-filtered... needs work.)
    try:
        av_div = soup.find('div', class_='b-component b-box-compact b-details-panel') \
            .find_all('div', class_='b-details-panel__row')[8]
        if av_div:
            av_text = tag_text(av_div) + ' | ' + course_data['Remarks']
            course_data['Remarks'] = av_text
    except (AttributeError, IndexError):
        try:
            av_div = soup.find('div', text=re.compile('^.*Availability for international students.*$', re.IGNORECASE)) \
                .find_parent() \
                .find_parent() \
                .find_next()
            if av_div:
                av_text = tag_text(av_div) + ' | ' + course_data['Remarks']
                course_data['Remarks'] = av_text.replace('\n', ' | ')
        except (AttributeError, IndexError):
            pass
        pass

    # CITIES
    try:
        location_tag = soup.find('div', class_='b-component b-box-compact b-details-panel') \
            .find_all('div', class_='b-details-panel__row')[5]
        if location_tag:
            location_string = tag_text(location_tag).lower()
            for i in possible_cities:
                if i.lower() in location_string:
                    if i not in actual_cities:
                        actual_cities.add(i)
    except (AttributeError, IndexError, TypeError):
        print('trouble extracting locations')

    # ==================================================================================================
    # DESCRIPTION
    DESC = '1'
    try:
        WebDriverWait(browser, delay_).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(text(), 'more information')]"))
        )
        show_more = browser.find_element_by_xpath(
            "(//a[contains(text(), 'more information')])[1]")
        show_more.click()
        each_url = browser.page_source
        soup = bs4.BeautifulSoup(each_url, 'lxml')
        try:
            ov_tag = soup.find('strong', text='About this course').find_parent('p').find_next_siblings('p')
            if ov_tag:
                DESC = tag_text(ov_tag)
                course_data['Description'] = tag_text(ov_tag)
        except AttributeError:
            try:
                ov_tag = soup.find('strong', text='About this course').find_parent('p').find_parent('div')
                if ov_tag:
                    DESC = tag_text(ov_tag)
                    course_data['Description'] = tag_text(ov_tag)
            except AttributeError:
                pass
    except (TimeoutException, NoSuchElementException, ElementNotInteractableException):
        pass
    try:
        if len(DESC.__str__()) < 10:
            ov_tag = soup.find('div', class_='b-see-more-content b-js-see-more-content')
            if ov_tag:
                DESC = tag_text(ov_tag)
                course_data['Description'] = tag_text(ov_tag).replace('\n', ' | ')
    except (AttributeError, TypeError):
        pass

    # LOCAL FEES
    try:
        WebDriverWait(browser, delay_).until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 "(//a[@class='b-dropdown-simple__button-toggle b-dropdown-simple__option                             b-link--block b-link--no-underline'])[2]"))
        )
        dropdown = browser.find_element_by_xpath(
            "(//a[@class='b-dropdown-simple__button-toggle b-dropdown-simple__option                             b-link--block b-link--no-underline'])[2]"
        )
        time.sleep(0.5)
        try:
            js = "var aa=document.getElementsByClassName('b-js-stickler-wrapper stuck')[0];aa.parentNode.removeChild(aa)"
            browser.execute_script(js)
            print('stickler wrapper deleted')
            each_url = browser.page_source
            soup = bs4.BeautifulSoup(each_url, 'lxml')
        except JavascriptException:
            pass
        dropdown.click()
        WebDriverWait(browser, delay_).until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 "//a[@href='javascript:void(0);' and contains(text(), 'an Australian citizen')]"))
        )
        local_option = browser.find_element_by_xpath(
            "//a[@href='javascript:void(0);' and contains(text(), 'an Australian citizen')]"
        )
        time.sleep(0.1)
        local_option.click()
        time.sleep(0.1)
    except (TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('trouble clicking local fees option')
    else:
        html_ = browser.page_source
        print('got local fees page source')
        soup_ = bs4.BeautifulSoup(html_, 'lxml')
        try:
            fee_tag = soup_.find('span', text=re.compile('^.*Tuition Fee for Domestic Students.*$', re.IGNORECASE))
            if fee_tag:
                print('found local fees')
                fees_temp = tag_text(fee_tag)  # .replace('$', '').replace('AUD', '').replace(',', '')
                head, sep, tail = fees_temp.partition('$')
                course_data['Local_Fees'] = tail.replace(',', '')
            if not fee_tag:
                fee_tag = soup_.find('span',
                                     text=re.compile('^.*Student Contribution Amount.*$', re.IGNORECASE))
                if fee_tag:
                    print('selecting SCA amount instead...')
                    fees_temp = tag_text(fee_tag)  # .replace('$', '').replace('AUD', '').replace(',', '')
                    head, sep, tail = fees_temp.partition('$')
                    course_data['Local_Fees'] = tail.replace(',', '')
        except AttributeError:
            print('cant find local fees')

    # INT FEES
    try:
        WebDriverWait(browser, delay_).until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 "(//a[@class='b-dropdown-simple__button-toggle b-dropdown-simple__option                             b-link--block b-link--no-underline'])[2]"))
        )
        dropdown = browser.find_element_by_xpath(
            "(//a[@class='b-dropdown-simple__button-toggle b-dropdown-simple__option                             b-link--block b-link--no-underline'])[2]"
        )
        time.sleep(0.5)
        try:
            js = "var aa=document.getElementsByClassName('b-js-stickler-wrapper stuck')[0];aa.parentNode.removeChild(aa)"
            browser.execute_script(js)
            print('stickler wrapper deleted')
            each_url = browser.page_source
            soup = bs4.BeautifulSoup(each_url, 'lxml')
        except JavascriptException:
            pass
        dropdown.click()
        WebDriverWait(browser, delay_).until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 "//a[@href='javascript:void(0);' and contains(text(), 'an International student')]"))
        )
        int_option = browser.find_element_by_xpath(
            "//a[@href='javascript:void(0);' and contains(text(), 'an International student')]"
        )
        time.sleep(0.1)
        int_option.click()
        time.sleep(0.1)
    except (TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('trouble clicking int fees option')
    else:
        html_ = browser.page_source
        print('got int fees page source')
        soup_ = bs4.BeautifulSoup(html_, 'lxml')
        try:
            fee_tag = soup_.find('span', text=re.compile('^.*Tuition Fee for International Students.*$', re.IGNORECASE))
            if fee_tag:
                print('found int fees')
                fees_temp = tag_text(fee_tag)  # .replace('$', '').replace('AUD', '').replace(',', '')
                head, sep, tail = fees_temp.partition('$')
                course_data['Int_Fees'] = tail.replace(',', '')
        except AttributeError:
            print('cant find int fees')

    # ATAR
    # "//label[contains(text(), 'Qualification')]/following-sibling::div/div/div/div/div/div/a/following-sibling::div/div/following-sibling::div/a"
    ATAR_DROP_XPATH = "//label[contains(text(), 'Qualification')]/following-sibling::div/div/div/div/div/div/a"
    ATAR_XPATH = "//label[contains(text(), 'Qualification')]/following-sibling::div/div/div/div/div/div/a/following-sibling::div/div/following-sibling::div/a"
    try:
        atar_dropdown = browser.find_element_by_xpath(
            f'{ATAR_DROP_XPATH}'
        )
        atar_option = browser.find_element_by_xpath(
            f'{ATAR_XPATH}'
        )
        time.sleep(0.1)
        atar_dropdown.click()
        time.sleep(0.1)
        atar_option.click()

        print('ATAR clicks done')
    except (TimeoutException, NoSuchElementException, ElementNotInteractableException):
        print('trouble clicking/finding ATAR')
    else:
        html_ = browser.page_source
        soup_ = bs4.BeautifulSoup(html_, 'lxml')
        try:
            atar_tag = soup_.find('p', text=re.compile('^.*Australian.*ATAR.*$', re.IGNORECASE)).find_next()
            if atar_tag:
                print('found atar')
                atar_val = tag_text(atar_tag).replace('Guaranteed', '')
                atar = re.findall(r'[-+]?\d*\.\d+|\d+', atar_val)
                course_data['Prerequisite_1'] = 'ATAR'
                course_data['Prerequisite_1_grade_1'] = atar[0]
        except (AttributeError, IndexError, TypeError):
            try:
                atar_tag = soup_.find('p', text=re.compile('^.*Australian.*ATAR.*$', re.IGNORECASE)).find_next()
                if atar_tag:
                    print('found atar')
                    atar = tag_text(atar_tag).replace('Guaranteed', '')
                    course_data['Prerequisite_1'] = 'ATAR'
                    course_data['Prerequisite_1_grade_1'] = atar
            except AttributeError:
                print('cant find atar')

    # PREREQUISITE 2, 3, 4 :: IELTS, TOEFL, PEARSON'S TEST OF ENGLISH
    # results location class name: b-paragraph b-box--slightly-transparent b-box--compact b-box--mid-grey b-component--tighter
    LANG_REQ_DROPDOWN_XPATH = "//div[@class='b-js-course-entry-requirements']/*/*/*/*/*/*/a"
    IELTS_REQ_OPTION_XPATH = "(//div[starts-with(@class, 'b-js-course-entry-requirements')]/*/*/*/*/*/*/a/following-sibling::div/*/a[contains(text(), 'IELTS')])[1]"
    TOEFL_REQ_OPTION_XPATH = "(//div[starts-with(@class, 'b-js-course-entry-requirements')]/*/*/*/*/*/*/a/following-sibling::div/*/a[contains(text(), 'TOEFL')])[1]"
    PEARSON_REQ_OPTION_XPATH = "(//div[starts-with(@class, 'b-js-course-entry-requirements')]/*/*/*/*/*/*/a/following-sibling::div/*/a[contains(text(), 'Pearson')])[1]"
    RESULTS_REQ_XPATH = "//div[@class='b-js-course-entry-requirements']//div[@class='b-form-control']/following::p[1]"
    RESULTS_REQ_CLASS = "b-paragraph b-box--slightly-transparent b-box--compact b-box--mid-grey b-component--tighter"

    # noinspection SpellCheckingInspection
    try:
        lang_req_dropdown = browser.find_element_by_xpath(
            f'{LANG_REQ_DROPDOWN_XPATH}'
        )
        ielts_option = browser.find_element_by_xpath(
            f'{IELTS_REQ_OPTION_XPATH}'
        )
        toefl_option = browser.find_element_by_xpath(
            f'{TOEFL_REQ_OPTION_XPATH}'
        )
        pearson_option = browser.find_element_by_xpath(
            f'{PEARSON_REQ_OPTION_XPATH}'
        )
        lang_req_dropdown.click()
        print('language requirements options expanded')

        try:    # to get IELTS score
            ielts_option.click()
        except (TimeoutException, NoSuchElementException, ElementNotInteractableException):
            print('trouble clicking ielts/ielts not available')
        else:
            try:
                html_ = browser.page_source
                soup_ = bs4.BeautifulSoup(html_, 'lxml')
                ielts_raw = browser.find_element_by_xpath(f'{RESULTS_REQ_XPATH}').text
                ielts_val = re.findall(r'[-+]?\d*\.\d+|\d+', ielts_raw)
                ielts = ielts_val[0]
                course_data['Prerequisite_2'] = 'IELTS'
                course_data['Prerequisite_2_grade_2'] = ielts
            except (AttributeError, IndexError, NoSuchElementException):
                print('ielts found, but unable to extract')

        try:    # to get TOEFL score
            lang_req_dropdown.click()
            toefl_option.click()
        except (TimeoutException, NoSuchElementException, ElementNotInteractableException):
            print('trouble clicking toefl/toefl not available')
        else:
            try:
                html_ = browser.page_source
                soup_ = bs4.BeautifulSoup(html_, 'lxml')
                toefl_raw = browser.find_element_by_xpath(f'{RESULTS_REQ_XPATH}').text
                toefl_val = re.findall(r'[-+]?\d*\.\d+|\d+', toefl_raw)
                toefl = toefl_val[0]
                course_data['Prerequisite_3'] = 'TOEFL'
                course_data['Prerequisite_3_grade_3'] = toefl
            except (AttributeError, IndexError, NoSuchElementException):
                print('toefl found, but unable to extract')

        try:    # to get PEARSON'S TEST OF ENGLISH score
            lang_req_dropdown.click()
            pearson_option.click()
        except (TimeoutException, NoSuchElementException, ElementNotInteractableException):
            print('trouble clicking pte/pte not available')
        else:
            try:
                html_ = browser.page_source
                soup_ = bs4.BeautifulSoup(html_, 'lxml')
                pte_raw = browser.find_element_by_xpath(f'{RESULTS_REQ_XPATH}').text
                pte_val = re.findall(r'[-+]?\d*\.\d+|\d+', pte_raw)
                pte = pte_val[0]
                course_data['Prerequisite_4'] = 'PTE'
                course_data['Prerequisite_4_grade_4'] = pte
            except (AttributeError, IndexError, NoSuchElementException):
                print('pte found, but unable to extract')
    except (TimeoutException, NoSuchElementException, ElementNotInteractableException):
        pass

    # SUBJECTS
    go_ahead: bool = False

    try:
        THE_XPATH = "//*[contains(text(), 'Units of Study')]/ancestor::*[1]"
        WebDriverWait(browser, delay).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, f'{THE_XPATH}'))
        )
        element = browser.find_element_by_xpath(f'{THE_XPATH}')
        element.click()
        time.sleep(0.2)
        go_ahead = True
    except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
        go_ahead = False
        print(f'cant open subjects listing: {e}')

    if go_ahead:
        subjects_links = []
        try:
            THE_XPATH = "//div[@data-m-el='m-courses-uos-landing-page']//form/following::ul//a//span[text()='2021']/ancestor::a[contains(@class, 'course-tag')]"
            WebDriverWait(browser, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{THE_XPATH}'))
            )
            a_tags = browser.find_elements_by_xpath(f'{THE_XPATH}')
            domain_url = "https://www.sydney.edu.au/"
            for a in a_tags:
                link = a.get_attribute('href')
                if link:
                    link_ = urljoin(domain_url, link)
                    if link_ not in subjects_links:
                        if link_ not in subjects_links:
                            subjects_links.append(link_)
                if len(subjects_links) is 40:
                    break

            THE_XPATH = "//a[@class='m-pagination__item']"
            WebDriverWait(browser, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{THE_XPATH}'))
            )
            pages = browser.find_elements_by_xpath(f'{THE_XPATH}')
            for page in pages:
                page.click()
                time.sleep(0.1)
                THE_XPATH = "//div[@data-m-el='m-courses-uos-landing-page']//form/following::ul//a//span[text()='2021']/ancestor::a[contains(@class, 'course-tag')]"
                WebDriverWait(browser, delay).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, f'{THE_XPATH}'))
                )
                a_tags = browser.find_elements_by_xpath(f'{THE_XPATH}')
                domain_url = "https://www.sydney.edu.au/"
                for a in a_tags:
                    link = a.get_attribute('href')
                    if link:
                        link_ = urljoin(domain_url, link)
                        if link_ not in subjects_links:
                            subjects_links.append(link_)
                    if len(subjects_links) is 40:
                        break

        except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
            print(f'cant extract subject links: {e}')
        try:
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
                    THE_XPATH = "//div[@data-js-el='overview-container']//p/ancestor::*[1]"
                    WebDriverWait(browser, delay).until(
                        EC.presence_of_all_elements_located(
                            (By.XPATH, f'{THE_XPATH}'))
                    )
                    value = browser.find_element_by_xpath(f'{THE_XPATH}')
                    course_data[f'Subject_Description_{i}'] = tag_text(
                        bs4.BeautifulSoup('<div>' + value.get_attribute('innerHTML') + '</div>', 'lxml'))
                except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
                    print(f'cant extract subject description {i}: {e}')
                print(f"SUBJECT {i}: {course_data[f'Subject_or_Unit_{i}']}\n"
                      f"SUBJECT DESCRIPTION {i}: {course_data[f'Subject_Description_{i}']}\n")
                if i is 40:
                    break
                i += 1
        except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
            print(f'cant extract subjects: {e}')

    else:
        print('unfortunately subjects cant be obtained')

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
    print('PEARSONS TEST OF ENGLISH: ', course_data['Prerequisite_4_grade_4'])
    print('IELTS: ', course_data['Prerequisite_2_grade_2'])
    print('TOEFL: ', course_data['Prerequisite_3_grade_3'])
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
