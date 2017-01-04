import requests
from bs4 import BeautifulSoup

def trade_spider(max_video_number):
    video_number = 20106
    while video_number < (max_video_number + 20106):
        url = 'https://www.thenewboston.com/videos.php?cat=98&video=' + str(video_number)
        source_code = requests.get(url)
        plain_text = source_code.text
        soup = BeautifulSoup(plain_text, "lxml")
        for title in soup.findAll('span', {'class': 'titles'}):
            name = title.string
            print(name)
        video_number += 1

trade_spider(48)