import requests
from bs4 import BeautifulSoup

def trade_spider():
    fw = open('jet_airways.text', 'w')
    url = 'http://www.jetairways.com/EN/BH/jetprivilege/earn-JPMiles.aspx'
    source_code = requests.get(url)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text, "lxml")
    for table_data in soup.findAll('table', {'class': 'table table-bordered'}):
        if table_data.find('caption').text == 'Earning JPMiles on Jet Airways codeshare flights operated by partner airlines':
            i = 0
            for datum in table_data.findAll('span', {'class': 'info-text'}):
                if i % 2 == 0:
                    for letter in datum.text.split(','):
                        fw.write(letter)
                    fw.write('\n')
                i += 1

trade_spider()