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
each_url = 'https://www.notredame.edu.au/study/programs'
domain_url = 'https://www.notredame.edu.au/'
browser.get(each_url)
pure_url = each_url.strip()
each_url = browser.page_source

soup = bs4.BeautifulSoup(each_url, 'html.parser')

# INTERNATIONAL UNDERGRAD LINK EXTRACTOR =============================================================================
bach_course_links = []

html_ = None
url_ = 'https://www.notredame.edu.au/study/programs'
delay_ = 15  # seconds

browser_ = webdriver.Chrome(executable_path=exec_path)
browser_.get(url_)

try:
    categories = soup.find_all('h3', {'class': 'course-tiles__title'})
    WebDriverWait(browser_, delay_).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, "//h3[@class='course-tiles__title']"))
    )
    for i in range(len(categories)):
        try:
            js = "var aa=document.getElementsByClassName('top-nav__container')[0];aa.parentNode.removeChild(aa)"
            browser_.execute_script(js)
            print('top nav deleted')
            each_url = browser_.page_source
            soup_ = bs4.BeautifulSoup(each_url, 'lxml')
        except JavascriptException:
            pass

        category = browser_.find_element_by_xpath(
            f"(//h3[@class='course-tiles__title'])[{i+1}]"
        )
        time.sleep(0.5)
        category.click()

        html_ = browser_.page_source
        print('got page source')

        if html_:
            soup_ = bs4.BeautifulSoup(html_, 'lxml')
            if soup_:
                a_tags = soup_.find_all('a', {'class': 'program-list__title', 'href': True})
                for a in a_tags:
                    link = a['href']
                    bach_link = urljoin(domain_url, link)
                    bach_course_links.append(bach_link)
                    print(bach_link)
except TimeoutException:
    print('timeout exception')


bach_course_links_file_path = os.getcwd().replace('\\', '/') + '/notre_dame_links_file'
bach_course_links_file = open(bach_course_links_file_path, 'w')
for i in bach_course_links:
    if i is not None and i is not "" and i is not "\n":
        if i == bach_course_links[-1]:
            bach_course_links_file.write(i.strip())
        else:
            bach_course_links_file.write(i.strip() + '\n')

bach_course_links_file.close()

#  print(*bach_course_links, sep='\n')
