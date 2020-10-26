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


def tag_text(string_):
    return string_.get_text().__str__().strip()


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
course_links_file_path = course_links_file_path.__str__() + '/anu_postgrad_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'ANU_Postgrad_Data.csv'

remarks = "For domestic fees and details on Commonwealth Supported Place (CSP) see: \
 http://www.anu.edu.au/students/program-administration/costs-fees"

course_data = {'Level_Code': '', 'University': 'Australian National University', 'City': 'Canberra', 'Course': '',
               'Faculty': '',
               'Int_Fees': '', 'Local_Fees': '', 'Currency': 'AUD', 'Currency_Time': 'Years', 'Duration': '',
               'Duration_Time': '', 'Full_Time': '', 'Part_Time': '',
               'Prerequisite_1': 'Undergraduate GPA (Scale of 7.0)',
               'Prerequisite_1_grade_1': '',
               'Website': '', 'Course_Lang': 'English', 'Availability': 'A', 'Description': '', 'Career_Outcomes': '',
               'Country': 'Australia', 'Online': 'No', 'Offline': 'Yes', 'Distance': 'No', 'Face_to_Face': '',
               'Blended': 'No', 'Remarks': remarks}

level_key = TemplateData.level_key  # dictionary of course levels

faculty_key = TemplateData.faculty_key  # dictionary of course levels

currency_pattern = "(?:[\£\$\€\(RM)\]{1}[,\d]+.?\d*)"  # regex pattern for finding currency or cash amount strings

course_data_all = []

campuses = set()

