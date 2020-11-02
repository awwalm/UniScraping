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
exec_path = exec_path.parent.parent.parent.__str__() + '/Libraries/Google/v86/chromedriver.exe'
browser = webdriver.Chrome(executable_path=exec_path, chrome_options=option)

# read the url from each file into a list
course_links_file_path = Path(os.getcwd().replace('\\', '/'))
course_links_file_path = course_links_file_path.__str__() + '/jcu_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'JCU_All_Data.csv'

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
                        'Blended': 'No', 'Remarks': ''}

possible_cities = {'Townsville': 'Townsville',
                   'Cairns': 'Cairns',
                   'Mackay': 'Mackay',
                   'Mount Isa': 'Mount Isa',
                   'Singapore': 'Geylang'}

other_cities = {}

campuses = set()

sample = ['']

# MAIN ROUTINE
for each_url in course_links_file:

    if 'online.jcu.edu.au' in each_url:
        continue

    course_data = {'Level_Code': '', 'University': 'James Cook University', 'City': '', 'Course': '',
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
    time.sleep(0.25)
    url__ = each_url
    pure_url = each_url.strip()
    print('CURRENT LINK: ', pure_url)
    each_url = browser.page_source

    soup = bs4.BeautifulSoup(each_url, 'html.parser')

    all_text = soup.text.replace('\n', '').strip()

    # COURSE URL
    course_data['Website'] = pure_url

    # COURSE NAME
    title = soup.find('h1', {'class': 'course-banner__title'})
    if title:
        course_data['Course'] = tag_text(title)

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

    # DURATION
    try:
        duration_tag = soup.find('h4', text=re.compile('Duration', re.IGNORECASE))\
            .find_parent('div', {'class': 'course-fast-facts__tile__header'})\
            .find_next_sibling('div', {'class': 'course-fast-facts__tile__body'})\
            .find('div', {'course-fast-facts__tile__body-top'})
        if duration_tag:
            duration_raw = tag_text(duration_tag)
            if 'part-time' in duration_raw.lower() or 'part time' in duration_raw.lower():
                course_data['Part_Time'] = 'Yes'
            if 'full time' in duration_raw.lower() or 'full-time' in duration_raw.lower():
                course_data['Full_Time'] = 'Yes'
            duration = DurationConverter.convert_duration(duration_raw)
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
        print('some error occurred while trying to decode duration.')
    print('DURATION + DURATION TIME: ', course_data['Duration'], course_data['Duration_Time'])

    # COURSE DESCRIPTION
    try:
        desc_tag = soup.find('div', {'id': 'accordion_what-to-expect'}).find('div', {'id': 'accordion-1-panel'})
        if desc_tag:
            desc = tag_text(desc_tag).replace('\n\n', '.\n')
            course_data['Description'] = desc
    except AttributeError:
        pass

    # ATAR (thank goodness it's simple this time!)
    try:
        atar_tag = soup.find('p', {'class': 'course-fast-facts__tile__body-top__rank'}).find('strong')
        if atar_tag:
            atar = tag_text(atar_tag).replace('ATAR', '')
            course_data['Prerequisite_1'] = 'ATAR'
            course_data['Prerequisite_1_grade_1'] = atar
    except AttributeError:
        print('could not find ATAR')

    # CAREER OUTCOMES
    try:
        out_tag = soup.find('div', {'id': 'accordion_career'}).find('div')
        if out_tag:
            outcomes = tag_text(out_tag)
            course_data['Career_Outcomes'] = outcomes
    except AttributeError:
        pass

    # CITIES
    try:
        location_tags = soup.find('ul', {'class': 'course-fast-facts__location-list'}).find_all('li')
        if location_tags:
            for li in location_tags:
                location = tag_text(li)
                if 'online' in location.lower():
                    course_data['Online'] = 'Yes'
                    continue
                actual_cities.append(location)
    except AttributeError:
        print('problem with scraping locations')
        course_data['Offline'] = 'No'
        course_data['Face_to_Face'] = 'No'

    # REMARKS
    try:
        rem_req_tag = soup.find('div', {'class': 'course-fast-facts__tile fast-facts-entry-requirements'})\
            .find('div', {'class': 'course-fast-facts__tile__body'})\
            .find('div', {'class': 'course-fast-facts__tile__body-top'}).find_all('p')
        if rem_req_tag:
            req_list = [tag_text(p) for p in rem_req_tag]
            rem_req_words = '  '.join(req_list)
            course_data['Remarks'] = 'Requires ' + rem_req_words + '.\t'
    except AttributeError:
        pass
    try:
        rem0_content = soup.find('h4', text=re.compile('Entry Requirements', re.IGNORECASE)) \
            .find_next('div') \
            .find_next('div', class_='course-fast-facts__tile__info')
        if rem0_content:
            rem0 = rem0_content['data-tooltip-text']
            course_data['Remarks'] += rem0 + '.\t'
    except AttributeError:
        pass
    try:
        rem1_tag = soup.find('div', {'class': 'course-fast-facts__tile__body-bottom'})
        if rem1_tag:
            rem1 = tag_text(rem1_tag)
            course_data['Remarks'] += rem1 + '.\t'
    except AttributeError:
        pass
    try:
        rem2_tag = soup.find('button', {'id': 'accordion-6-btn', 'target': '#accordion-6-panel'}).find_next('div').find(
            'div')
        if rem2_tag:
            rem2 = tag_text(rem2_tag)
            course_data['Remarks'] += rem2 + '.\t'
    except AttributeError:
        pass

    # LOCAL FEES
    try:
        local_fee_tag = soup.find('div', {'class': 'course-fast-facts__tile__body-top__lrg'}).find('p')
        if local_fee_tag:
            local_fees = tag_text(local_fee_tag).replace('$', '').replace(',', '')
            course_data['Local_Fees'] = local_fees
    except AttributeError:
        print('cannot find fees')
        # future alternative routine: convert the PDF course pricing to HTML and scrape the hell out of it.

    # INTERNATIONAL FEES
    # we now attempt to fetch international fees by re-modifying the url
    int_url = pure_url + '?international'
    url_ = int_url
    browser_ = webdriver.Chrome(executable_path=exec_path, chrome_options=option)
    browser_.get(url_)
    time.sleep(0.25)
    html_ = browser_.page_source
    soup_ = bs4.BeautifulSoup(html_, 'lxml')
    try:
        int_fee_tag = soup_.find('div', {'class': 'course-fast-facts__tile__body-top__lrg'}).find('p')
        if int_fee_tag:
            int_fees = tag_text(int_fee_tag).replace('$', '').replace(',', '')
            course_data['Int_Fees'] = int_fees
    except AttributeError:
        print('cannot find international fees')

    # duplicating entries with multiple cities for each city
    for i in actual_cities:
        course_data['City'] = possible_cities[i]
        print('repeated cities: ', course_data['City'])
        if 'singapore' in i.lower():
            course_data['Country'] = 'Singapore'
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
