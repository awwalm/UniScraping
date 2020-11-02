import re
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
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

# MAIN ROUTINE
course_links = []
each_url = 'https://www.jcu.edu.au/courses'
domain_url = 'https://www.jcu.edu.au'
browser.get(each_url)
pure_url = each_url.strip()
each_url = browser.page_source

soup = bs4.BeautifulSoup(each_url, 'html.parser')

if soup:
    tr_tags = soup.find('table', {'class': 'jcu-v1__course-table jcu-v1__border-color__theme_6'})\
        .find('tbody')\
        .find_all('tr', {'class': 'jcu-v1__course-table__row'})

    if tr_tags:
        for tr in tr_tags:
            a = tr.find('td', {'class': 'jcu-v1__course-table--name'})\
                .find('div', {'class': 'jcu-v1__course-table__row-data'})\
                .find('a', href=True)
            if a:
                link_ = a['href']
                link = urljoin(domain_url, link_)
                course_links.append(link)
                print(link)

# FILE
course_links_file_path = os.getcwd().replace('\\', '/') + '/jcu_links_file'
course_links_file = open(course_links_file_path, 'w')
for i in course_links:
    if i is not None and i is not "" and i is not "\n":
        if i == course_links[-1]:
            course_links_file.write(i.strip())
        else:
            course_links_file.write(i.strip() + '\n')

course_links_file.close()

#  print(*course_links, sep='\n')
