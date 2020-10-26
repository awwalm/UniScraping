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
exec_path = exec_path.parent.parent.parent.parent.__str__() + '/Libraries/Google/v86/chromedriver.exe'
browser = webdriver.Chrome(executable_path=exec_path, chrome_options=option)

# read the url from each file into a list
course_links_file_path = Path(os.getcwd().replace('\\', '/'))
course_links_file_path = course_links_file_path.__str__() + '/unisa_postgrad_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'UNISA_Postgrad_Data.csv'

level_key = TemplateData.level_key  # dictionary of course levels

faculty_key = TemplateData.faculty_key  # dictionary of course levels

currency_pattern = "(?:[\£\$\€\(RM)\]{1}[,\d]+.?\d*)"  # regex pattern for finding currency or cash amount strings

course_data_all = []

course_data_template = {'Level_Code': '', 'University': 'University of South Australia', 'City': '', 'Course': '',
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

possible_cities = {'City West': 'Adelaide',
                   'Mawson Lakes': 'Adelaide',
                   'City East': 'Adelaide',
                   'Magill': 'Adelaide',
                   'Wyhalla': 'Whyalla'}

other_cities = {}

campuses = set()

sample = ['https://study.unisa.edu.au/degrees/bachelor-of-interior-architecture/int',
          'https://online.unisa.edu.au/degrees/bachelor-of-business-financial-planning/int',
          'https://study.unisa.edu.au/courses/100722']

# MAIN ROUTINE
for each_url in course_links_file:

    course_data = {'Level_Code': '', 'University': 'University of South Australia', 'City': 'Adelaide', 'Course': '',
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
    div = soup.find('div', class_='title__-row')
    if div:
        title = tag_text(div)
        course_data['Course'] = title
    else:
        title_div = soup.find('div', class_='title-row')
        if title_div:
            course_data['Course'] = tag_text(title_div)

    # DECIDE THE LEVEL CODE
    for i in level_key:
        for j in level_key[i]:
            if j in course_data['Course']:
                course_data['Level_Code'] = i

    # CITY/CAMPUS
    try:
        span_a = soup.find('span', class_='text-uppercase caption', text=re.compile('Campus')).find_next('a').find('span')
        if span_a:
            city = tag_text(span_a)
            print('city/campus so far: ', city)
    except AttributeError:
        course_data['City'] = 'Adelaide'
        try:
            div1 = soup.find('div', class_='alert-block theme-background-green-light-alert theme-border-green-mid-alert theme-black theme-links-black')
            if div1:
                p = div1.find('p')
                if p:
                    text = tag_text(p)
                    course_data['Remarks'] = text
                    if 'Course Alert: This course is no longer available for enrolment' in text:
                        course_data['Availability'] = 'N'
                        print('course not available')
        except AttributeError:
            print('course not available')

    if course_data['Level_Code'] == '':
        course_data['Level_Code'] = 'PG'

    # DECIDE THE FACULTY
    for i in faculty_key:
        for j in faculty_key[i]:
            if j.lower() in course_data['Course'].lower():
                course_data['Faculty'] = i

    # INT FEES and LOCAL FEES
    try:
        svg_div = soup.find('svg', class_='Fees').find_parent('span').find_next('div').find('p')
        if svg_div:
            fee_data = tag_text(svg_div).replace('\n', '')
            extracted_fee = re.findall(currency_pattern, fee_data)[1] + re.findall(currency_pattern, fee_data)[2]
            cleaned_fee = extracted_fee.replace('$', '').replace(',', '')
            course_data['Int_Fees'] = cleaned_fee

            """This formula is based on: 
            https://i.unisa.edu.au/campus-central/Fees-and-Finance/Domestic-fee-paying-students/ """
            unit_tag = soup.find('td', {'data__-header': 'Units'})
            if unit_tag:
                unit_val = unit_tag.find('div', class_='table-content').contents[0]
                print('Unit: ', unit_val)
                local_fee = float(unit_val) * (int(cleaned_fee)/int(36))  # formula
                course_data['Local_Fees'] = local_fee
            else:
                the_div = soup.find('div', text=re.compile('Units'))
                if the_div:
                    print('passed 2nd find')
                    unit_val = the_div.find_next('div', class_='table-content')
                    unit_val = tag_text(unit_val)
                    print('Unit: ', unit_val)
                    local_fee = float(unit_val) * (int(cleaned_fee) / int(36))  # formula
                    course_data['Local_Fees'] = local_fee
        else:
            print('cant find fees')
    except AttributeError:
        print('no fees listed')

    # DURATION
    try:
        span_tags = soup.find_all('span', class_='text-uppercase caption')
        if span_tags:
            for span in span_tags:
                if 'Duration' in tag_text(span):
                    duration_text = tag_text(span.find_parent('p')).replace('\n', '')
                    p_word = duration_text
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

                    if 'full-time' in duration_text:
                        course_data['Full_Time'] = 'Yes'
                    if 'part-time' in duration_text or 'part time' in duration_text:
                        course_data['Part_Time'] = 'Yes'
    except AttributeError:
        print('no info on duration')

    # ATAR: PREREQUISITE 1
    try:
        table = soup.find('table', class_='medium-4').find('tbody')
        if table:
            tr_tags = table.find_all('tr')
            if tr_tags:
                for tr in tr_tags:
                    target_td = tr.find('td', text=re.compile('Australia'))
                    if target_td:
                        atar = target_td.find_next('td').get_text()
                        course_data['Prerequisite_1'] = 'ATAR'
                        course_data['Prerequisite_1_grade_1'] = atar
    except AttributeError:
        print('ATAR not found or not given')

    # IELTS: PREREQUISITE 2
    try:
        ielts_li_tag = soup.find('li', text=re.compile('^IELTS total', re.IGNORECASE))
        if ielts_li_tag:
            ielts = tag_text(ielts_li_tag)
            ielts_val = ielts.replace('IELTS total', '').replace('[', '').replace(']', '')
            course_data['Prerequisite_2'] = 'IELTS Total'
            course_data['Prerequisite_2_grade_2'] = ielts_val
    except AttributeError:
        print('IELTS Total not given')

    # DESCRIPTION
    try:
        h3 = soup.find("h3", text=re.compile("What you'll learn", re.IGNORECASE))
        if h3:
            li_tags = h3.find_next('div', {'class': 'unisa-u17-content'}).find('ul').find_all('li')
            if li_tags:
                content = [tag_text(i) for i in li_tags]
                course_data['Description'] = ' '.join(content)
    except AttributeError:
        print('description not found')

    # CAREER OUTCOMES
    try:
        car_tag = soup.find('h3', text=re.compile('Your career', re.IGNORECASE)).find_parent('div', class_='unisa-u17-content')
        if car_tag:
            outcomes = tag_text(car_tag)
            course_data['Career_Outcomes'] = outcomes
    except AttributeError:
        print('no career outcomes given or course not available')

    # DECIDE IF BLENDED OR NOT
    if course_data['Online'] == 'Yes' and course_data['Offline'] == 'Yes' and course_data['Distance'] == 'Yes' \
            and course_data['Part_Time'] == 'Yes' and course_data['Full_Time'] == 'Yes':
        course_data['Blended'] = 'Yes'

    # CHECK STUDY MODE
    try:
        mode_content = soup.find('span', text=re.compile('Mode')).find_parent('p')
        if mode_content:
            mode_data = tag_text(mode_content)
            if 'on-campus' in mode_data.lower():
                course_data['Offline'] = 'Yes'
            if 'online' in mode_data.lower():
                course_data['Online'] = 'Yes'
    except AttributeError:
        print('study mode not given or course not ava')

    # ADVANCED PART TIME/FULL TIME CHECK

    # "offered externally" in UNISA means DISTANCE LEARNING. Refer to
    # (https://i.unisa.edu.au/students/student-support-services/study-support/external-students/#:~:text=At%20UniSA%20you%20can%20study,bulk%20of%20your%20study%20online.)
    try:
        # noinspection RegExpDuplicateCharacterInClass
        online_img = soup.find('img', {'src': re.compile("[/siteassets/images/logos/online-logo-white.svg]"), 'alt': 'UniSA Online'})
        if online_img:
            course_data['Online'] = 'Yes'
            course_data['Offline'] = 'No'
            course_data['Face_to_Face'] = 'No'
    except AttributeError:
        pass
    try:
        div_tag = soup.find('span', text=re.compile('Offered Externally', re.IGNORECASE)).\
            find_parent('div', class_='description')
        if div_tag:
            print('found the div')
            data = tag_text(div_tag).replace('Offered Externally', '').replace('\n', '')
            if 'no' in data.lower():
                course_data['Distance'] = 'No'
            if 'yes' in data.lower():
                course_data['Distance'] = 'Yes'
            print('distanced: ', data)
    except AttributeError:
        pass

    print('COURSE: ', course_data['Course'])
    print('DESCRIPTION: ', course_data['Description'])
    print('LEVEL CODE: ', course_data['Level_Code'])
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
