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
course_links_file_path = course_links_file_path.__str__() + '/bond_pg_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'Bond_PG_Data.csv'

level_key = TemplateData.level_key  # dictionary of course levels

faculty_key = TemplateData.faculty_key  # dictionary of course levels

currency_pattern = "(?:[\£\$\€\(RM)\]{1}[,\d]+.?\d*)"  # regex pattern for finding currency or cash amount strings

course_data_all = []

city_set = set()

course_data_template = {'Level_Code': '', 'University': 'Bond University', 'City': '', 'Course': '',
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

possible_cities = {'gold coast': 'Gold Coast',
                   'lismore': 'New South Wales',
                   'brisbane': 'Brisbane',
                   'melbourne': 'Melbourne',
                   'coomera': 'Gold Coast',
                   'sydney': 'Sydney',
                   'coffs harbour': 'New South Wales',
                   'new south wales': 'New South Wales',
                   'online': ''}

other_cities = {}

campuses = set()

sample = ['https://bond.edu.au/program/bachelor-international-relations-bachelor-laws']

# MAIN ROUTINE
for each_url in course_links_file:

    course_data = {'Level_Code': '', 'University': 'Bond University', 'City': 'Gold Coast', 'Course': '',
                   'Faculty': '',
                   'Int_Fees': '', 'Local_Fees': '', 'Currency': 'AUD', 'Currency_Time': 'Semesters', 'Duration': '',
                   'Duration_Time': '', 'Full_Time': 'Yes', 'Part_Time': 'No',
                   'Prerequisite_1': '', 'Prerequisite_1_grade_1': '',  # ATAR
                   'Prerequisite_2': '', 'Prerequisite_2_grade_2': '',  # IELTS (Also used for OP)
                   'Prerequisite_3': '', 'Prerequisite_3_grade_3': '',  # GPA (Also used for IB)
                   'Website': '', 'Course_Lang': 'English', 'Availability': 'A', 'Description': '',
                   'Career_Outcomes': '',
                   'Country': 'Australia', 'Online': 'No', 'Offline': 'Yes', 'Distance': 'No', 'Face_to_Face': 'Yes',
                   'Blended': 'No', 'Remarks': ''}

    actual_cities = []

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
    h1 = soup.find('h1', {'class': 'page-title'})
    if h1:
        course_data['Course'] = tag_text(h1)

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

    # DURATION TEXT
    duration_td = soup.find('strong', text=re.compile('Duration', re.IGNORECASE))\
        .find_parent('td')\
        .find_next('td')
    if duration_td:
        duration_data = tag_text(duration_td)
        duration = DurationConverter.convert_duration(duration_data)
        course_data['Duration'] = duration[0]
        course_data['Duration_Time'] = duration[1]
        if duration[0] < 2 and 'month' in duration[1].lower():
            course_data['Duration'] = duration[0]
            course_data['Duration_Time'] = 'Month'
        if duration[0] < 2 and 'year' in duration[1].lower():
            course_data['Duration'] = duration[0]
            course_data['Duration_Time'] = 'Year'
        if duration[0] > 48 and 'month' in duration[1].lower():
            course_data['Duration'] = 4
            course_data['Duration_Time'] = 'Years'
        print('duration so far: ', duration)
    print('DURATION + DURATION TIME: ', course_data['Duration'], course_data['Duration_Time'])

    # DESCRIPTION
    try:
        data_tag = soup.find('a', {'id': 'about', 'data-anchor-label': 'About the program', 'class': 'anchor'})\
            .find_parent('section').find('div', class_='show-more-content').find('div', id='show-less-0').find('p')
        if data_tag:
            description = tag_text(data_tag)
            course_data['Description'] = description
    except AttributeError:
        data_tag = soup.find('a', {'id': 'overview', 'data-anchor-label': 'Overview', 'class': 'anchor'})\
            .find_parent('section').find_all('p')
        if data_tag:
            description_list = [tag_text(p) for p in data_tag]
            description = ' '.join(description_list)
            course_data['Description'] = description

    # STUDY MODE
    try:
        tag_1 = soup.find('strong', text=re.compile('Mode')).find_parent('td').find_next('td')
        if tag_1:
            mode = tag_text(tag_1)
            if 'on campus' in mode.lower():
                course_data['Offline'] = 'Yes'
                course_data['Face_to_Face'] = 'Yes'
            if 'remote' in mode.lower() or 'online' in mode.lowr():
                course_data['Online'] = 'Yes'
    except AttributeError:
        tag_1 = soup.find('table', {'class': 'table table-bordered table-hover table-striped'})\
            .find('tbody').find('tr').find('td', {'style': 'width: 594px;'})
        if tag_1:
            mode = tag_text(tag_1)
            if 'on campus' in mode.lower():
                course_data['Offline'] = 'Yes'
                course_data['Face_to_Face'] = 'Yes'
            if 'remote' in mode.lower() or 'online' in mode.lowr():
                course_data['Online'] = 'Yes'

    # LOCAL FEES 2020
    try:
        fee_tag = soup.find('strong', text=re.compile('Total program fee:', re.IGNORECASE))\
            .find_parent('p').find_next('ul').find('li')
        if fee_tag:
            fee_tag.strong.decompose()
            local_fees = tag_text(fee_tag).replace('* per semester average', '').replace('$', '').replace(',', '')
            course_data['Local_Fees'] = local_fees
            course_data['Currency_Time'] = 'Semesters'
    except AttributeError:
        try:
            fee_tag = soup.find('strong', text=re.compile('Annual program fee:', re.IGNORECASE)) \
                .find_parent('p').find_next('ul').find('li')
            if fee_tag:
                fee_tag.strong.decompose()
                local_fees = tag_text(fee_tag).replace('* annually', '').replace('$', '').replace(',', '')
                course_data['Local_Fees'] = local_fees
                course_data['Currency_Time'] = 'Years'
        except AttributeError:
            try:
                fee_tag = soup.find('strong', text=re.compile('Semester program fees:', re.IGNORECASE)) \
                    .find_parent('p').find_next('ul').find('li')
                if fee_tag:
                    fee_tag.strong.decompose()
                    local_fees = tag_text(fee_tag).replace('* per semester average', '').replace('$', '').replace(',', '')
                    course_data['Local_Fees'] = local_fees
                    course_data['Currency_Time'] = 'Semesters'
            except AttributeError:
                print('2020 local fees not provided')
    # LOCAL FEES 2021
    try:
        fee_tag = soup.find('strong', text=re.compile('Total program fee:', re.IGNORECASE))\
            .find_parent('p').find_next('ul').find_all('li')[1]
        if fee_tag:
            fee_tag.strong.decompose()
            local_fees = tag_text(fee_tag).replace('* per semester average', '').replace('$', '').replace(',', '')
            print('local fees 2021: ', local_fees)
    except (AttributeError, IndexError):
        try:
            fee_tag = soup.find('strong', text=re.compile('Annual program fee:', re.IGNORECASE)) \
                .find_parent('p').find_next('ul').find_all('li')[1]
            if fee_tag:
                fee_tag.strong.decompose()
                local_fees = tag_text(fee_tag).replace('* annually', '').replace('$', '').replace(',', '')
                print('local fees 2021: ', local_fees)
        except (AttributeError, IndexError):
            try:
                fee_tag = soup.find('strong', text=re.compile('Semester program fees:', re.IGNORECASE)) \
                    .find_parent('p').find_next('ul').find_all('li')[1]
                if fee_tag:
                    fee_tag.strong.decompose()
                    local_fees = tag_text(fee_tag).replace('* per semester average', '').replace('$', '').replace(',', '')
                    print('local fees 2021: ', local_fees)
            except (AttributeError, IndexError):
                print('2021 local fees not provided')

    # OUTCOMES
    try:
        tag_ = soup.find('div', {'id': 'panel-panel-group-2'}).find('div', class_='panel-body')
        if tag_:
            outcomes = tag_text(tag_)
            course_data['Career_Outcomes'] = outcomes
    except AttributeError:
        print('no outcomes provided')

    # PREREQUISITES
    try:
        pre_req_tags = soup.find('table', {'border': '0', 'cellpadding': '0', 'cellspacing': '0', 'class': 'table table-bordered table-condensed table-striped'}).find('tbody').find('tr').find_all('td')
        if pre_req_tags:
            pre_req_list = [tag_text(td) for td in pre_req_tags]
            if len(pre_req_list) > 2:
                course_data['Prerequisite_1'] = 'ATAR'
                course_data['Prerequisite_1_grade_1'] = pre_req_list[0]
                course_data['Prerequisite_2'] = 'OP (Overall Position)'
                course_data['Prerequisite_2_grade_2'] = pre_req_list[1]
                course_data['Prerequisite_3'] = 'IB (International Baccalaureate)'
                course_data['Prerequisite_3_grade_3'] = pre_req_list[2]
    except (AttributeError, IndexError):
        print('prerequisites not given')

    # we now attempt to fetch international fees
    int_url = pure_url.replace('https://bond.edu.au/', 'https://bond.edu.au/intl/')
    url_ = int_url
    browser_ = webdriver.Chrome(executable_path=exec_path, chrome_options=option)
    browser_.get(url_)
    time.sleep(0.5)
    html_ = browser_.page_source
    soup_ = bs4.BeautifulSoup(html_, 'lxml')
    # INT FEES 2020
    try:
        fee_tag = soup_.find('strong', text=re.compile('Total program fee:', re.IGNORECASE)) \
            .find_parent('p').find_next('ul').find('li')
        if fee_tag:
            fee_tag.strong.decompose()
            int_fees = tag_text(fee_tag).replace('* per semester average', '').replace('$', '').replace(',', '')
            course_data['Int_Fees'] = int_fees
            course_data['Currency_Time'] = 'Semesters'
    except AttributeError:
        try:
            fee_tag = soup_.find('strong', text=re.compile('Annual program fee:', re.IGNORECASE)) \
                .find_parent('p').find_next('ul').find('li')
            if fee_tag:
                fee_tag.strong.decompose()
                int_fees = tag_text(fee_tag).replace('* annually', '').replace('$', '').replace(',', '')
                course_data['Int_Fees'] = int_fees
                course_data['Currency_Time'] = 'Years'
        except AttributeError:
            try:
                fee_tag = soup_.find('strong', text=re.compile('Semester program fees:', re.IGNORECASE)) \
                    .find_parent('p').find_next('ul').find('li')
                if fee_tag:
                    fee_tag.strong.decompose()
                    int_fees = tag_text(fee_tag).replace('* per semester average', '').replace('$', '').replace(',', '')
                    course_data['Int_Fees'] = int_fees
                    course_data['Currency_Time'] = 'Semesters'
            except AttributeError:
                print('2020 int fees not provided')
    # INT FEES 2021
    try:
        fee_tag = soup_.find('strong', text=re.compile('Total program fee:', re.IGNORECASE)) \
            .find_parent('p').find_next('ul').find_all('li')[1]
        if fee_tag:
            fee_tag.strong.decompose()
            local_fees = tag_text(fee_tag).replace('* per semester average', '').replace('$', '').replace(',', '')
            print('local fees 2021: ', local_fees)
    except (AttributeError, IndexError):
        try:
            fee_tag = soup_.find('strong', text=re.compile('Annual program fee:', re.IGNORECASE)) \
                .find_parent('p').find_next('ul').find_all('li')[1]
            if fee_tag:
                fee_tag.strong.decompose()
                local_fees = tag_text(fee_tag).replace('* annually', '').replace('$', '').replace(',', '')
                print('local fees 2021: ', local_fees)
        except (AttributeError, IndexError):
            try:
                fee_tag = soup_.find('strong', text=re.compile('Semester program fees:', re.IGNORECASE)) \
                    .find_parent('p').find_next('ul').find_all('li')[1]
                if fee_tag:
                    fee_tag.strong.decompose()
                    local_fees = tag_text(fee_tag).replace('* per semester average', '').replace('$', '').replace(',',
                                                                                                                  '')
                    print('int fees 2021: ', local_fees)
            except (AttributeError, IndexError):
                print('2021 int fees not provided')

    course_data_all.append(copy.deepcopy(course_data))

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
