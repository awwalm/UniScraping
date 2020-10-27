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
course_links_file_path = course_links_file_path.__str__() + '/scu_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'SCU_All_Data.csv'

level_key = TemplateData.level_key  # dictionary of course levels

faculty_key = TemplateData.faculty_key  # dictionary of course levels

currency_pattern = "(?:[\£\$\€\(RM)\]{1}[,\d]+.?\d*)"  # regex pattern for finding currency or cash amount strings

course_data_all = []

city_set = set()

course_data_template = {'Level_Code': '', 'University': 'Southern Cross University', 'City': '', 'Course': '',
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

sample = ['https://study.unisa.edu.au/degrees/bachelor-of-interior-architecture/int',
          'https://online.unisa.edu.au/degrees/bachelor-of-business-financial-planning/int',
          'https://study.unisa.edu.au/courses/100722']

# MAIN ROUTINE
for each_url in course_links_file:

    course_data = {'Level_Code': '', 'University': 'University of South Australia', 'City': '', 'Course': '',
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
    h1 = soup.find('h1', {'class': 'pageTitleFixSource'})
    if h1:
        course_data['Course'] = tag_text(h1)

    # CITY
    try:
        div = soup.find('div', {'class': 'table-grid table-col-3 table-responsive no-overflow'})
        if div:
            dom_id = div.find('a', text=re.compile('Domestic snapshot', re.IGNORECASE))
            if dom_id:
                dom_table = div.find_all('table', {'class': 'table'})[0]
                if dom_table:
                    dom_tbody = dom_table.find('tbody')
                    if dom_tbody:
                        tr_tags = dom_tbody.find_all('tr')
                        if tr_tags:
                            for tr in tr_tags:
                                td_tags = tr.find_all('td')
                                if td_tags:
                                    data_list = [tag_text(i) for i in td_tags]
                                    for i in data_list:
                                        for j in possible_cities:
                                            if i.lower() == j.lower() or j.lower() in i.lower():
                                                actual_cities.append(j.lower())
                                                print('city spotted: ', possible_cities[j])
                                            if 'online' in i.lower():
                                                course_data['Online'] = 'Yes'
            else:
                course_data['Availability'] = 'I'
    except (AttributeError, IndexError):
        div = soup.find('div', {'class': 'table-grid table-col-3 table-responsive no-overflow'})
        if div:
            int_id = div.find('a', text=re.compile('International snapshot', re.IGNORECASE))
            if int_id:
                int_table = div.find_all('table', {'class': 'table'})[1]
                if int_table:
                    int_tbody = int_table.find('tbody')
                    if int_tbody:
                        tr_tags = int_tbody.find_all('tr')
                        if tr_tags:
                            for tr in tr_tags:
                                td_tags = tr.find_all('td')
                                if td_tags:
                                    data_list = [tag_text(i) for i in td_tags]
                                    for i in data_list:
                                        for j in possible_cities:
                                            if i.lower() == j.lower() or j.lower() in i.lower():
                                                actual_cities.append(j.lower())
                                                print('city spotted: ', possible_cities[j])
                                            if 'online' in i.lower():
                                                course_data['Online'] = 'Yes'
            else:
                course_data['Availability'] = 'D'

    # AVAILABILITY
    h3 = soup.find('h3', text=re.compile('This course is available to:', re.IGNORECASE))
    if h3:
        main_div = h3.find_parent('div').find_parent('div')
        if main_div:
            all_divs = main_div.find_all('div')
            if all_divs:
                div_text_list = [tag_text(d) for d in all_divs]
                div_text = ' '.join(div_text_list)
                int_student_in_aus = 'international students studying in australia'
                int_student_out_aus = 'international students studying online or outside australia'
                dom_students = 'australian/domestic students'

                if dom_students in div_text.lower() and \
                        int_student_in_aus not in div_text.lower() and \
                        int_student_out_aus not in div_text.lower():
                    course_data['Availability'] = 'D'

                if dom_students not in div_text.lower() and \
                        int_student_in_aus in div_text.lower() or \
                        int_student_out_aus in div_text.lower():
                    course_data['Availability'] = 'I'

                if dom_students in div_text.lower() and \
                        int_student_out_aus in div_text.lower():
                    course_data['Availability'] = 'A'

                if dom_students in div_text.lower() and \
                        int_student_in_aus in div_text.lower():
                    course_data['Availability'] = 'A'

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
    print('FACULTY: ', course_data['Faculty'])

    # COURSE DESCRIPTION
    h2_div = soup.find('h2', text=re.compile('Course summary', re.IGNORECASE)).find_next('div')
    if h2_div:
        description = tag_text(h2_div)
        course_data['Description'] = description

    # OUTCOMES
    try:
        # noinspection RegExpDuplicateCharacterInClass,SpellCheckingInspection
        p_table = soup.find('div', {'id': 'collapseCrsLO', 'aria-labelledby': 'headingCrsLO'})\
            .find('div', class_='card-body').find('table', class_='table').find('tbody')
        if p_table:
            outcomes = tag_text(p_table)
            course_data['Career_Outcomes'] = outcomes
    except AttributeError:
        print('no outcomes given')

    # REMARKS
    try:
        info_divs = soup.find_all('div', {'class': 'message-box info'})
        if info_divs:
            remarks_list = [tag_text(div) for div in info_divs]
            remarks = '  '.join(remarks_list)
            course_data['Remarks'] = remarks
    except AttributeError:
        print('no remarks')

    # INT FEES
    try:
        table = soup.find('strong', text=re.compile('Annual Fees'))\
            .find_parent('th')\
            .find_parent('tr')\
            .find_parent('thead')\
            .find_parent('table')
        if table:
            fee_tag = table.find('tbody').find('tr').find('td', title='Sessions available for commencing study').find_next('td')
            if fee_tag:
                fee = tag_text(fee_tag).split()[0].replace('$', '')
                course_data['Int_Fees'] = fee
                course_data['Availability'] = 'A'
            else:
                fee_tag = table.find('tbody').find('tr')\
                    .find('td', title='Study Periods available for commencing study')\
                    .find_next('td')
                if fee_tag:
                    fee = tag_text(fee_tag).split()[0].replace('$', '')
                    course_data['Int_Fees'] = fee
                    course_data['Availability'] = 'A'
    except AttributeError:
        try:
            table = soup.find('strong', text=re.compile('Annual Fees')) \
                .find_parent('th') \
                .find_parent('tr') \
                .find_parent('thead') \
                .find_parent('table')
            fee_tag = table.find('tbody').find('tr') \
                .find('td') \
                .find_next('td').find_next('td')
            if fee_tag:
                fee = tag_text(fee_tag).split()[0].replace('$', '')
                course_data['Int_Fees'] = fee
                course_data['Availability'] = 'A'
        except AttributeError:
            print('no fees')

    # DURATION
    td_target = soup.find('td', text=re.compile('Duration')).find_next('td')
    if td_target:
        duration_raw = tag_text(td_target).replace('\n', '')
        if 'full-time' or 'full time' in duration_raw.lower():
            course_data['Full_Time'] = 'Yes'
        if 'part-time' or 'part time' in duration_raw.lower():
            course_data['Part_Time'] = 'Yes'
        head, sep, tail = duration_raw.partition(';')
        duration_data = head
        p_word = duration_data
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
            try:
                value_conv = DurationConverter.convert_duration(p_word)
                duration_1 = int(
                    ''.join(filter(str.isdigit, str(value_conv)))[0])
                duration_2 = int(
                    ''.join(filter(str.isdigit, str(value_conv)))[1])
                duration = str(duration_1) + str(duration_2)
                duration_time = 'Months'
                if str(duration) == '1' or str(duration) == '1.00' or str(
                        duration) == '1.0':
                    duration_time = 'Month'
                course_data['Duration'] = duration
                course_data['Duration_Time'] = duration_time
                print('DURATION + DURATION TIME: ', duration, duration_time)
            except IndexError:
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
        # print('full time duration so far: ', duration_data)

    # PREREQUISITE 2: IELTS
    try:
        if course_data['Availability'] == 'A':
            td_ielts = soup.find('td', text=re.compile('English language IELTS', re.IGNORECASE))\
                .find_next('td')\
                .find('table')\
                .find('tbody')\
                .find('tr')\
                .find('td', text=re.compile('Overall'))\
                .find_next('td')
            if td_ielts:
                ielts = tag_text(td_ielts)
                course_data['Prerequisite_2'] = 'IELTS'
                course_data['Prerequisite_2_grade_2'] = ielts
    except AttributeError:
        print('No IELTS score')

    # duplicating entries with multiple cities for each city
    for i in actual_cities:
        course_data['City'] = possible_cities[i.lower()]
        print('repeated cities: ', course_data['City'])

        if len(course_data['City']) < 2:
            course_data['Face_to_Face'] = 'No'
            course_data['Offline'] = 'No'

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
    print('IELTS: ', course_data['Prerequisite_2_grade_2'])
    print('GPA: ', course_data['Prerequisite_3_grade_3'])
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
