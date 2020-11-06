import copy
import csv
import json
import re
import sre_constants
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
course_links_file_path = course_links_file_path.__str__() + '/charles_sturt_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'Charles_Sturt_All_Data.csv'

# load information for international fees into this BS4 variable
int_fee_page = 'https://study.csu.edu.au/international/apply/fees-costs/student-fees'
browser.get(int_fee_page)
time.sleep(5)
int_fee_page = browser.page_source
soup_int_fees = bs4.BeautifulSoup(int_fee_page, 'html.parser')

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

possible_cities = {'Albury-Wodonga': 'Albury',
                   'Bathurst': 'Bathurst',
                   'Canberra': 'Canberra',
                   'CSU Study Center Brisbane': 'Brisbane',
                   'CSU Study Center Melbourne': 'Melbourne',
                   'CSU Study Center Sydney': 'Sydney',
                   'Dubbo': 'Dubbo',
                   'Orange': 'New South Wales (Orange)',
                   'Parramatta': 'Parramatta',
                   'Port Macquarie': 'New South Wales (Port Macquarie)',
                   'Wagga Wagga': 'Wagga Wagga',
                   'Online': ''}

other_cities = {}

sample = ['https://study.csu.edu.au/courses/business/master-professional-accounting-12']

# MAIN ROUTINE
for each_url in course_links_file:

    course_data = {'Level_Code': '', 'University': 'Charles Sturt University', 'City': '', 'Course': '',
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
    title_ = None
    title = soup.find('div', {'id': 'banner-heading'})
    if title:
        course_data['Course'] = tag_text(title)
        title_ = tag_text(title)

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

    # DESCRIPTION
    try:
        desc_tg = soup.find('p', {'class': 'intro-blurb'}).find_parent('div', {'class': 'col s12 m12 l10'})
        if desc_tg:
            desc1 = tag_text(desc_tg)
            course_data['Description'] = desc1 + '\t'
    except AttributeError:
        pass
    try:
        desc2_tag = soup.find('div', {'id': 'courseHighlights'})
        if desc2_tag:
            desc2 = tag_text(desc2_tag)
            course_data['Description'] += course_data['Description'].replace('\n', ' ') + desc2 + '\t'
    except AttributeError:
        pass

    # REMARKS
    try:
        rem_tag = soup.find('div', class_=re.compile('^.*isUnderGrad.*$'))
        if rem_tag:
            course_data['Remarks'] = tag_text(rem_tag)
        else:
            rem_tag = soup.find('div', class_=re.compile('^.*isHonours.*$'))
            if rem_tag:
                course_data['Remarks'] = tag_text(rem_tag)
            else:
                rem_tag = soup.find('div', class_=re.compile('^.*isPostGrad.*$'))
                if rem_tag:
                    course_data['Remarks'] = tag_text(rem_tag)
                else:
                    rem_tag = soup.find('div', class_=re.compile('^.*isHDR.*$'))
                    if rem_tag:
                        course_data['Remarks'] = tag_text(rem_tag)
    except (AttributeError, sre_constants.error):
        pass

    # OUTCOMES
    try:
        out_tag = soup.find('div', {'id': 'careerOppsText'})
        if out_tag:
            course_data['Career_Outcomes'] = tag_text(out_tag)
    except AttributeError:
        pass

    # AVAILABILITY
    try:
        int_av_tag = soup.find('img', src=re.compile('^.*https://cdn.csu.edu.au/__data/assets/image/0008/2764808/icon_international.png.*$', re.IGNORECASE))
        if int_av_tag:
            course_data['Availability'] = 'A'
        else:
            course_data['Availability'] = 'D'
    except AttributeError:
        pass

    # DURATION
    try:
        duration_tag = soup.find('p', text=re.compile('^.*Full-time: [\d].*.years|months|weeks|semesters.*.{0,40}$', re.IGNORECASE))
        if duration_tag:
            tagged_duration = tag_text(duration_tag)
            print('duration so far: ', tag_text(duration_tag))
            course_data = DurationConverter.convert_duration_cleanly(tagged_text=tagged_duration, course_dict=course_data)
            course_data['Full_Time'] = 'Yes' if 'full time' in tagged_duration.lower() or 'full-time' in tagged_duration.lower() else ''
            course_data['Part_Time'] = 'Yes' if 'part time' in tagged_duration.lower() or 'part-time' in tagged_duration.lower() else ''
        else:
            duration_tag = soup.find('p', text=re.compile('^.*Full-time [\d].*.years|months|weeks|semesters.*.{0,40}$', re.IGNORECASE))
            if duration_tag:
                tagged_duration = tag_text(duration_tag)
                print('duration so far: ', tag_text(duration_tag))
                course_data = DurationConverter.convert_duration_cleanly(tagged_text=tagged_duration, course_dict=course_data)
                course_data['Full_Time'] = 'Yes' if 'full time' in tagged_duration.lower() or 'full-time' in tagged_duration.lower() else ''
                course_data['Part_Time'] = 'Yes' if 'part time' in tagged_duration.lower() or 'part-time' in tagged_duration.lower() else ''
            else:
                duration_tag = soup.find('p', text=re.compile('^.*Part-time [\d].*.years|months|weeks|semesters.*.{0,40}$', re.IGNORECASE))
                if duration_tag:
                    tagged_duration = tag_text(duration_tag)
                    print('duration so far: ', tag_text(duration_tag))
                    course_data = DurationConverter.convert_duration_cleanly(tagged_text=tagged_duration, course_dict=course_data)
                    course_data['Full_Time'] = 'Yes' if 'full time' in tagged_duration.lower() or 'full-time' in tagged_duration.lower() else ''
                    course_data['Part_Time'] = 'Yes' if 'part time' in tagged_duration.lower() or 'part-time' in tagged_duration.lower() else ''
                else:
                    pattern_c = course_data['Course'].replace('(', '\(').replace(')', '\)')
                    duration_tag = soup.find('h5', text=re.compile(pattern_c, re.IGNORECASE)).find_next('p')
                    if duration_tag:
                        tagged_duration = tag_text(duration_tag)
                        print('duration so far: ', tag_text(duration_tag))
                        course_data = DurationConverter.convert_duration_cleanly(tagged_text=tagged_duration, course_dict=course_data)
                        course_data['Full_Time'] = 'Yes' if 'full time' in tagged_duration.lower() or 'full-time' in tagged_duration.lower() else ''
                        course_data['Part_Time'] = 'Yes' if 'part time' in tagged_duration.lower() or 'part-time' in tagged_duration.lower() else ''
                    else:
                        print('cant find duration')
    except (AttributeError, TypeError, sre_constants.error):
        print('trouble extracting duration')

    # ATAR
    try:
        colon = ':'
        atar_tag = soup.find('li', text=re.compile('^.*minimum selection rank required for consideration:.{0,2}.[\d].*.{0,60}$', re.IGNORECASE))
        if atar_tag:
            atar_val = tag_text(atar_tag)
            head, sep, tail = atar_val.partition(colon)
            course_data['Prerequisite_1'] = 'ATAR'
            course_data['Prerequisite_1_grade_1'] = tail
        else:
            print('atar not available')
    except (TypeError, AttributeError):
        print('error with atar code')

    # INT FEES, CITY, ONLINE/OFFLINE TEST 1
    has_online, has_offline = False, False
    pattern_c = course_data['Course'].replace('(', '\(').replace(')', '\)')
    try:
        int_tbody = soup_int_fees.find('table', {'summary': 'International Onshore Student Tuition Fees'}) \
            .find('tbody')
        if int_tbody:
            int_fee_tag = int_tbody.find('td', text=re.compile(pattern_c, re.IGNORECASE)) \
                .find_next('td').find_next('td').find_next('td')
            #   city           # fee per pts.   # annual fee
            if int_fee_tag:
                int_fee = tag_text(int_fee_tag).replace('$', '').replace(',', '')
                print('int fee: ', int_fee)
                course_data['Int_Fees'] = int_fee
                course_data['Offline'] = 'Yes'
                course_data['Face_to_Face'] = 'Yes'

            # CITY
            int_tbody_city = soup_int_fees.find('table', {'summary': 'International Onshore Student Tuition Fees'}) \
                .find('tbody')
            if int_tbody_city:
                city_tag = int_tbody_city.find('td', text=re.compile(pattern_c, re.IGNORECASE)) \
                    .find_next('td')
                if city_tag:
                    city_string = tag_text(city_tag).lower()
                    for i in possible_cities:
                        if i.lower() in city_string and i not in actual_cities:
                            actual_cities.add(i)
    except AttributeError:
        try:
            int_tbody = soup_int_fees.find('table', {'summary': 'International Online Student Tuition Fees'}) \
                .find('tbody')
            if int_tbody:
                int_fee_tag = int_tbody.find('td', text=re.compile(pattern_c, re.IGNORECASE)) \
                    .find_next('td').find_next('td')
                #   fee per points  # annual fee
                if int_fee_tag:
                    int_fee = tag_text(int_fee_tag).replace('$', '').replace(',', '')
                    print('int fee (online): ', int_fee)
                    course_data['Int_Fees'] = int_fee
                    course_data['Online'] = 'Yes'
                    actual_cities.add('Online')

        except AttributeError:
            print('cant find int fees')
    try:
        int_tbody = soup_int_fees.find('table', {'summary': 'International Onshore Student Tuition Fees'}) \
            .find('tbody')
        if int_tbody:
            int_fee_tag = int_tbody.find('td', text=re.compile(pattern_c, re.IGNORECASE)) \
                .find_next('td').find_next('td').find_next('td')
            #   city           # fee per pts.   # annual fee
            if int_fee_tag:
                has_offline = True
    except AttributeError:
        pass
    try:
        int_tbody = soup_int_fees.find('table', {'summary': 'International Online Student Tuition Fees'}) \
            .find('tbody')
        if int_tbody:
            int_fee_tag = int_tbody.find('td', text=re.compile(pattern_c, re.IGNORECASE)) \
                .find_next('td').find_next('td')
            #   fee per points  # annual fee
            if int_fee_tag:
                actual_cities.add('Online')
                has_online = True
    except AttributeError:
        pass

    course_data['Offline'] = 'Yes' if has_offline else 'No'
    course_data['Face_to_Face'] = 'Yes' if has_offline else 'No'
    course_data['Online'] = 'Yes' if has_online else 'No'
    course_data['Offline'] = 'No' if len(course_data['City']) < 3 else course_data['Offline']

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
    # print('IB: ', course_data['Prerequisite_3_grade_3'])
    print('IELTS: ', course_data['Prerequisite_2_grade_2'])
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

with open(csv_file, 'w', encoding='utf8', newline='') as output_file:
    dict_writer = csv.DictWriter(output_file, course_dict_keys)
    dict_writer.writeheader()
    dict_writer.writerows(course_data_all)
