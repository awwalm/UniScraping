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
exec_path = exec_path.parent.parent.parent.parent.__str__() + '/Libraries/Google/v86/chromedriver.exe'
browser = webdriver.Chrome(executable_path=exec_path, chrome_options=option)

# MAIN ROUTINE
course_type_links = []
each_url = 'https://programsandcourses.anu.edu.au/catalogue'
domain_url = 'https://programsandcourses.anu.edu.au'
browser.get(each_url)
pure_url = each_url.strip()
each_url = browser.page_source

soup = bs4.BeautifulSoup(each_url, 'html.parser')

# POSTGRAD LINK EXTRACTOR =============================================================================
pg_course_links = []

html_ = None
url_ = 'https://programsandcourses.anu.edu.au/catalogue'
selector_ = '.catalogue-search-results__table catalogue-search-results__table--program table > div'
delay_ = 10  # seconds

browser_ = webdriver.Chrome(executable_path=exec_path)
browser_.get(url_)

try:
    WebDriverWait(browser_, delay_).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//a[@href='javascript:;' and @data__-template='program-template' and @sortshowall='false']"))
    )
    expander = browser_.find_element_by_xpath(
        "//a[@href='javascript:;' and @data__-template='program-template' and @sortshowall='false']")

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
        table_body = soup_.find('table',
                                class_='catalogue-search-results__table catalogue-search-results__table--program table').find(
            'tbody')
        if table_body:
            tr_tags = table_body.find_all('tr')
            if tr_tags:
                for tr in tr_tags:
                    if 'postgraduate' in tr.get_text().__str__().lower():
                        td = tr.find('td')  # only the first one also has the link
                        if td:
                            a = td.find('a', href=True)
                            if a:
                                link = a['href']
                                pg_link = urljoin(domain_url, link)
                                pg_course_links.append(pg_link)
                                print(pg_link)

        # POSTGRAD FILE
        pg_course_links_file_path = os.getcwd().replace('\\', '/') + '/anu_postgrad_links_file'
        pg_course_links_file = open(pg_course_links_file_path, 'w')
        for i in pg_course_links:
            if i is not None and i is not "" and i is not "\n":
                if i == pg_course_links[-1]:
                    pg_course_links_file.write(i.strip())
                else:
                    pg_course_links_file.write(i.strip() + '\n')

        pg_course_links_file.close()

#  print(*bach_course_links, sep='\n')
