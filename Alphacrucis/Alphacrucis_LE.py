import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, JavascriptException
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
each_url = 'https://study.ac.edu.au/'
domain_url = 'https://study.ac.edu.au/'
browser.get(each_url)
pure_url = each_url.strip()
each_url = browser.page_source

soup = bs4.BeautifulSoup(each_url, 'html.parser')

# INTERNATIONAL UNDERGRAD LINK EXTRACTOR =============================================================================
bach_course_links = []

html_ = None
url_ = 'https://study.ac.edu.au/'
delay_ = 15  # seconds

browser_ = webdriver.Chrome(executable_path=exec_path)
browser_.get(url_)

try:
    categories = browser_.find_elements_by_xpath("//div[@class='contents']/a[@class='url-link']")
    for i in categories:
        course_type_links.append(i.get_attribute('href'))
        print(i.get_attribute('href'))
    for j in course_type_links:
        browser_.get(j)
        x = browser_.find_elements_by_xpath("//section[@class='block-course_list']/div/p/a")
        for k in x:
            w = k.get_attribute('href')
            bach_course_links.append(w)
            print(w)
        x = browser_.find_elements_by_xpath("//section[@class='block-paragraph']/div/p/a")
        for k in x:
            w = k.get_attribute('href')
            bach_course_links.append(w)
            print(w)


except TimeoutException:
    print('timeout exception')

# noinspection SpellCheckingInspection
bach_course_links_file_path = os.getcwd().replace('\\', '/') + '/alphacrucis_links_file'
bach_course_links_file = open(bach_course_links_file_path, 'w')
for i in bach_course_links:
    if i is not None and i is not "" and i is not "\n":
        if i == bach_course_links[-1]:
            bach_course_links_file.write(i.strip())
        else:
            bach_course_links_file.write(i.strip() + '\n')

bach_course_links_file.close()

#  print(*bach_course_links, sep='\n')
