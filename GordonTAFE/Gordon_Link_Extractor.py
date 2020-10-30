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
each_url = 'https://www.thegordon.edu.au/courses/all-courses'
domain_url = 'https://www.thegordon.edu.au/courses'
browser.get(each_url)
time.sleep(2)
pure_url = each_url.strip()
each_page = browser.page_source
soup = bs4.BeautifulSoup(each_page, 'html.parser')

if soup:
    li_tags = soup.find('h2', text='Courses by category').find_next('ul').find_all('li')
    if li_tags:
        for li in li_tags:
            a = li.find('a', href=True)
            if a:
                link_ = a['href']
                link = urljoin(each_url, link_)
                course_links.append(link.lower())
                print(link.lower())

# FILE
bach_course_links_file_path = os.getcwd().replace('\\', '/') + '/gordon_links_file'
bach_course_links_file = open(bach_course_links_file_path, 'w')
for i in course_links:
    if i is not None and i is not "" and i is not "\n":
        if i == course_links[-1]:
            bach_course_links_file.write(i.strip())
        else:
            bach_course_links_file.write(i.strip() + '\n')

bach_course_links_file.close()

#  print(*bach_course_links, sep='\n')
