from selenium import webdriver
from os.path import isfile, join
from urllib import request, error
import sys
import os
import time
import shutil


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
    return s.replace('\\', '').replace('/', ',').replace(':', ' -').replace('*', '').replace('?', '.').replace('\'', '\'').replace('<', '').replace('>', '').replace('|', '').strip('.')


courses = {
    'Shell Scripting Linux': 'https://citigroup.udemy.com/shell-scripting-linux/learn/v4/content',
    'Learning Python for Data Analysis and Visualization': 'https://citigroup.udemy.com/learning-python-for-data-analysis-and-visualization/learn/v4/content',
    'Data Analysis in Python with Pandas': 'https://citigroup.udemy.com/data-analysis-in-python-with-pandas/learn/v4/content',
    'Data Science: Deep Learning in Python': 'https://citigroup.udemy.com/data-science-deep-learning-in-python/learn/v4/content',
    'Build Web Apps with React JS and Flux': 'https://citigroup.udemy.com/learn-and-understand-reactjs/learn/v4/content',
    'Project Management Professional: Prep for PMP': 'https://citigroup.udemy.com/pmp-exam-prep-everything-you-must-know-to-pass-the-pmp-exam/learn/v4/content',
    'Master Project Risk Management - 5 PDUs': 'https://citigroup.udemy.com/project-risk-management-5-pdus/learn/v4/content',
    'Business Management - Organisational Culture Change Training': 'https://citigroup.udemy.com/business-create-organisational-culture-change/learn/v4/content',
    'Statistics for Management (MBA) - Foundation of Analytics': 'https://citigroup.udemy.com/statistics-by-example/learn/v4/content',
    'Learn and Understand AngularJS': 'https://citigroup.udemy.com/learn-angularjs/learn/v4/content',
    'Meteor and React for Realtime Apps': 'https://citigroup.udemy.com/meteor-react-tutorial/learn/v4/content',
    'AngularJS Crash Course for Beginners': 'https://citigroup.udemy.com/angularjs-crash-course-for-beginners/learn/v4/content',
    'The Complete Guide to Angular 2': 'https://citigroup.udemy.com/the-complete-guide-to-angular-2/learn/v4/content',
    'Learn Grunt with Examples: Automate Your Front End Workflow': 'https://citigroup.udemy.com/learn-grunt-automate-your-front-end-workflow/learn/v4/content',
    'Introduction to Unit Testing': 'https://citigroup.udemy.com/refactoru-intro-unit-test/learn/v4/content',
    'Advanced Node.js Development': 'https://citigroup.udemy.com/refactoru-adv-nodejs/learn/v4/content',
    'Build Web Apps Using EmberJS: The Complete Course': 'https://citigroup.udemy.com/build-web-apps-using-emberjs-the-complete-course/learn/v4/content',
    'Web Hosting 101: Get Your Website Live on the Web in No Time': 'https://citigroup.udemy.com/web-hosting-101/learn/v4/overview',
    'Learn MongoDB 3.0 and Rapidly Develop Scalable Applications':  'https://citigroup.udemy.com/mongodb-tutorial/learn/v4/content',
    'Real Estate Investing: Complete Investment Analysis': 'https://citigroup.udemy.com/real-estate-investment-analysis/learn/v4/content',
    'Financial Modeling: Build a Complete DCF Valuation Model': 'https://citigroup.udemy.com/learn-how-to-value-a-company-and-build-a-dcf-model/learn/v4/content',
    'Accounting 1 Simplified for You': 'https://citigroup.udemy.com/accounting-1-simplified-for-you/learn/v4/content',
    'Accounting 2 Simplified for You': 'https://citigroup.udemy.com/accounting-2-simplified-for-you/learn/v4/content',
    'Seeing the Big Picture: Understanding Financial Statements': 'https://citigroup.udemy.com/seeing-the-big-picture-financial-statements-made-easy/learn/v4/content',
    'CFA Level I Review Course - 2015 curriculum': 'https://citigroup.udemy.com/cfa-level-i-review-course-2015-curriculum/learn/v4/content',
    'CFA Level I Quantitative Methods Lectures': 'https://citigroup.udemy.com/cfa-level-i-quantitative-methods/learn/v4/content',
    'CFA Level I Financial Reporting and Analysis Lectures': 'https://citigroup.udemy.com/cfa-level-i-fra-lectures/learn/v4/content',
    'CFA Level I Foundation Course: Introduction to Quants': 'https://citigroup.udemy.com/cfa-foundation-quants/learn/v4/content',
    'CFA Level I Workshop 6: Alternatives, PM and Economics': 'https://citigroup.udemy.com/cfa-workshop-6/learn/v4/content',
    'Beginner to Pro in Excel: Financial Modeling and Valuation': 'https://citigroup.udemy.com/beginner-to-pro-in-excel-financial-modeling-and-valuation/learn/v4/content',
    'The Complete Ruby on Rails Developer Course': 'https://citigroup.udemy.com/the-complete-ruby-on-rails-developer-course/learn/v4/content'
}

browser = webdriver.Chrome('C:/Users/ranamihir/AppData/Local/Programs/Python/Python35-32/chromedriver.exe')
url = 'https://citigroup.udemy.com/'
browser.get(url)
username = browser.find_element_by_name('USER')
username.send_keys('<username>')
password = browser.find_element_by_name('PASSWORD')
password.send_keys('<password>')
submit = browser.find_element_by_class_name('ButtonSm')
submit.click()

