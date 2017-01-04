import random
import urllib.requests

def download_web_image(url):
    name = random.randrange(1, 1000)
    full_name = str(name) + '.jpg'
    urllib.request.urlretrieve(url, full_name)

import requests
from bs4 import BeautifulSoup
def spider(max_pages):
    page = 1
    while page <= max_pages:
        url = 'https://www.quora.com/Aman-Srivastava-20/followers'
        source_code = requests.get(url)
        plain_text = source_code.text
        soup = BeautifulSoup(plain_text)
        for link in soup.findAll('img', {'class': 'profile_photo_img'}):
            href = link.get('src')
            print (href)
            download_web_image(href)
        page+=1
            
            
spider(1)
