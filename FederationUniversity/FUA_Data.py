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
from selenium.common.exceptions import TimeoutException, JavascriptException
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
# option.add_argument("headless")
exec_path = Path(os.getcwd().replace('\\', '/'))
exec_path = exec_path.parent.parent.parent.__str__() + '/Libraries/Google/v86/chromedriver.exe'
browser = webdriver.Chrome(executable_path=exec_path, chrome_options=option)

# read the url from each file into a list
course_links_file_path = Path(os.getcwd().replace('\\', '/'))
course_links_file_path = course_links_file_path.__str__() + '/fua_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'FUA_All_Data.csv'

with open('LocalData/ATAR-FUA.html') as atar_file:    # ATAR local HTML
    soup_atar = bs4.BeautifulSoup(atar_file, 'html.parser')
with open('LocalData/2020-FedUni-TAFE-Indicative-Fees.html') as tafe_file:  # TAFE fees local HTML
    soup_tafe = bs4.BeautifulSoup(tafe_file, 'html.parser')
with open('LocalData/2020_HigherEd_International_Tuition_Fee_Schedule.html') as int_file:   # INTERNATIONAL fees (some)
    soup_int = bs4.BeautifulSoup(int_file, 'html.parser')
with open('LocalData/2020_HigherEd_Domestic_Tuition_Fee_Schedule.html', encoding='utf8') as dom_file:        # DOMESTIC fees (some)
    soup_dom = bs4.BeautifulSoup(dom_file, 'lxml')

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

possible_cities = {'Ballarat': 'Ballarat',
                   'Berwick': 'Melbourne',
                   'Brisbane': 'Brisbane',
                   'Gippsland': 'Gippsland',
                   'Wimmera': 'Wimmera'}

other_cities = {}

campuses = set()

sample = ['https://study.federation.edu.au/course/HLTSS00067%20-%20Infection%20Control%20Skill%20Set%20(Retail)']

