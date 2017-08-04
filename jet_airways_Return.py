from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import sys

# Initialisation of variables
start_date = '15'
start_month = 'DECEMBER'
start_year = '2017'
end_date = '12'
end_month = 'JANUARY'
end_year = '2018'
source = 'DELHI'
destination = 'BLR'

# Navigate to appropriate flight web page
browser = webdriver.Chrome('C:/Users/ranamihir/AppData/Local/Programs/Python/Python35-32/chromedriver.exe')
browser.get("http://www.jetairways.com/EN/IN/Home.aspx")
label = browser.find_element_by_id("roundTrip__trigger")
label.click()

# Input source location
source_airport = browser.find_element_by_id("ObeFlights1_autoOriginHome_AutoText")
source_airport.click()
source_airport.send_keys(source + Keys.ENTER)

# Input destination location
destination_airport = browser.find_element_by_id("ObeFlights1_autoDestinationHome_AutoText")
destination_airport.click()
destination_airport.send_keys(destination + Keys.ENTER)

month_titles = []

# Set start date after checking validity
start_calendar = browser.find_element_by_id("txtStartDate")
start_calendar.click()
while 1:
    departureCalendar = browser.find_element_by_id('departureCalendar')
    current_first_year = departureCalendar.find_element_by_class_name("ui-datepicker-group-first").find_element_by_class_name('ui-datepicker-year').text
    if current_first_year == start_year:
        month_titles = [departureCalendar.find_element_by_class_name("ui-datepicker-group-first"), departureCalendar.find_element_by_class_name("ui-datepicker-group-last")]
        titles =  [month_titles[0].find_element_by_class_name("ui-datepicker-month").text, month_titles[1].find_element_by_class_name("ui-datepicker-month").text]
        if start_month not in titles:
            browser.find_element_by_class_name("ui-datepicker-next").click()
        else:
            break
    if current_first_year < start_year:
        departureCalendar.find_element_by_class_name("ui-datepicker-next").click()
    elif current_first_year > start_year:
        print('ERROR: Incorrect Start Year.')
        sys.exit(0)
start = month_titles[titles.index(start_month)].find_element_by_link_text(start_date)
start.click()

# Set end date after checking validity
end_calendar = browser.find_element_by_id("txtEndDate")
end_calendar.click()
while 1:
    returnCalendar = browser.find_element_by_id('returnCalendar')
    current_first_year = returnCalendar.find_element_by_class_name("ui-datepicker-group-first").find_element_by_class_name('ui-datepicker-year').text
    if current_first_year == end_year:
        month_titles = [returnCalendar.find_element_by_class_name("ui-datepicker-group-first"), returnCalendar.find_element_by_class_name("ui-datepicker-group-last")]
        titles =  [month_titles[0].find_element_by_class_name("ui-datepicker-month").text, month_titles[1].find_element_by_class_name("ui-datepicker-month").text]
        if end_month not in titles:
            browser.find_element_by_class_name("ui-datepicker-next").click()
        else:
            break
    elif current_first_year < end_year:
        returnCalendar.find_element_by_class_name("ui-datepicker-next").click()
    else:
        print('ERROR: Incorrect End Year.')
        sys.exit(0)
end = month_titles[titles.index(end_month)].find_element_by_link_text(end_date)
end.click()

# Submit query
submit_button = browser.find_element_by_id("ObeFlights1_btnBookOnline")
submit_button.click()