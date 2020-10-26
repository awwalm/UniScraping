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
each_url = 'https://www.griffith.edu.au/study/degrees?academicLevel=bachelor'
domain_url = 'https://www.griffith.edu.au'
browser.get(each_url)
time.sleep(2)
pure_url = each_url.strip()
each_url = browser.page_source

soup = bs4.BeautifulSoup(each_url, 'html.parser')

# BACHELORS LINK EXTRACTOR =============================================================================
bach_course_links = []
a_tags = soup.find_all('a', href=re.compile('^/study/degrees/', re.IGNORECASE))
if a_tags:
    for a in a_tags:
        link = a['href']
        bach_link = urljoin(domain_url, link)
        bach_course_links.append(bach_link)
        print(bach_link)

# BACHELORS FILE
bach_course_links_file_path = os.getcwd().replace('\\', '/') + '/griffith_bachelors_links_file'
bach_course_links_file = open(bach_course_links_file_path, 'w')
for i in bach_course_links:
    if i is not None and i is not "" and i is not "\n":
        if i == bach_course_links[-1]:
            bach_course_links_file.write(i.strip())
        else:
            bach_course_links_file.write(i.strip()+'\n')

bach_course_links_file.close()
#  print(*bach_course_links, sep='\n')
