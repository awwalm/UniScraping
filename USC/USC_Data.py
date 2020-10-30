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
exec_path = exec_path.parent.parent.parent.__str__() + '/Libraries/Google/v86/chromedriver.exe'
browser = webdriver.Chrome(executable_path=exec_path, chrome_options=option)

# read the url from each file into a list
course_links_file_path = Path(os.getcwd().replace('\\', '/'))
course_links_file_path = course_links_file_path.__str__() + '/usc_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'USC_All_Data.csv'

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

possible_cities = {'sunshine coast': 'Queensland (Sunshine Coast)',
                   'fraser coast': 'Queensland (Fraser Coast)',
                   'gympie': 'Queensland (Gympie)',
                   'caboolture': 'Queensland (Caboolture)',
                   'moreton bay': 'Queensland (Moreton Bay)',
                   'sippy downs': 'Queensland (Sippy Downs)',
                   'usc thompson institute': 'Queensland (USC Thompson Institute)'}

other_cities = {}

campuses = set()

sample = ['']

# MAIN ROUTINE
for each_url in course_links_file:

    course_data = {'Level_Code': '', 'University': 'University of Sunshine Coast', 'City': '', 'Course': '',
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
    time.sleep(1.5)
    url__ = each_url
    pure_url = each_url.strip()
    print('CURRENT LINK: ', pure_url)
    each_url = browser.page_source

    soup = bs4.BeautifulSoup(each_url, 'html.parser')

    all_text = soup.text.replace('\n', '').strip()

    # COURSE URL
    course_data['Website'] = pure_url

    # COURSE NAME
    title = soup.find('section', {'id': 'hero', 'class': 'hero-main'}).find('h1', {'class': 'mb-0'})
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

    # DURATION, PART-TIME/FULL-TIME
    try:
        dd_duration = soup.find('dt', text=re.compile('Duration')).find_next('dd')
        if dd_duration:
            duration_raw = tag_text(dd_duration)
            # print('duration so far: ', duration_raw)
            if 'part time' or 'part-time' in duration_raw.lower():
                course_data['Part_Time'] = 'Yes'
            if 'full time' or 'full-time' in duration_raw.lower():
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
    except AttributeError:
        print('duration not given')
    print('DURATION + DURATION TIME: ', course_data['Duration'], course_data['Duration_Time'])

    # CITY
    try:
        loc_tag = soup.find('dt', text=re.compile('^Study locations', re.IGNORECASE)).find_next('dd').find('ul', class_='list-unstyled').find_all('li')
        if loc_tag:
            loc_list = [tag_text(li) for li in loc_tag]
            for i in loc_list:
                for j in possible_cities:
                    if j.lower() in i.lower() or j.lower() == i.lower():
                        actual_cities.append(j.lower())
            print('locations so far: ', *loc_list, sep=' | ')
    except AttributeError:
        try:
            location_tag = soup.find('dt', text=re.compile('^Study locations', re.IGNORECASE)).find_next('dd').find('ul', {'class': 'list-unstyled'}).find_all('li')
            locations_list = [tag_text(li) for li in location_tag]
            for i in locations_list:
                for j in possible_cities:
                    if j.lower() in i.lower() or j.lower() == i.lower():
                        actual_cities.append(j.lower())
            print('locations so far: ', *locations_list, sep=' | ')
        except AttributeError:
            try:
                span = soup.find('span', text=re.compile('QTAC code', re.IGNORECASE)).find_parent('dt').find_next('dd').find('ul').find_all('li')
                if span:
                    loc_list = [tag_text(li) for li in span]
                    print('locations so far: ', *loc_list, sep=' | ')
                    for i in loc_list:
                        for j in possible_cities:
                            if j.lower() in i.lower() or j.lower() == i.lower():
                                actual_cities.append(j.lower())
            except AttributeError:
                print('no locations found')

    # STUDY MODE
    try:
        dd_tag = soup.find('dt', text=re.compile('Study mode', re.IGNORECASE)).find_next('dd')
        if dd_tag:
            study_mode_raw = tag_text(dd_tag)
            if 'online' in study_mode_raw.lower():
                course_data['Online'] = 'Yes'

            if 'blended' in study_mode_raw.lower():
                course_data['Online'] = 'Yes'
                course_data['Blended'] = 'Yes'
                course_data['Offline'] = 'Yes'
                course_data['Face_to_Face'] = 'Yes'

            if 'online' not in study_mode_raw.lower() and 'blended' not in study_mode_raw.lower():
                course_data['Online'] = 'No'

            if 'online' in study_mode_raw.lower() and 'on campus' not in study_mode_raw.lower() and 'blended' not in study_mode_raw.lower():
                course_data['Online'] = 'Yes'
                course_data['Blended'] = 'No'
                course_data['Offline'] = 'No'
                course_data['Face_to_Face'] = 'No'

            if 'on campus' in study_mode_raw.lower() and 'online' not in study_mode_raw.lower() and 'blended' not in study_mode_raw.lower():
                course_data['Online'] = 'No'
                course_data['Blended'] = 'No'
                course_data['Offline'] = 'Yes'
                course_data['Face_to_Face'] = 'Yes'

            print('study modes so far', study_mode_raw)
    except AttributeError:
        course_data['Online'] = 'No'
        course_data['Offline'] = 'Yes'
        course_data['Face_to_Face'] = 'Yes'

    # AVAILABILITY
    only_int_tag = soup.find('p', {'text': re.compile('This program is only available to international students.', re.IGNORECASE)})
    dom_tag = soup.find("li", {"class": "nav-item", "ng-click": "vm.setViewType('domestic')"})
    int_tag = soup.find("li", {"class": "nav-item", "ng-click": "vm.setViewType('international')"})
    if dom_tag and int_tag:
        course_data['Availability'] = 'A'
    if dom_tag and not int_tag:
        course_data['Availability'] = 'D'
    if not dom_tag and int_tag:
        course_data['Availability'] = 'I'
    if not dom_tag and not int_tag:
        course_data['Availability'] = 'D'
        print('cant spot both options')
    if only_int_tag:
        course_data['Availability'] = 'I'
        course_data['Remarks'] = tag_text(only_int_tag) + ' '

    # REMARKS
    try:
        div_rem = soup.find('div', {'compile': 'vm.currentStructure.requirements', 'highlights': 'fade'})
        if div_rem:
            remarks = tag_text(div_rem)
            course_data['Remarks'] += remarks
    except AttributeError:
        pass

    # DESCRIPTION
    # first pre-emptive version
    try:
        overview_p = soup.find('div', {'class': 'feature-card-lead'}).find('p')
        if overview_p:
            overview = tag_text(overview_p)
            course_data['Description'] = overview
    except AttributeError:
        pass
    # attempt 2
    div_p = soup.find('div', {'class': 'col-sm-7 col-md-8 order-2 order-sm-1'}).find('p')
    if div_p:
        description = tag_text(div_p)
        course_data['Description'] += description
        try:
            career_p = div_p.find_next('h5', text=re.compile('Career opportunities', re.IGNORECASE)).find_next('p')
            if career_p:
                outcomes = tag_text(career_p)
                course_data['Career_Outcomes'] = outcomes
        except AttributeError:
            try:
                car_p = soup.find('h6', {'text': re.compile('Career opportunities', re.IGNORECASE)}).find_next('p')
                if car_p:
                    outcomes = tag_text(car_p)
                    course_data['Career_Outcomes'] = outcomes
            except AttributeError:
                pass

    # OUTCOMES attempt 2
    try:
        if len(course_data['Career_Outcomes']) < 10:
            outcomes_li = soup.find('strong', text=re.compile('Career opportunities', re.IGNORECASE)).find_parent('p').find_next('ul')
            if outcomes_li:
                outcomes = tag_text(outcomes_li)
                course_data['Career_Outcomes'] += outcomes
    except AttributeError:
        pass
    try:
        if len(course_data['Career_Outcomes']) < 10:
            outcomes_p = soup.find('h5', text=re.compile('Career opportunities', re.IGNORECASE)).find_next('p')
            if outcomes_p:
                outcomes = tag_text(outcomes_p)
                course_data['Career_Outcomes'] += outcomes
    except AttributeError:
        pass
    try:
        if len(course_data['Career_Outcomes']) < 10:
            outcomes_p = soup.find('h6', text=re.compile('Career opportunities', re.IGNORECASE)).find_next('ul')
            if outcomes_p:
                outcomes = tag_text(outcomes_p)
                course_data['Career_Outcomes'] += outcomes
    except AttributeError:
        pass
    try:
        if 'please note' in course_data['Career_Outcomes'].lower() and len(course_data['Career_Outcomes']) < 15:
            outcomes__ = soup.find('h5', text=re.compile('Career opportunities', re.IGNORECASE)).find_next('ul')
            if outcomes__:
                outcomes = tag_text(outcomes__)
                course_data['Career_Outcomes'] += outcomes
    except AttributeError:
        pass
    if 'all first-year courses in this degree will be available online' in course_data['Career_Outcomes'].lower():
        course_data['Remarks'] = course_data['Career_Outcomes']
        course_data['Career_Outcomes'] = ''

    # COURSE FEES
    try:
        fee_tag = soup.find('dt', text=re.compile('^Annual tuition fee', re.IGNORECASE)).find_next('dd')
        if fee_tag:
            int_fees = tag_text(fee_tag).replace('A$', '').replace(',', '')
            course_data['Int_Fees'] = int_fees
            course_data['Currency_Time'] = 'Years'
    except AttributeError:
        print('fees not provided... possibly domestic only course.')

    # PREREQUISITE
    try:
        span = soup.find('span', text=re.compile('^ATAR'))
        if span:
            atar = tag_text(span).replace('ATAR - ', '')
            print('ATAR so far: ', atar)
            course_data['Prerequisite_1'] = 'ATAR'
            course_data['Prerequisite_1_grade_1'] = atar
    except AttributeError:
        print('ATAR not provided')

    # duplicating entries with multiple cities for each city
    for i in actual_cities:
        course_data['City'] = possible_cities[i.lower()]
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
