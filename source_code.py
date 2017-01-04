import requests
from bs4 import BeautifulSoup

def trade_spider():
    fw = open('bucky_code.text', 'w')
    url = 'https://www.thenewboston.com/forum/topic.php?id=1610'
    source_code = requests.get(url)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text, "lxml")
    for line in soup.find('code').text.split('    '):
        fw.write(line + '\n')
    fw.close()
trade_spider()
