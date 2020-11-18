import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, JavascriptException, NoSuchElementException, \
    ElementNotInteractableException
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
each_url = 'https://www.eit.edu.au/page/8/?post_type=courses&s#038;s'
domain_url = 'https://www.eit.edu.au/'
browser.get(each_url)
pure_url = each_url.strip()
each_url = browser.page_source

soup = bs4.BeautifulSoup(each_url, 'html.parser')

# INTERNATIONAL UNDERGRAD LINK EXTRACTOR =============================================================================
bach_course_links = []

html_ = None
url_ = 'https://www.eit.edu.au/page/8/?post_type=courses&s#038;s'
delay = 5  # seconds

browser_ = webdriver.Chrome(executable_path=exec_path)
browser_.get(url_)

try:
    pagination = soup.find_all('div', {'class': 'pagination'})
    WebDriverWait(browser_, delay).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, "//div[@class='pagination']"))
    )
    for i in range(1, 9):
        try:
            THE_XPATH = f"//a[contains(@class, 'page-numbers') and contains(@href, True) and contains(text(), {i})]"
            WebDriverWait(browser_, delay).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, f'{THE_XPATH}'))
            )
            next_page = browser_.find_element_by_xpath(f'{THE_XPATH}')
            try:
                next_page.click()
            except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
                pass
            each_url = browser_.page_source
            soup_ = bs4.BeautifulSoup(each_url, 'lxml')
            h3_tags = soup_.find_all('h3', {'class': 'course-heading'})
            if h3_tags:
                for h3 in h3_tags:
                    a = h3.find('a', {'href': True})
                    if a:
                        link = a['href']
                        if link:
                            link_ = urljoin(domain_url, link)
                            bach_course_links.append(link_)
                            print(link_)
        except (AttributeError, TimeoutException, NoSuchElementException, ElementNotInteractableException):
            pass
except TimeoutException:
    print('timeout exception')


bach_course_links_file_path = os.getcwd().replace('\\', '/') + '/eit_links_file'
bach_course_links_file = open(bach_course_links_file_path, 'w')
for i in bach_course_links:
    if i is not None and i is not "" and i is not "\n":
        if i == bach_course_links[-1]:
            bach_course_links_file.write(i.strip())
        else:
            bach_course_links_file.write(i.strip() + '\n')

bach_course_links_file.close()

#  print(*bach_course_links, sep='\n')