for course in courses:
    total_files = 0
    while 1:
        # Initially store the names of all videos for each course
        indices = []
        index_count = 0
        names = []
        video_count = 1
        print('Storing names of videos of the course \'' + replace(course) + '\'...')
        url = courses[course]
        browser.get(url)
        time.sleep(20)
        tooltip_containers = browser.find_elements_by_class_name('tooltip-container')
        for tooltip_container in tooltip_containers:
            if tooltip_container.text == 'All Sections':
                tooltip_container.click()
                break
        time.sleep(5)
        items = browser.find_elements_by_class_name('lecture__item')
        for item in items:
            if item.find_element_by_class_name('lecture__item__link__time').text:
                names.append(replace(str(video_count) + '. ' + item.find_element_by_class_name('lecture__item__link__name').text.strip(' ')) + '.mp4')
                video_count += 1
                indices.append(index_count)
            index_count += 1
        print('Found ' + str(video_count-1) + ' videos.\n')

        # Delete 'Download Urls.txt' file if all videos haves been downloaded and move to next course
        course_path = 'C:/Users/ranamihir/Desktop/Udemy/' + replace(course) + '/'
        if not os.path.exists(course_path):
            os.makedirs(course_path)
        f = open(course_path + 'Download Urls.txt', 'a')
        if len(names) == total_files:
            f.close()
            print('All files of the course + \'' + replace(course) + '\'s have been downloaded.\nRemoving ' + f.name + '...')
            os.remove(f.name)
            break

        # Downloading all videos with proper names
        url = courses[course]
        video_count = 0
        print('Downloading videos of the course \'' + course + '\'...')
        for index in indices:
            try:
                if not os.path.exists(course_path + names[video_count]):
                    browser.get(url)
                    time.sleep(20)
                    tooltip_containers = browser.find_elements_by_class_name('tooltip-container')
                    for tooltip_container in tooltip_containers:
                        if tooltip_container.text == 'All Sections':
                            tooltip_container.click()
                            break
                    time.sleep(5)
                    videos = browser.find_elements_by_class_name('lecture__item__link')
                    video = videos[index]
                    video.click()
                    time.sleep(5)
                    div = browser.find_element_by_class_name('asset-container')
                    download_url = div.find_element_by_tag_name('div').find_element_by_tag_name('video').get_attribute('src')
                    f.write(names[video_count] + ':\t' + download_url + '\n')
                    print('File being downloaded:\t' + names[video_count])
                    try:
                        request.urlretrieve(download_url, course_path + names[video_count], reporthook)
                    except error.ContentTooShortError:
                        print('\nDownload Failed. Internet disconnected in between.')
                        os.remove(course_path + names[video_count])
            except Exception as e:
                print('\nDownload Failed. ' + str(e))
            finally:
                video_count += 1
        f.close()

        # Put videos in correct folders if all files have been downloaded
        num_files = len([f for f in os.listdir(course_path) if isfile(join(course_path, f))])
        if num_files == len(names) + 1:
            browser.get(url)
            time.sleep(20)
            print('Rearranging videos of the course \'' + course + '\' in correct folders...')
            tooltip_containers = browser.find_elements_by_class_name('tooltip-container')
            for tooltip_container in tooltip_containers:
                if tooltip_container.text == 'All Sections':
                    tooltip_container.click()
                    break
            time.sleep(5)
            sections = browser.find_elements_by_class_name('curriculum-navigation__section')
            global_video_count = 0
            section_titles = []
            for i, section in enumerate(sections):
                section_title = str(i+1) + '. ' + replace(section.find_element_by_class_name('curriculum-navigation__section__title').text.strip(' '))
                section_titles.append(section_title)
                print(section_title)
                try:
                    if not os.path.exists(course_path + section_title):
                        os.makedirs(course_path + section_title)
                except FileNotFoundError:
                    print('Could not create directory \'' + section_title + '\'. Directory path too long.')
                except Exception as e:
                    print('Rearranging Failed. ' + str(e))
                num_videos = 0
                items = section.find_elements_by_class_name('lecture__item')
                for item in items:
                    if item.find_element_by_class_name('lecture__item__link__time').text:
                        num_videos += 1
                local_video_count = 0
                while local_video_count < num_videos:
                    try:
                        shutil.move(course_path + names[global_video_count + local_video_count], course_path + section_title + '/' + names[global_video_count + local_video_count])
                    except FileNotFoundError:
                        print('Rearranging Failed. File path too long.')
                    except Exception as e:
                        print('Rearranging Failed. ' + str(e))
                    finally:
                        local_video_count += 1
                global_video_count += num_videos

            # Remove Empty folders
            for section_title in section_titles:
                try:
                    section_path = course_path + section_title
                    num_files = len([f for f in os.listdir(section_path) if isfile(join(section_path, f))])
                    total_files += num_files
                    if not num_files:
                        print('Removing empty directory \'' + section_title + '\'...')
                        os.rmdir(section_path)
                except Exception as e:
                    print(str(e))
        else:
            total_files = 0

    # Safely quit browser
    browser.quit()
