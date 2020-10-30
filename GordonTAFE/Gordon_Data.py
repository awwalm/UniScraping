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
                        'Blended': 'No', 'Remarks': ''}

# noinspection SpellCheckingInspection
possible_cities = {'east geelong campus': 'Melbourne (East Geelong Campus)',
                   'geelong city campus': 'Melbourne (Geelong City Campus)',
                   'werribee princes campus': 'Melbourne (Werribee Princes Campus)',
                   'hoppers crossing trades campus': 'Melbourne (Hoppers Crossing Trades Campus)',
                   'werribee': 'Melbourne (Werribee Campus)',
                   'off campus': '',
                   'werribee watton campus': 'Melbourne (Werribee Watton Campus)',
                   'ballarat': 'Ballarat',
                   '': ''}

other_cities = {}

campuses = set()

sample = ['']

# MAIN ROUTINE
for each_url in course_links_file:

    # noinspection SpellCheckingInspection
    course_data = {'Level_Code': '', 'University': 'Gordon Geelong Institute of TAFE', 'City': '', 'Course': '',
                   'Faculty': '',
                   'Int_Fees': '', 'Local_Fees': '', 'Currency': 'AUD', 'Currency_Time': 'Course', 'Duration': '',
                   'Duration_Time': '', 'Full_Time': 'Yes', 'Part_Time': 'No',
                   'Prerequisite_1': '', 'Prerequisite_1_grade_1': '',  # ATAR
                   'Prerequisite_2': '', 'Prerequisite_2_grade_2': '',  # IELTS
                   'Prerequisite_3': '', 'Prerequisite_3_grade_3': '',  # GPA
                   'Website': '', 'Course_Lang': 'English', 'Availability': 'A', 'Description': '',
                   'Career_Outcomes': '',
                   'Country': 'Australia', 'Online': 'No', 'Offline': 'Yes', 'Distance': 'No', 'Face_to_Face': 'Yes',
                   'Blended': 'No', 'Remarks': ''}

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
        actual_cities.add('')
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
        fee_data = soup.find('span', text=re.compile('full fee tuition', re.IGNORECASE))\
            .find_next('span').find_next('span').find_next('span').find_next('span')
        if fee_data:
            fee = tag_text(fee_data)
            course_data['Int_Fees'] = course_data['Local_Fees'] = fee.replace('AUD', '').replace(',', '').replace('$', '')
            print('fees so far: ', fee)
    except AttributeError:
        try:
            fee_data = soup.find('span', text=re.compile('^ Cost \(inc\. GST\):', re.IGNORECASE)).find_next('span')
            if fee_data:
                fee = tag_text(fee_data)
                course_data['Int_Fees'] = course_data['Local_Fees'] = fee.replace('AUD', '').replace(',', '').replace('$', '')
                print('fees so far: ', fee)
        except AttributeError:
            try:
                fee_data = soup.find('span', text=re.compile('Full Fee Cost', re.IGNORECASE)).find_next('span')
                if fee_data:
                    fee = tag_text(fee_data)
                    course_data['Int_Fees'] = course_data['Local_Fees'] = fee.replace('AUD', '').replace(',', '').replace('$', '')
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
