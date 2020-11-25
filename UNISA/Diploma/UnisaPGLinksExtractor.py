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
exec_path = exec_path.parent.parent.parent.parent.__str__() + '/Libraries/Google/v86/chromedriver.exe'
browser = webdriver.Chrome(executable_path=exec_path, chrome_options=option)


# MAIN ROUTINE
course_type_links = []
each_url = 'https://search.unisa.edu.au/s/search.html?collection=study-search&query=&f.Tabs%7Ctab=Degrees+%26+Courses&f.Student+Type%7CpmpProgramsStudentType=International&f.Study+Type%7CstudyType=Degree&f.Level+of+study%7CfacetLevelStudy=Postgraduate&f.Location%7CfacetProgramsCampus=All'
domain_url = 'https://search.unisa.edu.au'

# LINK EXTRACTOR =============================================================================
course_links = []
course_links_2 = []
pages = set()

pages.add(each_url)
i = 1
while i <= 111:
    cur_url = each_url + '&start_rank=' + str(i)
    pages.add(cur_url)
    print(cur_url)
    i += 10

for j in pages:
    browser.get(j)
    time.sleep(0.5)
    pure_url = j.strip()
    each_page = browser.page_source
    soup = bs4.BeautifulSoup(each_page, 'html.parser')

    divs = soup.find_all('div', class_='search-result-block small-margin-bottom theme-background-white search-result-degree')
    if divs:
        for div in divs:
            a = div.find('a', href=True)
            if a:
                link = a['href']
                the_link = urljoin(domain_url, link)
                print(the_link)
                course_links.append(the_link)

# FILE (OTHER LINKS)
course_links_file_path = os.getcwd().replace('\\', '/') + '/unisa_postgrad_links_file'
course_links_file = open(course_links_file_path, 'w')
for i in course_links:
    if i is not None and i is not "" and i is not "\n":
        if i == course_links[-1]:
            course_links_file.write(i.strip())
        else:
            course_links_file.write(i.strip()+'\n')
course_links_file.close()
