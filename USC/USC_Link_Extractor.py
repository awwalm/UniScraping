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
each_url = 'https://www.usc.edu.au/study?discipline=Study+area&location=Study+location'
domain_url = 'https://www.usc.edu.au'
browser.get(each_url)
pure_url = each_url.strip()
each_url = browser.page_source

soup = bs4.BeautifulSoup(each_url, 'html.parser')

# INTERNATIONAL UNDERGRAD LINK EXTRACTOR =============================================================================
bach_course_links = []

html_ = None
url_ = 'https://www.usc.edu.au/study?discipline=Study+area&location=Study+location'
delay_ = 15  # seconds

browser_ = webdriver.Chrome(executable_path=exec_path)
browser_.get(url_)

try:
    WebDriverWait(browser_, delay_).until(
        EC.element_to_be_clickable(
            (By.XPATH, "(//option[@label='Show all' and @value='Show all'])[4]"))
    )  # "//button[@class='src-components-SidebarPublic-___sidebarPublic__browse-all___G1YcG']"
    expander = browser_.find_element_by_xpath(
        "(//option[@label='Show all' and @value='Show all'])[4]")

    expander.click()
    time.sleep(5)

except TimeoutException:
    print('timeout exception')
else:
    html_ = browser_.page_source
    print('got page source')
finally:
    browser_.quit()

if html_:
    soup_ = bs4.BeautifulSoup(html_, 'lxml')
    if soup_:
        divs = soup_.find_all('div', {'class': 'feature-card-content'})
        if divs:
            for div in divs:
                a = div.find('a', href=re.compile('^/study/courses-and-program'))
                if a:
                    link_ = a['href']
                    link = urljoin(domain_url, link_)
                    bach_course_links.append(link)
                    print(link)

        # FILE
        bach_course_links_file_path = os.getcwd().replace('\\', '/') + '/usc_links_file'
        bach_course_links_file = open(bach_course_links_file_path, 'w')
        for i in bach_course_links:
            if i is not None and i is not "" and i is not "\n":
                if i == bach_course_links[-1]:
                    bach_course_links_file.write(i.strip())
                else:
                    bach_course_links_file.write(i.strip() + '\n')

        bach_course_links_file.close()

#  print(*bach_course_links, sep='\n')
