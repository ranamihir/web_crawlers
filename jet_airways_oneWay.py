from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import sys

# Initialisation of variables
month = 'DECEMBER'
date = '15'
year = '2017'
source = 'DELHI'
destination = 'BLR'

# Navigate to appropriate flight web page
browser = webdriver.Chrome('C:/Users/ranamihir/AppData/Local/Programs/Python/Python35-32/chromedriver.exe')
browser.get("http://www.jetairways.com/EN/IN/Home.aspx")
label = browser.find_element_by_id("oneWay_trigger")
label.click()

# Input source location
source_airport = browser.find_element_by_id("ObeFlights1_autoOrigin_AutoText")
source_airport.click()
source_airport.send_keys(source + Keys.ENTER)

# Input destination location
destination_airport = browser.find_element_by_id("ObeFlights1_autoDestination_AutoText")
destination_airport.click()
destination_airport.send_keys(destination + Keys.ENTER)

month_titles = []

# Set date after checking validity
start_calendar = browser.find_element_by_id("txtStartDate")
start_calendar.click()
while 1:
    departureCalendar = browser.find_element_by_id('departureCalendar')
    current_first_year = departureCalendar.find_element_by_class_name("ui-datepicker-group-first").find_element_by_class_name('ui-datepicker-year').text
    if current_first_year == year:
        month_titles = [departureCalendar.find_element_by_class_name("ui-datepicker-group-first"), departureCalendar.find_element_by_class_name("ui-datepicker-group-last")]
        titles =  [month_titles[0].find_element_by_class_name("ui-datepicker-month").text, month_titles[1].find_element_by_class_name("ui-datepicker-month").text]
        if month not in titles:
            browser.find_element_by_class_name("ui-datepicker-next").click()
        else:
            break
    if current_first_year < year:
        departureCalendar.find_element_by_class_name("ui-datepicker-next").click()
    elif current_first_year > year:
        print('ERROR: Incorrect Year.')
        sys.exit(0)
start = month_titles[titles.index(month)].find_element_by_link_text(date)
start.click()

# Submit query
submit_button = browser.find_element_by_id("ObeFlights1_btnBookOnline")
submit_button.click()