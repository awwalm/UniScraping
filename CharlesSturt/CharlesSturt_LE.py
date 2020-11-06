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
course_links = []
each_url = 'https://study.csu.edu.au/courses/all'
domain_url = 'https://study.csu.edu.au/'
browser.get(each_url)
pure_url = each_url.strip()
each_url = browser.page_source

soup = bs4.BeautifulSoup(each_url, 'html.parser')


ul_orderings = soup.find_all('ul', {'class': 'calp-lists'})
if ul_orderings:
    for ul in ul_orderings:
        li_tags = ul.find_all('li')
        if li_tags:
            for li in li_tags:
                link = li.find('a', href=True)['href']
                if link:
                    link_ = urljoin(domain_url, link)
                    course_links.append(link_)
                    print(link_)


# FILE
course_links_file_path = os.getcwd().replace('\\', '/') + '/charles_sturt_links_file'
course_links_file = open(course_links_file_path, 'w', encoding='utf8')
for i in course_links:
    if i is not None and i is not "" and i is not "\n":
        if i == course_links[-1]:
            course_links_file.write(i.strip())
        else:
            course_links_file.write(i.strip() + '\n')

course_links_file.close()

#  print(*course_links, sep='\n')
