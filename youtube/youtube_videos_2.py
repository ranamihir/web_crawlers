import requests
import pafy
from bs4 import BeautifulSoup

def trade_spider(max_video_number):
    video_number = 1
    url = 'https://www.youtube.com'
    source_code = requests.get(url)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text, "lxml")
    for link in soup.findAll('a', {'class': 'yt-uix-sessionlink  yt-ui-ellipsis yt-ui-ellipsis-2 spf-link '}):
        if link['href']:
            href = link['href']
            video = pafy.new(url + href)
            best_video = video.getbest()
            best_video.download(filepath="/home/mihir/PycharmProjects/web_crawlers/")
        else:
            print(link.string + ': FAILURE')
        video_number += 1
        if video_number > max_video_number:
            break

trade_spider(5)