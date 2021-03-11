from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import csv
from newspaper import Article


# url = 'https://www.reuters.com/markets'

# config
options = Options()
options.headless = False
numpages = 1
# initialize a webdriver

def get_reuters_links(start_url,count):
    d = webdriver.Chrome(ChromeDriverManager().install())
    d.get('https://www.reuters.com/markets')
    soup = BeautifulSoup(d.page_source, 'lxml')
    all_urls = []
    for i in range(count):
        try:
            soup = BeautifulSoup(d.page_source, 'html.parser')
            blacklist = set()
            for story in soup.find_all(class_='story featured-article no-border-bottom'):
                for link in story.find_all('a'):
                    blacklist.add(link.get('href'))
            for story in soup.find_all(class_='story no-border-bottom'):
                for link in story.find_all('a'):
                    blacklist.add(link.get('href'))
            for story in soup.find_all(class_='story'):
                for link in story.find_all('a'):
                    link = link.get('href')
                    if link in blacklist:
                        # print(f'omitted {link}')
                        continue
                    link = start_url + str(link)
                    if link not in all_urls:
                        all_urls.append(link)
            print(len(all_urls))
            d.find_element_by_class_name("control-nav-next").click()
        except:
            time.sleep(3)
    return all_urls

def article_analyzer(url_list):
    output_data = {}
    count = 0
    completed = 0
    failed = 0
    id = 0

    for url in url_list:
        try:
            article = Article(url)
            article.download()
            article.parse()
            output_data[id] = {}
            output_data[id]['title'] = article.title
            output_data[id]['text'] = article.text
            output_data[id]['date'] = article.publish_date
            id += 1
            print("Finished parsing {}th article ".format(count))
            count+=1
            completed += 1
        except:
            print("Wasn't able to download this article {} ".format(count))
            print(url)
            count += 1
            failed += 1
            continue
    return output_data,completed,failed
# If success, all the data will be saved in "all_urls"

def main(url,count):
    print('--- Started scraping articles ---')
    start_time = time.time()
    reuters_links = get_reuters_links(url,count)
    print("--- Finished scraping articles in %s seconds ---" % (time.time() - start_time))

    print('--- Started parsing articles ---')
    start_time = time.time()
    final_data,completed,failed = article_analyzer(reuters_links)
    print(completed,failed)
    print("--- Finished scraping and parsing articles in %s seconds ---" % (time.time() - start_time))
    return final_data,completed,failed

