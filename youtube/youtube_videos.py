import requests
import subprocess
import urllib.request
from bs4 import BeautifulSoup

def trade_spider(max_video_number):
    video_number = 1
    url = 'https://www.youtube.com'
    cmd = "youtube-dl -g ".split()
    source_code = requests.get(url)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text, "lxml")
    for link in soup.findAll('a', {'class': 'yt-uix-sessionlink  yt-ui-ellipsis yt-ui-ellipsis-2 spf-link '}):
        if link['href']:
            href = link['href']
            p = subprocess.check_output(cmd + [str(url + href)])
            video_url = p.decode("utf-8")
            urllib.request.urlretrieve(video_url, link.string + ".mp4")
        else:
            print(link.string + ': FAILURE')
        video_number += 1
        if video_number > max_video_number:
            break

trade_spider(1)