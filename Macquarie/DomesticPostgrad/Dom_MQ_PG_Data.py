import copy
import csv
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

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
    except Exception as e:
        pass
    return None


def remove_banned_words(to_print, database_regex):
    pattern = re.compile(r"\b(" + "|".join(database_regex) + ")\\W", re.I)
    return pattern.sub("", to_print)


def save_data_json(title, data):
    with open(title, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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
option.add_argument("headless")
exec_path = Path(os.getcwd().replace('\\', '/'))
exec_path = exec_path.parent.parent.parent.parent.__str__() + '/Libraries/Google/v86/chromedriver.exe'
browser = webdriver.Chrome(executable_path=exec_path, chrome_options=option)

option2 = webdriver.ChromeOptions()
option2.add_argument(" - incognito")
browser2 = webdriver.Chrome(executable_path=exec_path, chrome_options=option2)

delay = 4

# read the url from each file into a list
course_links_file_path = Path(os.getcwd().replace('\\', '/'))
course_links_file_path = course_links_file_path.__str__() + '/mq_dom_postgrad_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'MQ_Dom_PG_Data.csv'

course_data_template = {'Level_Code': '', 'University': 'Macquarie University', 'City': '', 'Course': '',
                        'Faculty': '',
                        'Int_Fees': '', 'Local_Fees': '', 'Currency': 'AUD', 'Currency_Time': 'Years', 'Duration': '',
                        'Duration_Time': '', 'Full_Time': 'Yes', 'Part_Time': 'No',
                        'Prerequisite_1': '', 'Prerequisite_1_grade_1': '',
                        'Prerequisite_2': '', 'Prerequisite_2_grade_2': '',
                        'Website': '', 'Course_Lang': 'English', 'Availability': 'D', 'Description': '',
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

level_key = TemplateData.level_key  # dictionary of course levels

faculty_key = TemplateData.faculty_key  # dictionary of course levels

currency_pattern = "(?:[\£\$\€\(RM)\]{1}[,\d]+.?\d*)"  # regex pattern for finding currency or cash amount strings

course_data_all = []

campuses = set()

# MAIN ROUTINE
for each_url in course_links_file:

    course_data = {'Level_Code': '', 'University': 'Macquarie University', 'City': '', 'Course': '',
                   'Faculty': '',
                   'Int_Fees': '', 'Local_Fees': '', 'Currency': 'AUD', 'Currency_Time': 'Years', 'Duration': '',
                   'Duration_Time': '', 'Full_Time': 'Yes', 'Part_Time': 'No',
                   'Prerequisite_1': '', 'Prerequisite_1_grade_1': '',
                   'Prerequisite_2': '', 'Prerequisite_2_grade_2': '',
                   'Website': '', 'Course_Lang': 'English', 'Availability': 'D', 'Description': '',
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

    actual_cities = []

    browser.get(each_url)
    time.sleep(2)
    url__ = each_url
    pure_url = each_url.strip()
    print('CURRENT LINK: ', pure_url)
    each_url = browser.page_source

    soup = bs4.BeautifulSoup(each_url, 'html.parser')

    all_text = soup.text.replace('\n', '').strip()

    # COURSE URL
    course_data['Website'] = pure_url

    # COURSE NAME
    h1 = soup.find('h1')
    if h1:
        course_data['Course'] = tag_text(h1)
        print('COURSE NAME: ', tag_text(h1))
        if 'is unavailable' in tag_text(h1):
            course_data['Availability'] = 'N'
            course_data['Face_to_Face'] = 'No'
            course_data['Online'] = 'No'
            course_data['Offline'] = 'No'
            course_data['Blended'] = 'No'
            course_data['Part_Time'] = 'No'
            course_data['Full_Time'] = 'No'
            course_data['City'] = ''
            course_data['Prerequisite_2_grade_2'] = ''
            course_data['Prerequisite_2'] = ''
            print('COURSE NAME: ', tag_text(h1))
            print('AVAILABILITY: ', course_data['Availability'])

        else:
            course_data['Availability'] = 'D'
            course_data['Face_to_Face'] = 'Yes'
            course_data['Online'] = 'No'
            course_data['Offline'] = 'Yes'
            course_data['Blended'] = 'No'
            course_data['Part_Time'] = 'No'
            course_data['Full_Time'] = 'Yes'
            course_data['Prerequisite_1_grade_1'] = ''
            course_data['Prerequisite_2_grade_2'] = ''
            course_data['Prerequisite_2'] = ''
            print('AVAILABILITY: ', course_data['Availability'])

            # DECIDE THE LEVEL CODE
            for i in level_key:
                for j in level_key[i]:
                    if j in course_data['Course']:
                        course_data['Level_Code'] = i
            print('LEVEL CODE: ', course_data['Level_Code'])

            # DECIDE THE FACULTY
            for i in faculty_key:
                for j in faculty_key[i]:
                    if j.lower() in course_data['Course'].lower():
                        course_data['Faculty'] = i
            print('FACULTY: ', course_data['Faculty'])

            # DURATION
            # DELIVERY MODE (ONLINE, FACE TO FACE, OFFLINE)
            div1 = soup.find('div', class_='src-components-ProgramMeta-___programMeta__program-meta-data___2OQpy') \
                .find('div').find('div')
            if div1:
                program_divs = div1.find_all('div')
                for div in program_divs:
                    h4 = div.find('h4')
                    if h4:

                        # DURATION
                        if 'duration' in h4.contents[0].__str__().lower():
                            p_tag = div.find('p')
                            p_word = tag_text(p_tag)
                            if 'year' in p_word.__str__().lower():
                                value_conv = DurationConverter.convert_duration(p_word)
                                duration = float(
                                    ''.join(filter(str.isdigit, str(value_conv)))[0])
                                duration_time = 'Years'
                                if str(duration) == '1' or str(duration) == '1.00' or str(
                                        duration) == '1.0':
                                    duration_time = 'Year'
                                course_data['Duration'] = duration
                                course_data['Duration_Time'] = duration_time
                                print('DURATION + DURATION TIME: ', duration, duration_time)
                            # print(tag_text(div_span))
                            elif 'month' in p_word.__str__().lower():
                                value_conv = DurationConverter.convert_duration(p_word)
                                duration = float(
                                    ''.join(filter(str.isdigit, str(value_conv)))[0])
                                duration_time = 'Months'
                                if str(duration) == '1' or str(duration) == '1.00' or str(
                                        duration) == '1.0':
                                    duration_time = 'Month'
                                course_data['Duration'] = duration
                                course_data['Duration_Time'] = duration_time
                                print('DURATION + DURATION TIME: ', duration, duration_time)

            # PART TIME/ FULL TIME
            h4 = soup.find_all('h4', class_='src-components-ProgramMeta-___programMeta__title___2M-m9')[1]
            if h4:
                div = h4.find_parent('div')
                if 'study mode' in h4.text.__str__().lower():
                    p_tag = div.find('p')
                    p_word = tag_text(p_tag)
                    if 'full-time' in p_word.lower():
                        course_data['Full_Time'] = 'Yes'
                    if 'part-time' in p_word.lower():
                        course_data['Part_Time'] = 'Yes'
                    print('FULL TIME: ', course_data['Full_Time'])
                    print('PART-TIME: ', course_data['Part_Time'])

            # CITY
            h4 = soup.find_all('h4', class_='src-components-ProgramMeta-___programMeta__title___2M-m9')[2]
            if h4:
                div = h4.find_parent('div')
                if 'attendance' in h4.text.__str__().lower():
                    p_tag = div.find('p')
                    p_word = tag_text(p_tag)
                    if 'off-campus' in p_word.lower():
                        course_data['City'] = p_word
                        course_data['Distance'] = 'Yes'
                    else:
                        course_data['City'] = p_word
                        course_data['Distance'] = 'No'
                    if 'hong kong' in p_word.lower():
                        course_data['City'] = p_word
                        course_data['Distance'] = 'Yes'
                    else:
                        course_data['City'] = p_word
                        course_data['Distance'] = 'No'
                    if 'off-shore' in p_word.lower():
                        course_data['City'] = p_word
                        course_data['Distance'] = 'Yes'
                    else:
                        course_data['City'] = p_word
                        course_data['Distance'] = 'No'
                    if 'city' in p_word.lower():
                        course_data['City'] = p_word
                        course_data['Distance'] = 'Yes'
                    else:
                        course_data['City'] = p_word
                        course_data['Distance'] = 'No'
                    if 'korea' in p_word.lower():
                        course_data['City'] = p_word
                        course_data['Distance'] = 'Yes'
                    else:
                        course_data['City'] = p_word
                        course_data['Distance'] = 'No'
                    if 'online' in p_word.lower():
                        course_data['Online'] = 'Yes'
                    else:
                        course_data['City'] = p_word
                        course_data['Distance'] = 'No'

                    print('CITY/CAMPUS: ', course_data['City'])

            # INT FEES
            p_tags = soup.find_all('p', class_='src-components-ProgramMeta-___programMeta__info___1PJy1')
            if p_tags:
                for p in p_tags:
                    if 'estimated annual fee' in tag_text(p).lower():
                        int_fee_raw = tag_text(p)
                        int_fee = re.findall(currency_pattern, int_fee_raw)[0].replace('$', '').replace('?', '')
                        course_data['Int_Fees'] = int_fee
                        print('INT FEES: ', course_data['Int_Fees'])
                        break

            # DESCRIPTION
            div1 = soup.find('div', class_='tick-list')
            if div1:
                div_minus_1 = div1.find_previous_sibling('div')
                if div_minus_1:
                    overview_content = tag_text(div_minus_1)
                    course_data['Description'] = overview_content
            print('DESCRIPTION: ', course_data['Description'])

            # CAREER OUTCOMES
            professions_text = 'PROFESSIONS: '
            employers_text = 'EMPLOYERS: '
            h4 = soup.find('h4', text='Professions')
            try:
                if h4:
                    li = h4.find_next('div').find('ul').find_all('li')
                    if li:
                        professions = [tag_text(i) for i in li]
                        professions_text += '. '.join(professions).strip()
                        print('PROFESSIONS: ', professions_text)
            except AttributeError:
                pass
            h4 = soup.find('h4', text='Employers')
            if h4:
                try:
                    li = h4.find_next('div').find('ul').find_all('li')
                    if li:
                        employers = [tag_text(i) for i in li]
                        employers_text += '. '.join(employers).strip()
                        print('EMPLOYERS: ', employers_text)
                    course_data['Career_Outcomes'] = professions_text + employers_text
                except AttributeError:
                    h4 = soup.find('h4', text=re.compile('Employers', re.IGNORECASE))
                    if h4:
                        p = h4.find_next('div').find('p')
                        if p:
                            course_data['Career_Outcomes'] = tag_text(p)
                            print('OUTCOMES COMBINED: ', employers_text)

            # SUBJECTS
            try:
                browser2.get(pure_url)
                time.sleep(0.5)
                SUBJECTS_XPATH = "(//a[contains(text(), 'Course Structure')])[1]"
                WebDriverWait(browser2, 2).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, f'{SUBJECTS_XPATH}'))
                )
                course_structure = browser2.find_element_by_xpath(f'{SUBJECTS_XPATH}')
                course_structure.click()

                THE_XPATH = "//table[@class='table zones']/tbody/tr/td/a[@href]"
                WebDriverWait(browser2, 2).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, f'{THE_XPATH}'))
                )
                values = browser2.find_elements_by_xpath(f'{THE_XPATH}')

                a_tags = set().union(i for i in values)
                subjects_links = []
                subject_names = []
                subject_names_links_map = dict()
                domain_url = "https://coursehandbook.mq.edu.au/"
                delay = 3
                for a in a_tags:
                    link = a.get_attribute('href')
                    if link:
                        link_ = link
                        if link_ not in subjects_links:
                            if link_ not in subjects_links:
                                subjects_links.append(link_)
                                subject_names.append(a.get_attribute('text'))
                    if len(subjects_links) is 40:
                        break
                i = 1
                for sn in subject_names:
                    course_data[f'Subject_or_Unit_{i}'] = sn
                    print(f"SUBJECT {i}: {course_data[f'Subject_or_Unit_{i}']}")
                    i += 1
            except (
                    AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
                print(f'cant extract subjects: {e}')

            """
            # REMARKS
            # reset it first to avoid any replication
            h4 = soup.find('h4', text='Notes')
            if h4:
                p = h4.find_next('div').find('p')
                if p:
                    p_word = tag_text(p)
                    course_data['Remarks'] = p_word
                    print('REMARKS: ', p_word)
                else:
                    course_data['Remarks'] = ''
            """

            """
            # PREREQUISITES
            # very frustrating that we have to reset before continuing
            # PREREQUISITE 2 : IELTS
            new_url = course_data['Website'] + "/entry-requirements#content"
            browser.get(new_url)
            time.sleep(2)
            new_each_url = browser.page_source
            new_soup = bs4.BeautifulSoup(new_each_url, 'html.parser')
            p_q_ielts = new_soup.find('p', text=re.compile('Academic IELTS of', re.IGNORECASE))
            if p_q_ielts:
                g = tag_text(p_q_ielts)
                if '4' in g or '5' in g or '6' in g or '7' or '8' in g or '9' in g \
                        and '4/' not in g and '6/' not in g and '7/' not in g and '8/' not in g:
                    ielts_temp_1 = int(list(filter(str.isdigit, g))[0])
                    ielts_temp_2 = int(list(filter(str.isdigit, g))[1])
                    ielts_temp = str(ielts_temp_1) + '.' + str(ielts_temp_2)
                    course_data['Prerequisite_2_grade_2'] = ielts_temp
                elif '4/' in g or '5/' in g or '6/' in g or '7/' in g or '8/' in g:
                    ielts_temp_1 = int(list(filter(str.isdigit, g))[0])
                    course_data['Prerequisite_2_grade_2'] = ielts_temp_1
            print('IELTS: ', course_data['Prerequisite_2_grade_2'])
            """

            """
            # PREREQUISITE 1:
            li = new_soup.find('li', text=re.compile("^AQF level 7 bachelor's qualification", re.IGNORECASE))
            if li:
                gpa_raw = li.get_text().__str__().strip()
                g = gpa_raw.lower()
                if 'gpa' in g:
                    try:
                        if '4.' in g or '5.' in g or '6.' in g or '7.' \
                                and '4/' not in g and '6/' not in g and '7/' not in g:
                            gpa_temp_1 = int(list(filter(str.isdigit, gpa_raw))[1])
                            gpa_temp_2 = int(list(filter(str.isdigit, gpa_raw))[2])
                            gpa_temp = str(gpa_temp_1) + '.' + str(gpa_temp_2)
                            course_data['Prerequisite_1_grade_1'] = gpa_temp
                        else:
                            course_data['Prerequisite_1_grade_1'] = ''
                    except IndexError:
                        next_li = li.find_next('li', text=re.compile("^Minimum GPA of", re.IGNORECASE))
                        if next_li:
                            gpa_raw = next_li.get_text().__str__().strip()
                            g = gpa_raw.lower()
                            if 'gpa' in g:
                                if '4.' in g or '5.' in g or '6.' in g or '7.' \
                                        and '4/' not in g and '6/' not in g and '7/' not in g:
                                    gpa_temp_1 = int(list(filter(str.isdigit, gpa_raw))[1])
                                    gpa_temp_2 = int(list(filter(str.isdigit, gpa_raw))[2])
                                    gpa_temp = str(gpa_temp_1) + '.' + str(gpa_temp_2)
                                    course_data['Prerequisite_1_grade_1'] = gpa_temp
                                else:
                                    course_data['Prerequisite_1_grade_1'] = ''

            print('GPA: ', course_data['Prerequisite_1_grade_1'])
            """

    course_data_all.append(copy.deepcopy(course_data))

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

browser2.quit()
