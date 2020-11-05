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
course_links_file_path = course_links_file_path.__str__() + '/torrens_links_file'
course_links_file = open(course_links_file_path, 'r')

# the csv file we'll be saving the courses to
csv_file_path = Path(os.getcwd().replace('\\', '/'))
csv_file = 'TorrensUA_All_Data.csv'

with open('LocalData/2020-DomesticFees.html', encoding='utf8') as dom_file:  # Domestic Fees local HTML
    soup_dom_fees = bs4.BeautifulSoup(dom_file, 'html.parser')
with open('LocalData/2020-InternationalFees.html', encoding='utf8') as int_file:  # International Fees local HTML
    soup_int_fees = bs4.BeautifulSoup(int_file, 'html.parser')

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

possible_cities = {'Adelaide': 'Adelaide',
                   'Sydney': 'Sydney',
                   'Brisbane': 'Brisbane',
                   'Melbourne': 'Melbourne',
                   'Perth': 'Perth',
                   'Flight Center Office': 'Adelaide'}

other_cities = {}

sample = ['https://www.torrens.edu.au/courses/business/master-of-business-administration-2']

# MAIN ROUTINE
for each_url in course_links_file:

    if 'www.think.edu.au' in each_url:
        continue

    course_data = {'Level_Code': '', 'University': 'Torrens University Australia', 'City': '', 'Course': '',
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
    title = soup.find('h1', {'class': 'font-bold mt-4 main-heading'})
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

    # CHECK LOCAL FILES FOR FEES
    comma, bracket_o, ampersand = ',', ' (', ' & '
    try:
        title_pattern = course_data['Course'] if title_ is None else title_
        local_fee = soup_dom_fees.find('p', text=re.compile('^.*'+title_pattern+'.*$'))\
            .find_parent('td')\
            .find_parent('tr').find('td', class_='tr3 td2')
        if local_fee:
            print('found local fee via HTML file: ', tag_text(local_fee))
            course_data['Local_Fees'] = tag_text(local_fee).replace('$', '').replace(',', '')
    except AttributeError:
        try:
            local_fee = soup_dom_fees.find('p', text=title_) \
                .find_parent('td') \
                .find_parent('tr').find('td', class_='tr3 td2')
            if local_fee:
                print('found local fee via HTML file: ', tag_text(local_fee))
                course_data['Local_Fees'] = tag_text(local_fee).replace('$', '').replace(',', '')
        except AttributeError:
            try:
                head, sep, tail = title_.partition(comma)
                local_fee = soup_dom_fees.find('p', text=head) \
                    .find_parent('td') \
                    .find_parent('tr').find('td', class_='tr3 td2')
                if local_fee:
                    print('found local fee via HTML file: ', tag_text(local_fee))
                    course_data['Local_Fees'] = tag_text(local_fee).replace('$', '').replace(',', '')
            except AttributeError:
                try:
                    head, sep, tail = title_.partition(bracket_o)
                    local_fee = soup_dom_fees.find('p', text=head) \
                        .find_parent('td') \
                        .find_parent('tr').find('td', class_='tr3 td2')
                    if local_fee:
                        print('found local fee via HTML file: ', tag_text(local_fee))
                        course_data['Local_Fees'] = tag_text(local_fee).replace('$', '').replace(',', '')
                except AttributeError:
                    try:
                        head, sep, tail = title_.partition(ampersand)
                        local_fee = soup_dom_fees.find('p', text=head) \
                            .find_parent('td') \
                            .find_parent('tr').find('td', class_='tr3 td2')
                        if local_fee:
                            print('found local fee via HTML file: ', tag_text(local_fee))
                            course_data['Local_Fees'] = tag_text(local_fee).replace('$', '').replace(',', '')
                    except AttributeError:
                        print('cant find local fees in file')

    # CHECK LOCAL FILES FOR INT FEES
    try:
        title_pattern = course_data['Course'] if title_ is None else title_
        int_fee = soup_int_fees.find('p', text=re.compile('^.*' + title_pattern + '.*$')) \
            .find_parent('td') \
            .find_parent('tr').find('td', class_='tr6 td22')
        if int_fee:
            print('found int fee via HTML file: ', tag_text(int_fee))
            course_data['Int_Fees'] = tag_text(int_fee).replace('$', '').replace(',', '')
        if not int_fee:
            int_fee = soup_int_fees.find('p', text=re.compile('^.*' + title_pattern + '.*$')) \
                .find_parent('td') \
                .find_parent('tr').find('td', class_='tr6 td36')
            if int_fee:
                print('found int fee via HTML file: ', tag_text(int_fee))
                course_data['Int_Fees'] = tag_text(int_fee).replace('$', '').replace(',', '')
            if not int_fee:
                int_fee = soup_int_fees.find('p', text=re.compile('^.*' + title_pattern + '.*$')) \
                    .find_parent('td') \
                    .find_parent('tr').find('td', class_='tr6 td65')
                if int_fee:
                    print('found int fee via HTML file: ', tag_text(int_fee))
                    course_data['Int_Fees'] = tag_text(int_fee).replace('$', '').replace(',', '')
                if not int_fee:
                    int_fee = soup_int_fees.find('p', text=re.compile('^.*' + title_pattern + '.*$')) \
                        .find_parent('td') \
                        .find_parent('tr').find_all('td')[4]
                    if int_fee:
                        ('found int fee via HTML file: ', tag_text(int_fee))
                        course_data['Int_Fees'] = tag_text(int_fee).replace('$', '').replace(',', '')
                    if not int_fee:
                        try:
                            head, sep, tail = title_.partition(comma)
                            int_fee = soup_int_fees.find('p', text=head) \
                                .find_parent('td') \
                                .find_parent('tr').find_all('td')[4]
                            if int_fee:
                                print('found int fee via HTML file: ', tag_text(int_fee))
                                course_data['Int_Fees'] = tag_text(int_fee).replace('$', '').replace(',', '')
                        except (AttributeError, IndexError):
                            try:
                                head, sep, tail = title_.partition(bracket_o)
                                int_fee = soup_int_fees.find('p', text=head) \
                                    .find_parent('td') \
                                    .find_parent('tr').find_all('td')[4]
                                if int_fee:
                                    print('found int fee via HTML file: ', tag_text(int_fee))
                                    course_data['Int_Fees'] = tag_text(int_fee).replace('$', '').replace(',', '')
                            except (AttributeError, IndexError):
                                try:
                                    head, sep, tail = title_.partition(ampersand)
                                    int_fee = soup_int_fees.find('p', text=head) \
                                        .find_parent('td') \
                                        .find_parent('tr').find_all('td')[4]
                                    if int_fee:
                                        print('found int fee via HTML file: ', tag_text(int_fee))
                                        course_data['Int_Fees'] = tag_text(int_fee).replace('$', '').replace(',', '')
                                except (AttributeError, IndexError):
                                    pass
    except (AttributeError, IndexError):
        print('cant find int fee in local HTML file')

    # DESCRIPTION
    try:
        desc1_tag = soup.find('h2', {'class': 'text-uppercase h4 font-bold'}).find_next('p')
        if desc1_tag:
            desc1 = tag_text(desc1_tag)
            course_data['Description'] = desc1 + '\t'
    except AttributeError:
        pass
    try:
        desc2_tag = soup.find('h2', text=re.compile('^.*WHAT TO EXPECT.*$', re.IGNORECASE)) \
            .find_parent('div', {'class': 'col-12'}) \
            .find_next('div', {'class': 'col-12 col-lg-8 pb-3'})
        if desc2_tag:
            desc2 = tag_text(desc2_tag)
            course_data['Description'] += desc2
    except AttributeError:
        pass

    # REMARKS
    try:
        rem1_tag = soup.find("h2", text=re.compile("^.*What you'll study.*$", re.IGNORECASE)) \
            .find_next("p")
        if rem1_tag:
            rem1 = tag_text(rem1_tag)
            course_data['Remarks'] = rem1 + '\t'
    except AttributeError:
        pass
    try:
        rem2_tag = soup.find('h3', text=re.compile('Workload', re.IGNORECASE)).find_next('a').find_next('div')
        if rem2_tag:
            rem2 = tag_text(rem2_tag)
            course_data['Remarks'] += rem2 + '\t'
    except AttributeError:
        pass

    # ONLINE
    try:
        online_tag = soup.find('p', text=re.compile('^.*Available online\..*$', re.IGNORECASE))
        if online_tag:
            rem3 = tag_text(online_tag)
            course_data['Remarks'] += rem3 + '\t'
            course_data['Online'] = 'Yes'
    except AttributeError:
        pass

    # OUTCOMES
    try:
        out_tag = soup.find('h3', text=re.compile('^.*WHAT CAN YOU EXPECT WHEN YOU GRADUATE.*$', re.IGNORECASE)) \
            .find_next('div') \
            .find_next('div')
        if out_tag:
            outcomes = tag_text(out_tag)
            course_data['Career_Outcomes'] = outcomes
    except AttributeError:
        try:
            out_tag = soup.find('div', text=re.compile('^.*WHAT CAN YOU EXPECT WHEN YOU GRADUATE.*$', re.IGNORECASE)) \
                .find_next('div') \
                .find_next('div')
            if out_tag:
                outcomes = tag_text(out_tag)
                course_data['Career_Outcomes'] = outcomes
        except AttributeError:
            pass
    try:
        if len(course_data['Career_Outcomes']) < 2:
            out_tag_extra = soup.find('div', text=re.compile('^.*Learning Outcomes:.*$', re.IGNORECASE)).find_next('ul')
            if out_tag_extra:
                out_new = tag_text(out_tag_extra)
                course_data['Career_Outcomes'] = out_new
    except (AttributeError, IndexError):
        pass

    # PREREQUISITES
    try:
        year12_tag = soup.find(attrs={'text': re.compile('^.*Year 12 or equivalent.*$', re.IGNORECASE)})
        if year12_tag:
            course_data['Prerequisite_3'] = 'Year 12'
        else:
            year12_tag = soup.find(
                attrs={'text': re.compile('^.*Year 12 certificate \(or equivalent\).*$', re.IGNORECASE)})
            if year12_tag:
                course_data['Prerequisite_3'] = 'Year 12'
    except AttributeError:
        pass
    try:
        ielts_tag = soup.find('li', text=re.compile('^.*Academic IELTS.*$', re.IGNORECASE))
        if ielts_tag:
            print('ielts found')
            ielts_raw = tag_text(ielts_tag)
            ielts_val = re.findall(r'[-+]?\d*\.\d+|\d+', ielts_raw)
            course_data['Prerequisite_2'] = 'IELTS'
            course_data['Prerequisite_2_grade_2'] = ielts_val[0]
    except AttributeError:
        try:
            ielts_tag2 = soup.find('li', text=re.compile('^.*IELTS.*[\d].*with no band less than.*$'))
            if ielts_tag2:
                print('ielts found with second attempt')
                ielts_raw = tag_text(ielts_tag2)
                ielts_val = re.findall(r'[-+]?\d*\.\d+|\d+', ielts_raw)
                course_data['Prerequisite_2'] = 'IELTS'
                course_data['Prerequisite_2_grade_2'] = ielts_val[0]
        except AttributeError:
            pass

    # DURATION
    full_time = None
    part_time = None
    accelerated = None
    time.sleep(1)
    try:
        full_time_tag = soup.find('p', text=re.compile('^.*\(Full-time\).*$', re.IGNORECASE))
        full_time_tag2 = soup.find('p', text=re.compile('^[\d].*full-time.*$', re.IGNORECASE))
        full_time_tag3 = soup.find('p', text=re.compile('^.*full-time:.*[\d].*years|months|weeks|semesters|trimesters{0,40}$', re.IGNORECASE))
        full_time_tag4 = soup.find('p', text=re.compile('^.*full time:.*[\d].*years|months|weeks|semesters|trimesters{0,40}$', re.IGNORECASE))
        full_time_tag5 = soup.find('p', text=re.compile('^.*full time.*[\d].*years|months|weeks|semesters|trimesters{0,40}$', re.IGNORECASE))
        full_time_tag6 = soup.find('p', text=re.compile(
            '^.*full-time:.*[\d].*(?!accelerated).*years\)|months\)|weeks\)|semesters\)|trimesters\)$', re.IGNORECASE))

        if pure_url == 'https://www.torrens.edu.au/courses/business/doctor-of-business-leadership':
            full_time = tag_text(full_time_tag3).lower().replace('full-time:', '')
            print('full time duration (reg3): ', full_time)

        if full_time_tag:
            full_time = tag_text(full_time_tag).lower().replace('(full-time)', '')
            print('full time duration (reg1): ', full_time)
        elif not full_time_tag and full_time_tag2:
            full_time = tag_text(full_time_tag2).lower().replace('full-time', '')
            print('full time duration (reg2): ', full_time)

        elif not full_time_tag and not full_time_tag2 and full_time_tag3:
            full_time = tag_text(full_time_tag3).lower().replace('full-time:', '')
            print('full time duration (reg3): ', full_time)

        elif not full_time_tag and not full_time_tag2 and not full_time_tag3 and full_time_tag4:
            full_time = tag_text(full_time_tag4).lower().replace('full-time:', '')
            print('full time duration (reg4): ', full_time)
        elif not full_time_tag and not full_time_tag2 and not full_time_tag3 and not full_time_tag4 and full_time_tag5:
            full_time = tag_text(full_time_tag5).lower().replace('full-time:', '')
            print('full time duration (reg5): ', full_time)
        elif not full_time_tag and not full_time_tag2 and not full_time_tag3 and not full_time_tag4 and not full_time_tag5 and full_time_tag6:
            full_time = tag_text(full_time_tag6).lower().replace('full-time:', '')
            print('full time duration (reg6): ', full_time)

        accelerated_tag = soup.find('p', text=re.compile('^.*\(Accelerated\).*$', re.IGNORECASE))
        accelerated_tag2 = soup.find('p', text=re.compile('^[\d].*accelerated.*$', re.IGNORECASE))
        accelerated_tag3 = soup.find('p', text=re.compile('^.*accelerated:.*[\d].*$', re.IGNORECASE))
        if accelerated_tag:
            accelerated = tag_text(accelerated_tag).lower().replace('(accelerated)', '')
            print('accelerated duration: ', accelerated)
        elif not accelerated_tag and accelerated_tag2:
            accelerated = tag_text(accelerated_tag2).lower().replace('accelerated', '')
            print('accelerated duration: ', accelerated)
        elif not accelerated_tag and not accelerated_tag2 and accelerated_tag3:
            accelerated = tag_text(accelerated_tag3).lower().replace('accelerated:', '')
            print('accelerated duration: ', accelerated)

        part_time_tag = soup.find('p', text=re.compile('^.*\(Part-time\).*$', re.IGNORECASE))
        part_time_tag2 = soup.find('p', text=re.compile('^[\d].*part-time.*$', re.IGNORECASE))
        part_time_tag3 = soup.find('p', text=re.compile('^.*part-time:.*[\d].*$', re.IGNORECASE))
        part_time_tag4 = soup.find('p', text=re.compile('^.*part time:.*[\d].*years|months|weeks|semesters|trimesters{0,40}$', re.IGNORECASE))
        part_time_tag5 = soup.find('p', text=re.compile('^.*part time.*[\d].*years|months|weeks|semesters|trimesters{0,40}$', re.IGNORECASE))
        if part_time_tag:
            course_data['Part_Time'] = 'Yes'
            part_time = tag_text(part_time_tag).lower().replace('(part-time)', '')
            print('part-time duration: ', part_time)
        elif not part_time_tag and part_time_tag2:
            course_data['Part_Time'] = 'Yes'
            part_time = tag_text(part_time_tag2).lower().replace('part-time', '')
            print('part-time duration: ', part_time)
        elif not part_time_tag and not part_time_tag2 and part_time_tag3:
            course_data['Part_Time'] = 'Yes'
            part_time = tag_text(part_time_tag3).lower().replace('part-time:', '')
            print('part-time duration: ', part_time)
        elif not part_time_tag and not part_time_tag2 and not part_time_tag3 and part_time_tag4:
            course_data['Part_Time'] = 'Yes'
            part_time = tag_text(part_time_tag4).lower().replace('part-time:', '')
            print('part-time duration: ', part_time)
        elif not part_time_tag and not part_time_tag2 and not part_time_tag3 and not part_time_tag4 and part_time_tag5:
            course_data['Part_Time'] = 'Yes'
            part_time = tag_text(part_time_tag5).lower().replace('part-time:', '')
            print('part-time duration: ', part_time)

    except (AttributeError, IndexError) as err:
        print(err.__traceback__)

    try:
        if full_time is not None and 'hours' not in full_time:
            duration = DurationConverter.convert_duration(full_time.replace('trimester', 'semester'))
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
    except TypeError:
        print('type error with trimester again')

    try:
        if full_time is None and part_time is not None:
            duration = DurationConverter.convert_duration(part_time.replace('trimester', 'semester'))
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
    except TypeError:
        pass

    try:
        if full_time is None and part_time is None and accelerated is not None:
            duration = DurationConverter.convert_duration(accelerated.replace('trimester', 'semester'))
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
    except TypeError:
        pass

    # AVAILABILITY
    try:
        is_int_tag = soup.find('a', text=re.compile('INTERNATIONAL ADMISSION CRITERIA', re.IGNORECASE))
        is_dom_tag = soup.find('a', text=re.compile('DOMESTIC ADMISSION CRITERIA', re.IGNORECASE))
        if is_int_tag and is_dom_tag:
            course_data['Availability'] = 'A'
        if is_dom_tag:
            if not is_int_tag:
                course_data['Availability'] = 'D'
        if not is_dom_tag:
            if is_int_tag:
                course_data['Availability'] = 'I'
    except AttributeError:
        pass

    # CITIES
    try:
        camp_tag = soup.find('i', {'class': 'icon icon-x2 fa-bank white-bg'}) \
            .find_parent('div', {'class': 'col-auto d-flex my-2 pr-0'}) \
            .find_next('div', {'class': 'col d-flex my-2'})
        if camp_tag:
            campus_string = tag_text(camp_tag)
            campuses = campus_string.split()
            print('found campuses: ', campuses)
            for i in possible_cities:
                if i in campuses or i in campus_string:
                    actual_cities.add(i)
        if not camp_tag:
            camp2_tag = soup.find('div', {'class': 'row collapse show d-md-flex pb-3', 'id': 'ki-1'}) \
                .find('div', {'class': 'col d-flex my-2'})
            if camp2_tag:
                print('found cities sing second approach')
                campus2_string = tag_text(camp2_tag)
                campuses2 = campus2_string.split()
                for i in possible_cities:
                    if i in campuses2 or i in campus2_string:
                        actual_cities.add(i)
    except (AttributeError, IndexError, KeyError) as ae:
        print(ae.__cause__, ae.__context__, ae.__traceback__, ae.__str__())
        pass

    # ADVANCE ONLINE CHECKING
    try:
        online_tag2 = soup.find('i', {'class': 'icon icon-x2 fa-laptop white-bg'}) \
            .find_parent('div', {'class': 'col-auto d-flex my-2 pr-0'}) \
            .find_next('div', {'class': 'col d-flex my-2'})
        if online_tag2:
            course_data['Online'] = 'Yes'
            if len(course_data['City']) < 4:
                campus_string = tag_text(online_tag2)
                campuses = campus_string.split()
                print('found campuses from online tag: ', campuses)
                for i in possible_cities:
                    if i in campuses or i in campus_string:
                        actual_cities.add(i)
    except (AttributeError, IndexError, TypeError):
        pass

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

with open(csv_file, 'w', encoding='utf-8', newline='') as output_file:
    dict_writer = csv.DictWriter(output_file, course_dict_keys)
    dict_writer.writeheader()
    dict_writer.writerows(course_data_all)
