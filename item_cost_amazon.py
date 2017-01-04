# Checks price of an item on Amazon.in
from bs4 import BeautifulSoup
import requests
import smtplib

url = 'http://www.amazon.in/WD-Elements-Portable-External-Drive/dp/B008GS8LT0/ref=sr_1_2?ie=UTF8&qid=1464859010&sr=8-2&keywords=wd+my+passport+1+tb+external+hard+disk'
threshold_value = 3000

source_code = requests.get(url)
plain_text = source_code.text
soup = BeautifulSoup(plain_text, 'lxml')
name = soup.find('span', {'id': 'productTitle'}).text.replace('\n', '').strip(' ')
try:
    price = soup.find('span', {'id': 'priceblock_ourprice'}).text.strip(' ').replace(',', '').replace(u'\xa0', '').strip(' ')
except:
    price = soup.find('span', {'id': 'priceblock_saleprice'}).text.strip(' ').replace(',', '').replace(u'\xa0', '').strip(' ')
print('Price of ' + name + ' is: Rs.' + price)

if int(price) <= threshold_value:
        # Send mail
        sender_address = 'abc@gmail.com'
        receiver_address = 'xyz@gmail.com'
        message = 'The price for ' + name + ' -- Rs.' + price + ' is below your threshold value of Rs.' + str(threshold_value) + '.'

        # Credentials
        username = 'abc@gmail.com'
        password = '<password>'

        # The actual mail send
        try:
            server = smtplib.SMTP('smtp.gmail.com:587')
            server.starttls()
            server.login(username, password)
            server.sendmail(sender_address, receiver_address, message)
            server.quit()
            print('Message sent successfully.')
        except Exception as e:
            error = e.args[1]
            error = error[(error.index(' ')+1):]
            end = error.index('.')+1
            print('Falied to send message: ' + error[:end] + '(' + str(e.args[0]) + ')')