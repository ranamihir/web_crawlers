import requests
import pafy
from hurry.filesize import size
from bs4 import BeautifulSoup

def trade_spider():
    print('Do you want to download a video or audio? (a/v)')
    download_content()

def download_content():
    type_of_file = input()
    if type_of_file == 'v' or type_of_file == 'a':
        type_string = 'video' if type_of_file == 'v' else 'audio'
        result = check_by_url_and_return_video(type_string)
        if result[1] == 'video':
            if result[0]:
                video = result[0]
                print('The ' + type_string + ' you are going to download is:\n' + video.title)
                print('\nDetails:\n\n' + 'Rating: ' + "%.1f" % video.rating + '\nView Count: ' + str(video.viewcount) + '\nAuthor: ' + video.author + '\nLength: ' + str(video.length) + ' seconds\nDuration: ' + str(video.duration) + '\nLikes: ' + str(video.likes) + '\nDislikes: ' + str(video.dislikes))
                print('\nDescription: ' + video.description)
                download_video(video) if type_of_file == 'v' else download_audio(video)
            else:
                print('Invalid search. Please try again.')
                trade_spider()
        else:
            if result[0]:
                videos = result[0]
                for video in videos:
                    download_video(video) if type_of_file == 'v' else download_audio(video)
            else:
                print('Invalid search. Please try again.')
                trade_spider()
    else:
        print('Invalid search. Please try again.')
        trade_spider()

def check_by_url_and_return_video(type):
    type_string = 'video' if type == 'v' else 'audio'
    print('Search:')
    query = input()
    if "playlist" not in query:
        url = 'https://www.youtube.com/results?search_query='
        for word in query.split():
            url += word + '+'
        source_code = requests.get(url[:len(url)-1])
        plain_text = source_code.text
        soup = BeautifulSoup(plain_text, "lxml")
        try:
            link = soup.find('a', {'class': 'yt-uix-sessionlink yt-uix-tile-link yt-ui-ellipsis yt-ui-ellipsis-2 spf-link '})
            try:
                video = pafy.new('https://www.youtube.com' + link['href'])
                return [video, 'video']
            except TypeError:
                print('No results found.')
                return [0, 'video']
        except ValueError:
            return [0, 'video']
    else:
        playlist_source_code = requests.get(query)
        playlist_plain_text = playlist_source_code.text
        playlist_soup = BeautifulSoup(playlist_plain_text, "lxml")
        playlist = pafy.get_playlist(query)
        print('\nYou are going to download ' + type_string + 's of the playlist:\n' + playlist['title'])
        print('\nAuthor: ' + playlist['author'])
        print('\nList of ' + type_string + 's:')
        for item in playlist['items']:
            print(item['pafy'].title)
        videos = []
        try:
            for link in playlist_soup.findAll('a', {'class': 'pl-video-title-link yt-uix-tile-link yt-uix-sessionlink  spf-link '}):
                try:
                    href = link['href']
                    videos.append(pafy.new('https://www.youtube.com' + href))
                except TypeError:
                    print('No results found.')
                    return [0, 'playlist']
            return [videos, 'playlist']
        except ValueError:
            return [0, 'playlist']

def download_video(video):
        best_video = video.getbest(preftype="mp4", ftypestrict=False)
        print('\nResolution of best video available: ' + best_video.resolution)
        print('\nFile size of best video available: ' + size(best_video.get_filesize()))
        best_video.download(quiet=False, callback=show_progress)
        print('Video downloaded successfully.')

def download_audio(video):
        best_audio = video.getbestaudio(preftype="m4a", ftypestrict=False)
        print('\nBitrate of best audio available: ' + best_audio.bitrate)
        print('\nFile size of best audio available: ' + size(best_audio.get_filesize()))
        best_audio.download(quiet=False, callback=show_progress)
        print('Audio downloaded successfully.')

def show_progress(total, received, ratio, rate, eta):
    eta_string = " second" if int(eta) == 1 else " seconds"
    print("Progress: %.2f" % (ratio * 100) + "%" + "    Download Speed: " + str(int(rate)) + " kbps   ETA: " + str(int(eta)) + eta_string, end="\r")

trade_spider()