import re
import time
from pathlib import Path
from selenium import webdriver
from urllib.parse import urljoin
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
browser2 = webdriver.Chrome(executable_path=exec_path, chrome_options=option)

# MAIN ROUTINE
course_type_links = []
course_links = []
category_url = 'https://study.unimelb.edu.au/find/'
each_url = ''
domain_url = 'https://study.unimelb.edu.au'
browser.get(category_url)
pure_url = category_url.strip()
category_url = browser.page_source

soup = bs4.BeautifulSoup(category_url, 'html.parser')
if soup:
    a_tags = soup.find_all('a', {'class': 'interest-item', 'data-test': 'interest-item'})
    if a_tags:
        for a in a_tags:
            link_ = a['href']
            link = urljoin(domain_url, link_)
            course_type_links.append(link)
            print(link)
        print('\ndone fetching categories. now fetching course links...\n')

if len(course_type_links) > 0:
    for faculty in course_type_links:
        browser2.get(faculty)
        time.sleep(0.2)
        faculty = browser2.page_source
        soup_ = bs4.BeautifulSoup(faculty, 'html.parser')
        a_tags = soup_.find_all('a', {'data-test': 'card-course', 'href': True})
        if a_tags:
            for a in a_tags:
                link__ = a['href']
                link = urljoin(domain_url, link__)
                if link not in course_links:
                    course_links.append(link)
                    print(link)

# FILE
course_links_file_path = os.getcwd().replace('\\', '/') + '/uo_melbourne_links_file'
course_links_file = open(course_links_file_path, 'w')
for i in course_links:
    if i is not None and i is not "" and i is not "\n":
        if i == course_links[-1]:
            course_links_file.write(i.strip())
        else:
            course_links_file.write(i.strip() + '\n')

course_links_file.close()

#  print(*course_links, sep='\n')
