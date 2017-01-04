import requests
import pafy
from hurry.filesize import size
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
            print('Do you want to download a video or audio? (a/v)')
            download_content(video)
        else:
            print(link.string + ': FAILURE')
        video_number += 1
        if video_number > max_video_number:
            break
def download_content(video):
    type_of_file = input()
    if type_of_file == 'v' or type_of_file == 'a':
        type_string = 'video' if type_of_file == 'v' else 'audio'
        print('The ' + type_string + ' you are going to download is:\n' + video.title)
        print('\nDetails:\n\n' + 'Rating: ' + "%.1f" % video.rating + '\nView Count: ' + str(video.viewcount) + '\nAuthor: ' + video.author + '\nLength: ' + str(video.length) + ' seconds\nDuration: ' + str(video.duration) + '\nLikes: ' + str(video.likes) + '\nDislikes: ' + str(video.dislikes))
        print('\nDescription: ' + video.description)
        download_video(video) if type_of_file == 'v' else download_audio(video)
    else:
        print('Invalid input. Please try again:')
        download_content(video)

def download_video(video):
        best_video = video.getbest(preftype="mp4", ftypestrict=False)
        print('\nResolution of best video available: ' + best_video.resolution)
        print('\nFile size of best video available: ' + size(best_video.get_filesize()))
        print('\nAre you sure you want to continue with this download? (y/n)')
        check_response(best_video, 'v')

def download_audio(video):
        best_audio = video.getbestaudio(preftype="m4a", ftypestrict=False)
        print('\nBitrate of best audio available: ' + best_audio.bitrate)
        print('\nFile size of best audio available: ' + size(best_audio.get_filesize()))
        print('\nAre you sure you want to continue with this download? (y/n)')
        check_response(best_audio, 'a')

def check_response(best, type):
    response = input()
    if response == 'y':
        best.download(quiet=False, callback=show_progress)
        type_string = 'Video' if type == 'v' else 'Audio'
        print(type_string + ' downloaded successfully.')
    elif response == 'n':
        print('Download terminated.')
    else:
        print('Invalid input. Please try again:')
        check_response(best, type)

def show_progress(total, received, ratio, rate, eta):
    eta_string = " second" if int(eta) == 1 else " seconds"
    print("Progress: %.2f" % (ratio * 100) + "%" + "    Download Speed: " + str(int(rate)) + " kbps   ETA: " + str(int(eta)) + eta_string, end="\r")

trade_spider(1)