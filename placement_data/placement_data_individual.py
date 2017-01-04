# This is a script which download all placement data (branch-wise) from channel-i to separate files.

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
serials = []
degrees = []
branches = []
selected_students = []
stats_urls = []

# Store aggregate stats (branch-wise)
rows = browser.find_element_by_tag_name('tbody').find_elements_by_tag_name('tr')
for row in rows:
    cells = row.find_elements_by_tag_name('td')
    serials.append(cells[0].text)
    degrees.append(cells[1].text)
    branches.append(cells[2].text.replace('&', 'and'))
    selected_students.append(cells[3].text)
    stats_urls.append(cells[4].find_element_by_tag_name('a').get_attribute('href'))

total_files = str(len(serials))
print(str(total_files) + ' files will be downloaded.\n')

# Write all data to .dat files stored in a 'Data' folder
for serial in serials:
    s_no = int(serial)-1
    browser.get(stats_urls[s_no])
    filename = serial + '. ' + branches[s_no] + ' (' + degrees[s_no] + ').dat'
    print('Downloading file '+ str(s_no+1) + '/' + total_files + ': \'' + filename + '\'')

    if not os.path.exists('Data'):
        os.makedirs('Data')
    f = open('Data/' + filename, 'w+')
    data_rows = WebDriverWait(browser, 15).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'tr')))
    for data_row in data_rows:
        data_cells = data_row.find_elements_by_tag_name('td')
        for data_cell in data_row.find_elements_by_tag_name('td'):
            f.write(data_cell.text + '|')
        f.write('\n')
    f.close()

# Safely quit browser
browser.quit()