# MAIN ROUTINE
for each_url in course_links_file:
    actual_cities = []

    browser.get(each_url)
    pure_url = each_url.strip()
    print('CURRENT LINK: ', pure_url)
    each_url = browser.page_source

    soup = bs4.BeautifulSoup(each_url, 'html.parser')
    time.sleep(0.1)

    all_text = soup.text.replace('\n', '').strip()

    # COURSE URL
    course_data['Website'] = pure_url

    # COURSE NAME
    h1_span = soup.find('span', class_='intro__degree-title__component')
    if h1_span:
        course = h1_span.get_text().__str__().strip()
        course_data['Course'] = course
    print(course_data['Course'])

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

    # DELIVERY MODE (ONLINE, OFFLINE, FACE TO FACE)
    i_tag = soup.find('i', class_='fa fa-truck degree-summary__code-truck-icon')
    if i_tag:
        span = i_tag.find_parent('span')
        if span:
            ul = span.find_next('ul')
            if ul:
                delivery = ul.find('li')
                if delivery:
                    delivery_mode = tag_text(delivery)
                    if 'in person' in delivery_mode.lower():
                        course_data['Face_to_Face'] = 'Yes'
                        course_data['Offline'] = 'Yes'
                        course_data['Online'] = 'No'
                    if 'online' in delivery_mode.lower() and 'in person' not in delivery_mode.lower():
                        course_data['Online'] = 'Yes'
                    if 'online' not in delivery_mode.lower():
                        course_data['Face_to_Face'] = 'Yes'

    print('FACE TO FACE: ', course_data['Face_to_Face'])
    print('ONLINE: ', course_data['Online'])
    print('OFFLINE: ', course_data['Offline'])

    # DESCRIPTION
    div1 = soup.find('div', id='introduction', class_='introduction')
    if div1:
        course_data['Description'] = div1.get_text().__str__().strip()
    print('DESCRIPTION: ', course_data['Description'])

    course_data['Availability'] = 'A'
    # AVAILABILITY
    if 'This program is available for domestic students only' in course_data['Description']:
        course_data['Availability'] = 'D'
    if 'Applications from international students for Semester 1, 2020 intake of this program are now closed' \
            in course_data['Description']:
        course_data['Availability'] = 'D'
    if ' This program is closed to International applicants' in course_data['Description']:
        course_data['Availability'] = 'D'
    if 'This program is no longer available for applications.' in course_data['Description']:
        course_data['Availability'] = 'N'

    # LEARNING OUTCOMES
    try:
        # there are two types. we find the first type (CAREER OPTIONS), else we find LEARNING OUTCOMES
        div1 = soup.find('div', class_='callout-box callout-box--reverse callout-box--career callout-box--right')
        if div1:
            ol = div1.find_next('ol')
            if ol:
                li_tags = ol.find_all('li')
                if li_tags:
                    learning_outcomes = []
                    for i in li_tags:
                        learning_outcomes.append(tag_text(i))
                    outcomes = ' '.join(learning_outcomes).strip()
                    course_data['Career_Outcomes'] = outcomes
        else:
            # there are two types. we find the first type (CAREER OPTIONS), else we find LEARNING OUTCOMES
            div_h2 = soup.find('div', class_='callout-box callout-box--reverse callout-box--career callout-box--right'). \
                find('div').find('h2', id='career-options')
            if div_h2:
                the_div = soup.find('div',
                                    class_='callout-box callout-box--reverse callout-box--career callout-box--right'). \
                    find('div')
                if the_div:
                    p_tags = the_div.find_all('p')
                    if p_tags:
                        p_array = []
                        for p in p_tags:
                            p_array.append(tag_text(p))
                        career_options = ' '.join(p_array).strip()
                        course_data['Career_Outcomes'] = career_options
    except AttributeError:
        course_data['Career_Outcomes'] = ''

    print('OUTCOMES: ', course_data['Career_Outcomes'])

    # ONLY INT_FEES
    try:
        div_dl = soup.find('div', id='indicative-fees__international').find('dl')
        if div_dl:
            dd = div_dl.find('dd')
            if dd:
                int_fees = tag_text(dd).replace('$', '')
                course_data['Int_Fees'] = int_fees
                print('', course_data['Int_Fees'])
    except AttributeError:
        course_data['Int_Fees'] = ''
        print('no fees for this course')
        pass

    # DURATION
    try:
        div_span = \
            soup.find('div', class_='degree-summary hide-mobile w-doublenarrow').find('div').find('ul').find(
                'li').find_all('span')[1]
        if div_span:
            duration_raw = tag_text(div_span)
            p_word = duration_raw
            if 'full-time' in duration_raw.lower() and 'part-time' not in duration_raw.lower():
                course_data['Full_Time'] = 'Yes'
            else:
                course_data['Full_Time'] = 'Yes'
            if 'part-time' in duration_raw.lower() or 'part' in duration_raw.lower() and 'full-time' not in duration_raw.lower():
                course_data['Part_Time'] = 'Yes'
            else:
                course_data['Part_Time'] = 'No'
            if 'full-time' in duration_raw.lower() and 'part-time' in duration_raw.lower():
                course_data['Blended'] = 'Yes'
            else:
                course_data['Blended'] = 'No'

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
    except IndexError:
        course_data['Full_Time'] = ''
        course_data['Part_Time'] = ''
        course_data['Duration'] = ''
        course_data['Duration_Time'] = ''
        print("this course doesn't have information pertaining to duration")

    course_data['Blended'] = 'No'
    if course_data['Online'] == 'Yes' and course_data['Offline'] == 'Yes':
        course_data['Blended'] = 'Yes'

    # PREREQUISITES 1
    div_ps = soup.find('div', id='admission-and-fees').find('div', class_='body__inner w-doublewide copy').find_all('p')
    if div_ps:
        try:
            for p in div_ps:
                gpa_raw = p.get_text().__str__().strip()
                if 'with a minimum gpa of' in gpa_raw.lower():
                    g = gpa_raw.lower()
                    if '4.' in g or '5.' in g or '6.' in g or '7.' \
                            and '4/' not in g and '6/' not in g and '7/' not in g:
                        gpa_temp_1 = int(list(filter(str.isdigit, gpa_raw))[0])
                        gpa_temp_2 = int(list(filter(str.isdigit, gpa_raw))[1])
                        gpa_temp = str(gpa_temp_1) + '.' + str(gpa_temp_2)
                        course_data['Prerequisite_1_grade_1'] = gpa_temp
                    elif '4/' in g or '5/' in g or '6/' in g or '7/' in g:
                        gpa_temp_1 = int(list(filter(str.isdigit, gpa_raw))[0])
                        course_data['Prerequisite_1_grade_1'] = gpa_temp_1
                    # break
        except IndexError:
            course_data['Prerequisite_1_grade_1'] = ''

    print('AVAILABILITY: ', course_data['Availability'])
    print('GPA: ', course_data['Prerequisite_1_grade_1'])

    course_data_all.append(copy.deepcopy(course_data))

print(*course_data_all, sep='\n')

# tabulate our data__
# course_dict_keys = set().union(*(d.keys() for d in course_data_all))
course_dict_keys = []
for i in course_data:
    course_dict_keys.append(i)

with open(csv_file, 'w', encoding='utf-8', newline='') as output_file:
    dict_writer = csv.DictWriter(output_file, course_dict_keys)
    dict_writer.writeheader()
    dict_writer.writerows(course_data_all)
