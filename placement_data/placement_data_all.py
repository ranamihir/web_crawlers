# This is a script which download all placement data (branch-wise) from channel-i to one file.

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

# Login to channel-i
browser = webdriver.Chrome('<webdriver_path>') # Replace <webdriver_path> with path to your webdriver
browser.get('https://channeli.in/')
sign_in = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.ID, 'login')))
sign_in.click()
WebDriverWait(browser, 15).until(EC.presence_of_element_located((By.ID, 'login_dialog-div')))
browser.switch_to.frame(browser.find_element_by_id('login_dialog-iframe'))
username = WebDriverWait(browser, 1).until(EC.presence_of_element_located((By.NAME, 'username')))
username.send_keys('<username>') # Replace <username> with your username
password = WebDriverWait(browser, 1).until(EC.presence_of_element_located((By.NAME, 'password')))
password.send_keys('<password>') # Replace <password> with your password
submit = browser.find_element_by_id('sign_in_button').click()

# Open Placement Online Results page
browser.get('https://channeli.in/placement/results/branch/')

# Declare arrays to store aggregate stats (branch-wise)
branch_serials = []
degrees = []
branches = []
selected_students = []
stats_urls = []

# Store aggregate stats (branch-wise)
rows = browser.find_element_by_tag_name('tbody').find_elements_by_tag_name('tr')
for row in rows:
    cells = row.find_elements_by_tag_name('td')
    branch_serials.append(cells[0].text)
    degrees.append(cells[1].text)
    branches.append(cells[2].text)
    selected_students.append(int(cells[3].text))
    stats_urls.append(cells[4].find_element_by_tag_name('a').get_attribute('href'))

# Print total offers on campus
print('Total offers: ' + str(sum(selected_students)))

# Create 'Data' folder
if not os.path.exists('Data'):
    os.makedirs('Data')

# Create and open data file
filename = 'student_data.dat'
f = open('Data/' + filename, 'w+')

# Write all data to a .dat file stored in 'Data' folder
for branch_serial in branch_serials:
    print('\rDownloading file \'' + filename + '\' (' + branch_serial + '/' + str(len(branch_serials)) + ')', end='')
    s_no = int(branch_serial)-1

    # Open branch stats page
    browser.get(stats_urls[s_no])

    # Scrape data
    data_rows = WebDriverWait(browser, 15).until(EC.presence_of_element_located((By.TAG_NAME, 'tbody'))).find_elements_by_tag_name('tr')
    for data_row in data_rows:
        for data_cell in data_row.find_elements_by_tag_name('td')[1:]:
            f.write(data_cell.text + '|')
        f.write(branches[s_no] + '|')
        f.write(degrees[s_no])
        f.write('\n')

# Close student_data file
f.close()

# Open Company List
browser.get('https://channeli.in/placement/company/list/')

# Declare arrays to store company stats
company_serials = []
companies = []
company_urls = []
categories = []
eligible_branches_urls = []

# Store aggregate stats (branch-wise)
rows = browser.find_element_by_tag_name('tbody').find_elements_by_tag_name('tr')
for row in rows:
    cells = row.find_elements_by_tag_name('td')
    company_serials.append(int(cells[0].text))
    companies.append(cells[1].text)
    company_urls.append(cells[1].find_element_by_tag_name('a').get_attribute('href'))
    categories.append(cells[2].text)
    eligible_branches_urls.append(cells[4].text)

# Print total companies on campus
total_companies = str(len(company_serials))
print('Total companies: ' + total_companies)

# Create and open data file
filename = 'company_data.dat'
f = open('Data/' + filename, 'w+')

# Open any company stats page and scrape headers
browser.get(company_urls[0])
data_rows = WebDriverWait(browser, 15).until(EC.presence_of_element_located((By.TAG_NAME, 'tbody'))).find_elements_by_tag_name('tr')
for data_row in data_rows:
    f.write(data_row.find_elements_by_tag_name('td')[0].text + '|')
f.write('\n')

# Write all data to a .dat file stored in 'Data' folder
for company_serial in company_serials:
    print('\rDownloading file \'' + filename + '\' (' + str(company_serial) + '/' + total_companies + ')', end='')
    s_no = int(company_serial)-1

    # Scrape data
    browser.get(company_urls[s_no])
    data_rows = WebDriverWait(browser, 15).until(EC.presence_of_element_located((By.TAG_NAME, 'tbody'))).find_elements_by_tag_name('tr')
    for data_row in data_rows:
        if data_row.find_elements_by_tag_name('td')[1].text == '-':
            f.write(data_row.find_elements_by_tag_name('td')[1].text.replace('-', '') + '|')
        else:
            f.write(data_row.find_elements_by_tag_name('td')[1].text + '|')
    f.write('\n')

# Close company_data file
f.close()

# Safely quit browser
browser.quit()