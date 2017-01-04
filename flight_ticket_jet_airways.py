# This script checks for a particular flight of jet airways, and sends an mail notifying about the price falling below a threshold value.
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import time
import smtplib

while 1:
    # Initialisation of variables
    month = 'MAY'
    date = '15'
    source = 'DEL'
    destination = 'BLR'
    departure = '11:45'
    threshold_value = 8000

    # Navigate to appropriate flight web page
    browser = webdriver.Chrome('C:/Users/ranamihir/AppData/Local/Programs/Python/Python35-32/chromedriver.exe')
    browser.get("http://www.jetairways.com/EN/IN/Home.aspx")
    label = browser.find_element_by_id("oneWay_trigger")
    label.click()
    source_airport = browser.find_element_by_id("ObeFlights1_autoOrigin_AutoText")
    source_airport.send_keys(source)
    source_airport.send_keys(Keys.ENTER)
    destination_airport = browser.find_element_by_id("ObeFlights1_autoDestination_AutoText")
    destination_airport.send_keys(destination)
    destination_airport.send_keys(Keys.ENTER)
    calendar = browser.find_element_by_id("txtStartDate")
    calendar.click()
    while 1:
        month_titles = [browser.find_element_by_class_name("ui-datepicker-group-first"), browser.find_element_by_class_name("ui-datepicker-group-last")]
        titles =  [month_titles[0].find_element_by_class_name("ui-datepicker-month").text, month_titles[1].find_element_by_class_name("ui-datepicker-month").text]
        if month not in titles:
            browser.find_element_by_class_name("ui-datepicker-next").click()
        else:
            break
    date_element = month_titles[titles.index(month)].find_element_by_link_text(date)
    date_element.click()
    submit_button = browser.find_element_by_id("ObeFlights1_btnBookOnline")
    submit_button.click()

    # Check for price of appropriate flight
    time.sleep(10)
    search_result = browser.find_element_by_class_name("search-result")
    flight_rows = search_result.find_elements_by_tag_name("li")
    flight_row = flight_rows[0]
    for row in flight_rows:
        try:
            departure_time = row.find_element_by_class_name("journey__time").text
            if departure_time == departure:
                flight_row = row
                break
        except NoSuchElementException:
            continue
    price_element = flight_row.find_element_by_class_name("fare-class__price")
    price = int(price_element.text[3:].replace(',', ''))
    print(price)
    time.sleep(10)
    try:
        browser.close()
    except:
        pass
    if price <= threshold_value:
        # Send mail
        sender_address = 'abc@gmail.com'
        receiver_address1 = 'xyz@gmail.com'
        receiver_address2  = 'pqr@gmail.com'
        message = 'The price for Jet Airways ' + source + '-' + destination + ' fight on ' + month + ' ' + date + ' has gone below INR ' + str(threshold_value) + '. Book it now!'

        # Credentials
        username = 'abc@gmail.com'
        password = '<password>'

        # The actual mail send
        try:
            server = smtplib.SMTP('smtp.gmail.com:587')
            server.starttls()
            server.login(username, password)
            server.sendmail(sender_address, receiver_address1, message)
            server.sendmail(sender_address, receiver_address2, message)
            server.quit()
            print("Message sent successfully.")
        except Exception as e:
            error = e.args[1].decode("utf-8")
            error = error[(error.index(' ')+1):]
            end = error.index('.')+1
            print("Falied to send message: " + error[:end] + '(' + str(e.args[0]) + ')')

    # Keep checking after every one hour
    time.sleep(3600)