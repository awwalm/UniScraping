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
each_url = 'https://www.sydney.edu.au/courses/search.html?search-type=course'
domain_url = 'https://www.sydney.edu.au'
browser.get(each_url)
pure_url = each_url.strip()
each_url = browser.page_source

print('got page 1 source'
      '')
soup = bs4.BeautifulSoup(each_url, 'lxml')
if soup:
    a_tags = soup.find_all('a', {
        'class': 'b-result-container__item-wrapper b-result-container__item-wrapper--data b-link--no-underline'})
    if a_tags:
        for a in a_tags:
            link__ = a['href']
            link = urljoin(domain_url, link__)
            course_links.append(link)
            print(link)

# INTERNATIONAL UNDERGRAD LINK EXTRACTOR =============================================================================
bach_course_links = []

html_ = None
url_ = 'https://www.sydney.edu.au/courses/search.html?search-type=course'
delay_ = 5  # seconds

browser_ = webdriver.Chrome(executable_path=exec_path)
browser_.get(url_)

for i in range(2, 60):
    try:
        WebDriverWait(browser_, delay_).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[@class='m-pagination']"))
        )
        next_page = browser_.find_element_by_xpath(
            f"//a[@class='m-pagination__item' and contains(text(), {i})]"
        )
        next_page.click()
        time.sleep(1)

    except TimeoutException:
        print('timeout exception')
    else:
        html_ = browser_.page_source
        print(f'got page {i} source')
        # magic happens within this block
        if html_:
            soup_ = bs4.BeautifulSoup(html_, 'lxml')
            if soup_:
                a_tags = soup_.find_all('a', {
                    'class': 'b-result-container__item-wrapper b-result-container__item-wrapper--data b-link--no-underline'})
                if a_tags:
                    for a in a_tags:
                        link__ = a['href']
                        link = urljoin(domain_url, link__)
                        course_links.append(link)
                        print(link)

# FILE
course_links_file_path = os.getcwd().replace('\\', '/') + '/uo_sydney_links_file'
course_links_file = open(course_links_file_path, 'w')
for i in course_links:
    if i is not None and i is not "" and i is not "\n":
        if i == course_links[-1]:
            course_links_file.write(i.strip())
        else:
            course_links_file.write(i.strip() + '\n')

course_links_file.close()

#  print(*course_links, sep='\n')
