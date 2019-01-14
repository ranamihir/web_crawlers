'''
This script checks for jet airways round-trip flights, and sends an mail
notifying about the combined price falling below a set threshold value.
'''

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import time
import smtplib


while 1:
    # Initialization of variables
    source_date, target_date = '1', '10'
    source_month, target_month = 'JANUARY', 'JANUARY'
    source_year, target_year= '2019', '2019'
    source_city, target_city = 'DEL', 'BLR'
    source_departure_time, target_arrival_time = '15:10', '17:55'
    target_departure_time, source_arrival_time,  = '18:55', '21:55'
    departure_price_threshold, return_price_threshold = 8000, 4000

    # Navigate to appropriate flight web page
    browser = webdriver.Chrome()
    browser.maximize_window()
    browser.get('https://www.jetairways.com/EN/IN/home.aspx')
    label = browser.find_element_by_id('roundTrip__trigger')
    label.click()

    source_airport = browser.find_element_by_id('ObeFlights1_autoOriginHome_AutoText')
    source_airport.clear()
    source_airport.send_keys(source_city)
    source_airport.send_keys(Keys.ENTER)

    target_airport = browser.find_element_by_id('ObeFlights1_autoDestinationHome_AutoText')
    target_airport.clear()
    target_airport.send_keys(target_city)
    target_airport.send_keys(Keys.ENTER)

    info_dict = {
        'source': [source_date, source_month, source_year, 'departureCalendar'],
        'target': [target_date, target_month, target_year, 'returnCalendar']
    }

    for key in info_dict.keys():
        date, month, year, calendar_type = info_dict[key]
        calendar = browser.find_element_by_id(calendar_type)
        calendar.click()
        while 1:
            month_elements = [calendar.find_element_by_class_name('ui-datepicker-group-first'), \
                              calendar.find_element_by_class_name('ui-datepicker-group-last')]
            month_titles =  [month_elements[0].find_element_by_class_name('ui-datepicker-month').text, \
                             month_elements[1].find_element_by_class_name('ui-datepicker-month').text]
            year_titles =  [month_elements[0].find_element_by_class_name('ui-datepicker-year').text, \
                             month_elements[1].find_element_by_class_name('ui-datepicker-year').text]

            month_index = month_titles.index(month) if month in month_titles else -1
            year_index = year_titles.index(year) if year in year_titles else -1
            if not (month_index != -1 and year_index != -1 and month_index == year_index):
                calendar.find_element_by_class_name('ui-datepicker-next').click()
            else:
                break
        date_element = month_elements[month_index].find_element_by_link_text(date)
        date_element.click()

    submit_button = browser.find_element_by_id('ObeFlights1_btnBookOnline')
    submit_button.click()

    # Check for price of appropriate flight
    time.sleep(10)

    results_dict = {
        'departure': ['flight-matrix-0', source_departure_time, target_arrival_time, departure_price_threshold, 0],
        'return': ['flight-matrix-1', target_departure_time, source_arrival_time, return_price_threshold, 0]
    }

    for key in results_dict:
        result, flight_departure_time, flight_arrival_time, flight_price_threshold, _ = results_dict[key]
        search_result = browser.find_element_by_id(result).find_element_by_class_name('farematrix')
        flight_rows = search_result.find_elements_by_tag_name('li')
        flight_row = None
        for row in flight_rows:
            try:
                journey_info = row.find_element_by_class_name('farematrix-journey-info')
                departure_time = journey_info.find_element_by_class_name('left')\
                                             .find_element_by_class_name('journey__time').text
                arrival_time = journey_info.find_element_by_class_name('right')\
                                           .find_element_by_class_name('journey__time').text
                if departure_time == flight_departure_time and arrival_time == flight_arrival_time:
                    flight_row = row
                    break
            except NoSuchElementException:
                continue

        if not flight_row:
            print('{} flight not found.'.format(key.capitalize()))
            continue

        fare_bucket_container = flight_row.find_element_by_class_name('fare-bucket-container')\
                                          .find_elements_by_tag_name('li')
        for e in fare_bucket_container:
            if 'economy-class' in e.get_attribute('class'):
                economy_fare_bucket_container = e
                break
        assert economy_fare_bucket_container is not None, \
            'Could not find economy fare bucket container.'

        best_price = None
        for economy_class in economy_fare_bucket_container.find_elements_by_class_name('fare-class'):
            price_element = economy_class.find_element_by_class_name('price-wrap')
            if price_element.text.strip() == 'Sold Out' or best_price:
                continue
            for e in price_element.find_elements_by_xpath('*'):
                if 'price-striked' not in e.get_attribute('class'):
                    best_price = e.text
                    best_price = int(best_price.replace('INR', '').replace(',', '').strip())
                    print(best_price)
                    if best_price <= flight_price_threshold:
                        results_dict[key][-1] = 1
                    break

        if not best_price:
            print('All {} economy flights seem to be sold out.'.format(key))
            continue

    thresholds_passed = results_dict['departure'][-1]*results_dict['return'][-1]
    message_sent = 0
    if thresholds_passed:
        # Send mail
        sender_address = 'abc@gmail.com'
        receiver_address = 'xyz@gmail.com'
        subject = 'Jet Airways {}-{}'.format(source_city, target_city)
        text = 'The price for the Jet Airways {}-{} fight ({}-{}) on {} {}, {} has gone below INR {}'\
                  ' and for the {}-{} fight ({}-{}) on {} {}, {} has gone below INR {}. Book them now!'\
                  .format(source_city, target_city, source_departure_time, target_arrival_time, \
                          source_month, source_date, source_year, departure_price_threshold, \
                          target_city, source_city, target_departure_time, source_arrival_time, \
                          target_month, target_date, target_year, return_price_threshold)
        message = 'Subject: {}\n\n{}'.format(subject, text)

        # Credentials
        password = '<password>'

        # The actual mail send
        try:
            server = smtplib.SMTP('smtp.gmail.com:587')
            server.starttls()
            server.login(sender_address, password)
            server.sendmail(sender_address, receiver_address, message)
            server.quit()
            print('Message sent successfully.')
            message_sent = 1
        except Exception as e:
            print(str(e))

    # Keep checking after every one hour if message not sent
    if not message_sent:
        'Requirements not met. Checking again in 1 hour.'
        time.sleep(3600)
    else:
        browser.quit()
        break
