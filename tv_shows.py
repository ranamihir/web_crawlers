# This is a script checks for new episodes of TV Shows, opens their download page in browser and starts downloading them automatically
from bs4 import BeautifulSoup
from datetime import datetime
from rarfile import RarFile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib import request, error
import requests
import time
import os
import glob

# List TV Shows
tv_shows = {
    "Arrow": 'http://awesomedl.ru/tag/arrow/',
    "Elementary": 'http://awesomedl.ru/tag/elementary/',
    "House of Cards": 'http://awesomedl.ru/tag/house-of-cards-2013/',
    "Marvel's Agents of S.H.I.E.L.D": 'http://awesomedl.ru/tag/marvels-agents-of-s-h-i-e-l-d/',
    "Marvel's Daredevil": 'http://awesomedl.ru/tag/marvels-daredevil/',
    "Sherlock": 'http://awesomedl.ru/tag/sherlock/',
    "Silicon Valley": 'http://awesomedl.ru/tag/silicon-valley/',
    "The Night Manager": 'http://awesomedl.ru/?s=the+night+manager&x=0&y=0',
    "Suits": 'http://awesomedl.ru/tag/suits/',
    "BBT": 'http://awesomedl.ru/tag/the-big-bang-theory/',
    "The Flash": 'http://awesomedl.ru/tag/the-flash-2014/'
}

def check_internet():
    try:
        request.urlopen('http://www.google.com', timeout=1)
        return True
    except error.URLError:
        pass
    return False

while 1:
    if check_internet():
        break

# Declare global variable browser
global browser

# Check for new episodes, download them if not downloaded already, and extract the RAR file. Move the video file to D: and delete the RAR file.
for show in tv_shows:
    print('Checking for ' + show + '...')
    url = tv_shows[show]
    try:
        source_code = requests.get(url)
        plain_text = source_code.text
        soup = BeautifulSoup(plain_text, "html5lib")
        for dates in soup.findAll('span', {'class': 'meta_date'}):
            if datetime.strptime(dates.text, '%B %d, %Y').date() == datetime.today().date():
                episode_url = dates.find_previous('a')['href']
                episode_source_code = requests.get(episode_url)
                episode_plain_text = episode_source_code.text
                episode_soup = BeautifulSoup(episode_plain_text, "html5lib")
                download_url = episode_soup.find('a', text='Mega')['href']
                try:
                    browser.get('http://' + download_url[download_url.index('goo.gl')::])
                except:
                    browser = webdriver.Chrome('C:/Users/ranamihir/AppData/Local/Programs/Python/Python35-32/chromedriver.exe')
                    browser.get('http://' + download_url[download_url.index('goo.gl')::])
                finally:
                    filename = WebDriverWait(browser, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'filename'))).get_attribute('title')
                    if not glob.glob('D:/' + filename.replace('.rar', '') + '*'):
                        print('\n' + show + ' is here!')
                        login_button = WebDriverWait(browser, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'top-login-button')))
                        login_button.click()
                        username = browser.find_element_by_id('login-name')
                        username.send_keys('<username>')
                        password = browser.find_element_by_id('login-password')
                        password.send_keys('<password>')
                        submit_button = browser.find_element_by_class_name('top-dialog-login-button').click()
                        while 1:
                            time.sleep(1)
                            try:
                                browser.find_element_by_class_name('not-logged')
                            except:
                                break
                        download_button = WebDriverWait(browser, 30).until(EC.visibility_of_element_located((By.CLASS_NAME, 'throught-browser')))
                        download_button.click()
                        print('Downloading ' + filename + '...')
                        while 1:
                            download_percent = browser.find_element_by_class_name('percents-txt').text
                            print('\r' + download_percent + ' completed.', end='')
                            if download_percent == '100 %':
                                time.sleep(30)
                                with RarFile('C:/Users/ranamihir/Downloads/' + filename) as rf:
                                    for f in rf.infolist():
                                        if not f.filename.endswith('.txt'):
                                            with open('D:/' + f.filename, 'wb') as of:
                                                of.write(rf.read(f))
                                            break
                                os.remove('C:/Users/ranamihir/Downloads/' + filename)
                                print(show + ' has been downloaded and saved in D:.')
                                break
                        print()
                    else:
                        print(show + ' has already been downloaded.')
                    # Safely quit browser
                    browser.quit()
    except Exception as e:
        print('\nError: ' + str(e))
        pass