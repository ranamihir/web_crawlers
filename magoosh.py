from selenium import webdriver
from os.path import isfile, join
from urllib import request, error
import sys
import os


def reporthook(blocknum, blocksize, totalsize):
    readsofar = (blocknum * blocksize)
    if totalsize > 0:
        percent = min(readsofar * 1e2 / totalsize, 100.0)
        s = '\r%5.1f%% %*.2f mb / %.2f mb' % (
            percent, len(str(totalsize)), readsofar/(1024*1024), totalsize/(1024*1024))
        sys.stderr.write(s)
        if readsofar >= totalsize:
            sys.stderr.write('\n')
    else:
        sys.stderr.write('read %d\n' % (readsofar,))

def replace(s):
    return s.replace('\\', '').replace('/', ',').replace(':', ' -').replace('*', '').replace('?', '.').replace('<', '').replace('>', '').replace('|', '').strip('.')


browser = webdriver.Chrome('C:/Users/ranamihir/AppData/Local/Programs/Python/Python35-32/chromedriver.exe')
browser.get('https://gmat.magoosh.com/login')
username = browser.find_element_by_id('session_login')
username.send_keys('<email_id>')
password = browser.find_element_by_id('session_password')
password.send_keys('<password>')
submit = browser.find_element_by_id('session_submit_action')
submit.click()

course_path = 'D:/ranamihir/Desktop/MagooshGMAT/'
if not os.path.exists(course_path):
    os.makedirs(course_path)

browser.get('https://gmat.magoosh.com/lessons')

final_video_list = []
for i, section in enumerate(browser.find_elements_by_class_name('col-sm-11')):
    section_name = section.find_element_by_tag_name('h2').text

    section_path = course_path + str(i + 1) + '. ' + section_name + '/'
    if not os.path.exists(section_path):
        os.makedirs(section_path)

    subsection_paths = []
    subsections = section.find_elements_by_tag_name('h4')
    for j, subsection in enumerate(subsections):
        subsection_path = section_path + str(j + 1) + '. ' + subsection.text + '/'
        subsection_paths.append(subsection_path)
        if not os.path.exists(subsection_path):
            os.makedirs(subsection_path)

    for i, subsection in enumerate(section.find_elements_by_class_name('list-unstyled')):
        videos = subsection.find_elements_by_tag_name('li')
        for j, video in enumerate(videos):
            video_title = str(j + 1) + '. ' + replace(video.find_element_by_class_name('lesson-item-title').text) + '.mp4'
            video_url = video.find_element_by_tag_name('a').get_attribute('href')
            if 'Quiz' not in video_title:
                final_video_list.append([subsection_paths[i] + video_title, video_url])

for video in final_video_list:
    if not isfile(video[0]):
        browser.get(video[1])
        video_tag = browser.find_element_by_class_name('video')
        for source in video_tag.find_elements_by_tag_name('source'):
            if source.get_attribute('type') == 'video/mp4':
                download_url = source.get_attribute('src')
        try:
            print('Downloading ' + video[0] +'...')
            request.urlretrieve(download_url, video[0], reporthook)
        except error.ContentTooShortError:
            print('\nDownload Failed. Internet disconnected in between.')
            os.remove(video[0])
        except Exception as e:
            print('\nError: ' + str(e))

# Safely quit browser
browser.quit()