# MAIN ROUTINE
for each_url in course_links_file:

    if 'online.jcu.edu.au' in each_url:
        continue

    course_data = {'Level_Code': '', 'University': 'Federation University of Australia', 'City': '', 'Course': '',
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
    time.sleep(0.5)
    delay = 1
    url__ = each_url
    pure_url = each_url.strip()
    print('CURRENT LINK: ', pure_url)
    each_url = None

    # =========================================================================
    # START CHECKING FOR DOMESTIC DETAILS

    try:
        browser.execute_script("StudentType('domestic');$('#search').focus();")

        time.sleep(0.5)
        each_url = browser.page_source
    except TimeoutException:
        pass

    if each_url is None:
        each_url = browser.page_source

    soup = bs4.BeautifulSoup(each_url, 'html.parser')

    all_text = soup.text.replace('\n', '').strip()

    # COURSE URL
    course_data['Website'] = pure_url

    # COURSE NAME
    title = soup.find('div', {'id': 'course-title-header'})
    if title:
        course_data['Course'] = tag_text(title)

    # TAFE PRICE FIXING
    qualification_code = None
    try:
        the_tag = soup.find('span', {'id': 'course-overview-atar-qualification', 'class': 'course-overview', 'feedback': 'Code'})
        if the_tag:
            code_raw = tag_text(the_tag)
            if 7 < len(code_raw) < 11:
                print('TAFE discovered')
                course_data['Availability'] = 'D'
                qualification_code = code_raw
    except AttributeError:
        pass
    try:
        if qualification_code is not None:
            tafe_fee_tag = soup_tafe.find('p', text=qualification_code).find_parent('td').find_parent('tr').find('td', class_='td100')
            if tafe_fee_tag:
                tafe_fee = tag_text(tafe_fee_tag).replace(',', '')
                print('TAFE fee found: ', tafe_fee)
                course_data['Local_Fees'] = tafe_fee
                course_data['Currency_Time'] = 'Course'
    except AttributeError:
        pass

    # DOMESTIC PRICE FIXING
    try:
        if len(course_data['Local_Fees']) < 1:
            degree = course_data['Course']
            dom_fee_tag = soup_dom.find('p', text=re.compile('^'+degree, re.IGNORECASE)).find_parent('td').find_parent('tr').find('td', class_='td54')
            if dom_fee_tag:
                dom_fee = tag_text(dom_fee_tag).replace('$', '').replace(',', '')
                print('domestic fees found: ', dom_fee)
                course_data['Local_Fees'] = dom_fee
    except AttributeError:
        pass

    # ATAR (if available)
    try:
        degree_split = course_data['Course'].lower().split()
        atar_table = soup_atar.find('table', {'id': 'table43581'}).find('tbody')
        if atar_table:
            tr_tags = atar_table.find_all('tr')
            if tr_tags:
                for tr in tr_tags:
                    td_tags = tr.find_all('td')
                    if td_tags:
                        atar_degree_string = tag_text(td_tags[0]).lower()
                        atar_degree_split = atar_degree_string.split()
                        atar_score = tag_text(td_tags[1])
                        for d in degree_split:
                            for a in atar_degree_split:
                                if d == a:
                                    course_data['Prerequisite_1'] = 'ATAR'
                                    course_data['Prerequisite_1_grade_1'] = atar_score
                                    break
    except (AttributeError, IndexError, TypeError) as e:
        print(e.stacktrace, e.__cause__)

    # DURATION
    try:
        duration_tag = soup.find('span', {'id': 'course-overview-length', 'class': 'course-overview'})
        if duration_tag:
            duration_text = tag_text(duration_tag)
            duration = DurationConverter.convert_duration(duration_text)
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

    # DESCRIPTION
    try:
        desc_div = soup.find('div', {'aria-labelledby': 'exItem2Header', 'data-parent': '#accordion-course-outline', 'id': re.compile('^course-outline')})
        desc = tag_text(desc_div)
        course_data['Description'] = desc
    except AttributeError:
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

    # CITIES
    location_tags = soup.find_all('div', {'class': 'l-s-col location'})
    locations = [tag_text(div) for div in location_tags]
    for loc in locations:
        if 'online' or 'on-line' in loc.lower():
            course_data['Online'] = 'Yes'
        for pc in possible_cities:
            if pc in loc:
                if possible_cities[pc] not in actual_cities:
                    actual_cities.append(possible_cities[pc])
    online_loc_tag = soup.find_all('div', {'class': 'l-s-col location', 'text': 'On-line Learning'})
    if online_loc_tag:
        course_data['Online'] = 'Yes'

    # PREREQUISITES
    try:
        year12_tag = soup.find('h3', text=re.compile('Entry requirements \(year 12\)', re.IGNORECASE))
        if year12_tag:
            course_data['Prerequisite_3'] = 'Year 12'
    except AttributeError:
        pass

    # REMARKS
    try:
        rem_tag = soup.find('div', {'id': 'course-entry_requirements-expand', 'data-parent': '#accordion-course-entry_requirements'})
        if rem_tag:
            remarks = tag_text(rem_tag)
            course_data['Remarks'] = remarks
    except AttributeError:
        pass
    try:
        rem2_tag = soup.find('div', {'id': 'course-how_to_apply-expand', 'data-parent': '#accordion-course-how_to_apply'})
        if rem2_tag:
            remarks2 = tag_text(rem2_tag)
            course_data['Remarks'] += '.\t' + remarks2.replace('\n\n', '')
    except AttributeError:
        pass

    # CAREER OUTCOMES
    try:
        out1_tag = soup.find('div', {'id': 'course-careers-expand', 'data-parent': '#accordion-course-careers'})
        if out1_tag:
            out1 = tag_text(out1_tag)
            course_data['Career_Outcomes'] = out1
    except AttributeError:
        pass
    try:
        out2_tag = soup.find('div', {'id': 'course-professional_recognition-expand', 'data-parent': '#accordion-course-professional_recognition'})
        if out2_tag:
            out2 = tag_text(out2_tag)
            course_data['Career_Outcomes'] += '.\t' + out2.replace('\n\n', '')
    except AttributeError:
        pass

    # ==============================================================================================
    # START CHECKING INTERNATIONAL DETAILS
    try:
        browser.execute_script("StudentType('international');$('#search').focus();")
        each_url_ = browser.page_source
        soup_ = bs4.BeautifulSoup(each_url_, 'html.parser')
        # AVAILABILITY
        try:
            int_avl = soup_.find('span', text=re.compile('^Sorry, this course is not available to international students', re.IGNORECASE))
            if int_avl:
                course_data['Availability'] = 'D'
        except AttributeError:
            print('cant determine if course is int or dom only')
        # IELTS
        try:
            ielts_tag = soup_.find('h3', text='English language requirement').find_next('p')
            if ielts_tag and 'IELTS' in tag_text(ielts_tag):
                ielts_raw = tag_text(ielts_tag)
                ielts_val = re.findall(r'[-+]?\d*\.\d+|\d+', ielts_raw)
                course_data['Prerequisite_2'] = 'IELTS'
                course_data['Prerequisite_2_grade_2'] = ielts_val[0]
        except AttributeError:
            pass
        # INT FEES
        try:
            fee_strong_tag = soup_.find('strong', text=re.compile('^\$.*\d*.AUD$'))
            if fee_strong_tag:
                int_fees = tag_text(fee_strong_tag).replace('$', '').replace(',', '').replace('AUD', '')
                course_data['Int_Fees'] = int_fees
        except AttributeError:
            pass
        # INT FEES, FURTHER FIXING
        try:
            degree = course_data['Course']
            if len(course_data['Int_Fees']) <= 3 or str(course_data['Int_Fees']) == '0.00':
                degree_split_ = degree.lower().split()
                int_fee_tag = None
                for w in degree_split_:
                    int_fee_tag_ = soup_int.find('p', text=re.compile('^.*'+w.strip()+'.*$', re.IGNORECASE))
                    if int_fee_tag_:
                        int_fee_tag = int_fee_tag_
                        break
                if int_fee_tag is not None:
                    the_real_int_fee_tag = int_fee_tag.find_parent('td').find_parent('tr').find('td', class_='td54')
                    if the_real_int_fee_tag:
                        the_int_fees = tag_text(the_real_int_fee_tag)
                        course_data['Int_Fees'] = the_int_fees.replace('$', '').replace(',', '')
                        print('missing int fees found: ', the_int_fees)
        except (AttributeError, IndexError, TypeError, sre_constants.error) as e:
            print(e.__str__())
    except TimeoutException as t:
        print(t.stacktrace, t.__cause__, t.msg, t.__context__)
    except JavascriptException as j:
        print(j.stacktrace, j.__cause__, j.msg, j.__context__)

    # duplicating entries with multiple cities for each city
    for i in actual_cities:
        course_data['City'] = possible_cities[i]
        print('repeated cities: ', possible_cities[i])
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

with open(csv_file, 'w', encoding='utf-8', newline='') as output_file:
    dict_writer = csv.DictWriter(output_file, course_dict_keys)
    dict_writer.writeheader()
    dict_writer.writerows(course_data_all)
