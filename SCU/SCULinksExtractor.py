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


# MAIN ROUTINE
course_type_links = []
each_url = 'https://www.scu.edu.au/study-at-scu/courses/'
domain_url = 'https://www.scu.edu.au'
browser.get(each_url)
time.sleep(2)
pure_url = each_url.strip()
each_url = browser.page_source

soup = bs4.BeautifulSoup(each_url, 'html.parser')

# LINK EXTRACTOR =============================================================================
course_links = []
table_body = soup.find('table', {'class': 'course-table'}).find('tbody')
if table_body:
    tr_tags = table_body.find_all('tr')
    if tr_tags:
        for tr in tr_tags:
            a = tr.find('td').find('a', href=True)
            if a:
                link = a['href']
                the_link = urljoin(domain_url, link)
                course_links.append(the_link)
                print(the_link)

# FILE
course_links_file_path = os.getcwd().replace('\\', '/') + '/scu_links_file'
course_links_file = open(course_links_file_path, 'w')
for i in course_links:
    if i is not None and i is not "" and i is not "\n":
        if i == course_links[-1]:
            course_links_file.write(i.strip())
        else:
            course_links_file.write(i.strip()+'\n')

course_links_file.close()
#  print(*bach_course_links, sep='\n')
