import copy
import csv
import json
import re
import time
from pathlib import Path

# noinspection PyProtectedMember
from bs4 import Comment
from selenium import webdriver
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

# read the url from each file into a list
course_links_file_path = Path(os.getcwd().replace('\\', '/'))
course_links_file_path = course_links_file_path.__str__() + '/griffith_masters_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'Griff_Mast_Data.csv'

level_key = TemplateData.level_key  # dictionary of course levels

faculty_key = TemplateData.faculty_key  # dictionary of course levels

currency_pattern = "(?:[\£\$\€\(RM)\]{1}[,\d]+.?\d*)"  # regex pattern for finding currency or cash amount strings

course_data_all = []

course_data_template = {'Level_Code': '', 'University': 'Griffith University', 'City': '', 'Course': '',
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

possible_cities = {'Gold Coast': 'Brisbane',    # > Southport > Gold Coast > Brisbane > Queensland
                   'Logan': 'Brisbane',         # > Brisbane > Queensland
                   'Mt Gravatt': 'Brisbane',    # > Brisbane > Queensland
                   'Nathan': 'Brisbane',        # > Brisbane > Queensland
                   'South Bank': 'Brisbane'     # > Brisbane > Queensland
                   }

other_cities = {'Offshore': '',
                'Digital (Online)': '',
                'Distance Education': '',
                'Open Universities Australia': ''
                }

campuses = set()

# MAIN ROUTINE
for each_url in course_links_file:

    course_data = {'Level_Code': '', 'University': 'Griffith University', 'City': '', 'Course': '',
                   'Faculty': '',
                   'Int_Fees': '', 'Local_Fees': '', 'Currency': 'AUD', 'Currency_Time': 'Years', 'Duration': '',
                   'Duration_Time': '', 'Full_Time': 'Yes', 'Part_Time': 'No',
                   'Prerequisite_1': '', 'Prerequisite_1_grade_1': '',  # ATAR
                   'Prerequisite_2': '', 'Prerequisite_2_grade_2': '',  # IELTS
                   'Prerequisite_3': '', 'Prerequisite_3_grade_3': '',  # GPA
                   'Website': '', 'Course_Lang': 'English', 'Availability': 'A', 'Description': '',
                   'Career_Outcomes': '',
                   'Country': 'Australia', 'Online': 'No', 'Offline': 'Yes', 'Distance': 'No', 'Face_to_Face': 'Yes',
                   'Blended': 'No', 'Remarks': ''}

    actual_cities = []

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
    div1 = soup.find('div', class_='banner study feature').find('div', class_='flex')
    if div1:
        course = tag_text(div1)
        course_data['Course'] = course
    print('COURSE NAME: ', course_data['Course'])

    # AVAILABILITY
    course_data['Availability'] = 'A'
    print('AVAILABILITY: ', course_data['Availability'])

    # COURSE DESCRIPTION
    try:
        div1 = soup.find('div', class_='degree-content', itemprop=re.compile('description')).find('div')
        if div1:
            p_tags = div1.find_all('p')
            if p_tags:
                descriptions = [tag_text(p) for p in p_tags]
                description = ' '.join(descriptions)
                course_data['Description'] = description
    except AttributeError:
        div1 = soup.find('div', class_='degree-content', itemprop='description')
        if div1:
            description = tag_text(div1)
            course_data['Description'] = description
        pass
    print('DESCRIPTION: ', course_data['Description'])

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

    # INTERNATIONAL FEES
    try:
        dd_fee = soup.find('dt', class_='info-group-title__ fee').find_next('dd')
        if dd_fee:
            int_fees = tag_text(dd_fee).split()[0].replace('$', '').replace('*', '')
            course_data['Int_Fees'] = int_fees
            course_data['Currency_Time'] = 'Years'
    except AttributeError:
        print('No international fees available for this course')
        course_data['Int_Fees'] = ''
        course_data['Currency_Time'] = ''

    # PREREQUISITE 2 (IELTS)/ PREREQUISITE 3 (GPA)
    try:  # attempt to get IELTS
        div1 = soup.find('div', class_='requirements-badges').find('div')
        if div1:
            ielts_temp = tag_text(div1)
            g = ielts_temp
            if '4.' in g or '5.' in g or '6.' in g or '7.' or '8.' in g or '9.' in g \
                    and '4/' not in g and '6/' not in g and '7/' not in g and '8/' not in g:
                try:
                    ielts_temp_1 = int(list(filter(str.isdigit, g))[0])
                    ielts_temp_2 = int(list(filter(str.isdigit, g))[1])
                    ielts_temp_val = str(ielts_temp_1) + '.' + str(ielts_temp_2)
                    course_data['Prerequisite_2_grade_2'] = ielts_temp_val
                    course_data['Prerequisite_2'] = 'IELTS'
                except IndexError:
                    ielts_temp_1 = int(list(filter(str.isdigit, g))[0])
                    course_data['Prerequisite_2_grade_2'] = ielts_temp_1
                    course_data['Prerequisite_2'] = 'IELTS'
            elif '4' in g or '5' in g or '6' in g or '7' in g or '8' in g:
                ielts_temp_1 = int(list(filter(str.isdigit, g))[0])
                course_data['Prerequisite_2_grade_2'] = ielts_temp_1
                course_data['Prerequisite_2'] = 'IELTS'
    except AttributeError:  # get the GPA instead
        span_p = soup.find('span', itemprop=re.compile('coursePrerequisites')).find('p')
        if 'GPA' in tag_text(span_p):
            print('No IELTS value, switching to GPA...')
            gpa_temp = tag_text(span_p)
            g = gpa_temp
            if '4.' in g or '5.' in g or '6.' in g or '7.' or '8.' in g or '9.' in g \
                    and '4/' not in g and '6/' not in g and '7/' not in g and '8/' not in g:
                gpa_temp_1 = int(list(filter(str.isdigit, g))[0])
                gpa_temp_2 = int(list(filter(str.isdigit, g))[1])
                gpa_temp_val = str(gpa_temp_1) + '.' + str(gpa_temp_2)
                course_data['Prerequisite_3_grade_3'] = gpa_temp_val
                course_data['Prerequisite_3'] = 'GPA'
                if 'Any 2 OUA' in g:
                    gpa_temp_1 = int(list(filter(str.isdigit, g))[1])
                    gpa_temp_2 = int(list(filter(str.isdigit, g))[2])
                    gpa_temp_val = str(gpa_temp_1) + '.' + str(gpa_temp_2)
                    course_data['Prerequisite_3_grade_3'] = gpa_temp_val
                    course_data['Prerequisite_3'] = 'GPA'
            elif '4' in g or '5' in g or '6' in g or '7' in g or '8' in g:
                gpa_temp_1 = int(list(filter(str.isdigit, g))[0])
                course_data['Prerequisite_3_grade_3'] = gpa_temp_1
                course_data['Prerequisite_3'] = 'GPA'
                if 'Any 2 OUA' in g:
                    gpa_temp_1 = int(list(filter(str.isdigit, g))[1])
                    gpa_temp_val = str(gpa_temp_1)
                    course_data['Prerequisite_3_grade_3'] = gpa_temp_val
                    course_data['Prerequisite_3'] = 'GPA'

            print(tag_text(span_p))
        else:
            course_data['Prerequisite_2'] = ''
            course_data['Prerequisite_2_grade_2'] = ''
            course_data['Prerequisite_3'] = ''
            course_data['Prerequisite_3_grade_3'] = ''

    # CITY (actually campus), DISTANCE LEARNING, ONLINE LEARNING
    dt1 = soup.find('dt', class_='info-group-title__ campus', text=re.compile('Campus', re.IGNORECASE))
    if dt1:
        dd_tags = dt1.find_next_siblings('dd')
        if dd_tags:
            campus_list = list()
            campus_list_string = str()
            for dd in dd_tags:
                campus_list.append(tag_text(dd))
            campus_list_string = ' '.join(campus_list)
            if 'online' in campus_list_string.lower():
                course_data['Online'] = 'Yes'
            if 'distance education' in campus_list_string.lower():
                course_data['Distance'] = 'Yes'
            if 'open universities australia' in campus_list_string.lower():
                course_data['Online'] = 'Yes'
                course_data['Offline'] = 'No'
                course_data['Face_to_Face'] = 'No'
            for i in possible_cities:
                if i.lower() in campus_list_string.lower():
                    course_data['City'] = possible_cities[i]
                    course_data['Offline'] = 'Yes'
                    course_data['Face_to_Face'] = 'Yes'
                    break
            print('STUDY OPTIONS: ', campus_list_string)

    # CAREER OUTCOMES
    try:
        section_div = soup.find('section', id='career-outcomes').find('div').find('div').find('div')
        if section_div:
            p_tags = section_div.find_all('p')
            if p_tags:
                outcomes = [tag_text(p) for p in p_tags]
                career_outcome = ' '.join(outcomes)
                course_data['Career_Outcomes'] = career_outcome
    except AttributeError:
        course_data['Career_Outcomes'] = ''
        print('no career outcomes listed')

    print('CITY: ', course_data['City'])
    print('OFFLINE: ', course_data['Offline'])

    # DURATION, PART-TIME, FULL TIME
    dt1 = soup.find('dt', class_='info-group-title__ duration', text=re.compile('Duration', re.IGNORECASE))
    if dt1:
        dd1 = dt1.find_next('dd')
        if dd1:
            duration_raw = tag_text(dd1)
            p_word = duration_raw
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

            if 'full-time' in duration_raw or 'full time' in duration_raw:
                course_data['Full_Time'] = 'Yes'
            if 'online' in duration_raw.lower():
                course_data['Online'] = 'Yes'
            if 'online only' in duration_raw.lower():
                course_data['Face_to_Face'] = 'No'
                course_data['Offline'] = 'No'
            dd2 = dd1.find_next_sibling('dd')
            if dd2:
                duration_part_time_raw = tag_text(dd2)
                if 'part-time' in duration_part_time_raw:
                    course_data['Part_Time'] = 'Yes'
                if 'online' in duration_part_time_raw.lower():
                    course_data['Online'] = 'Yes'

    if course_data['Online'] == 'Yes' and course_data['Offline'] == 'Yes' and course_data['Distance'] == 'Yes' \
            and course_data['Part_Time'] == 'Yes' and course_data['Full_Time'] == 'Yes':
        course_data['Blended'] = 'Yes'

    """
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.wait import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    html_ = None
    browser_ = webdriver.Chrome(executable_path=exec_path)
    browser_.get(course_data['Website'])
    time.sleep(3)
    try:
        browser_.execute_script("arguments[3].click();", WebDriverWait(browser_, 2).until(
            EC.element_to_be_clickable((By.LINK_TEXT, '"International"'))))
    except TimeoutException:
        print('Timeout Exception: Failed')
    else:
        html_ = browser_.page_source
        print('got page source')
    if html_:
        soup_ = bs4.BeautifulSoup(html_, 'lxml')
        if soup_:
            # PREREQUISITE 1 (ATAR)
            try:
                span = soup_.find('div', class_='requirements-badges').find('div').find('span')
                if span:
                    print('found span')
                    atar = tag_text(span)
                    course_data['Prerequisite_1'] = 'ATAR'
                    course_data['Prerequisite_1_grade_1'] = atar
            except AttributeError:
                print('No ATAR for this course.')
                course_data['Prerequisite_1'] = 'ATAR'
                course_data['Prerequisite_1_grade_1'] = ''
    """

    print('INT FEES: ', course_data['Int_Fees'])
    print('ATAR: ', course_data['Prerequisite_1_grade_1'])
    print('IELTS: ', course_data['Prerequisite_2_grade_2'])
    print('GPA: ', course_data['Prerequisite_3_grade_3'])
    print('FULL TIME: ', course_data['Full_Time'])
    print('PART-TIME: ', course_data['Part_Time'])
    print('DISTANCE: ', course_data['Distance'])
    print('BLENDED: ', course_data['Blended'])
    print('ONLINE: ', course_data['Online'])
    print('FACE TO FACE: ', course_data['Face_to_Face'])
    print('OUTCOMES: ', course_data['Career_Outcomes'])
    print()

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
