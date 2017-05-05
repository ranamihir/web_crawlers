from selenium import webdriver
from os.path import isfile, join
from urllib import request, error
import sys
import os
import time


def reporthook(blocknum, blocksize, totalsize):
    readsofar = (blocknum * blocksize)
    if totalsize > 0:
        percent = min(readsofar * 1e2 / totalsize, 100.0)
        s = '\r%5.1f%% %*.2f mb / %.2f mb' % (
            percent, len(str(totalsize)), readsofar / (1024 * 1024), totalsize / (1024 * 1024))
        sys.stderr.write(s)
        if readsofar >= totalsize:
            sys.stderr.write('\n')
    else:
        sys.stderr.write('read %d\n' % (readsofar,))

tv_shows = {
    'Mad Men': {
        '1': 'https://fmovies.to/film/mad-men-1.y4xp',
        '2': 'https://fmovies.to/film/mad-men-2.x398',
        '3': 'https://fmovies.se/film/mad-men-3.w2v6'
    }
}

browser = webdriver.Chrome('<path_to_chromedriver>')

for show in tv_shows:
    for season in tv_shows[show]:
        while 1:
            # Downloading all episodes
            url = 'https://fmovies.to/'
            browser.get(tv_shows[show][season])
            season_name = show + ' - Season ' + season
            print('Downloading episodes of ' + season_name + '...')

            season_path = './FMovies/' + show + '/' + season_name + '/'
            if not os.path.exists(season_path):
                os.makedirs(season_path)

            # Check if all episodes have already been downloaded.
            episodes = browser.find_element_by_class_name('episodes').find_elements_by_tag_name('li')
            num_episodes = len(episodes)
            num_files = len([f for f in os.listdir(season_path) if isfile(join(season_path, f))])
            if num_episodes == num_files:
                print('All episodes of ' + season_name + ' have been downloaded.')
                break
            print(str(num_episodes - num_files) + ' episode(s) to be downloaded.')

            video_links = []
            download_urls = []
            indices = []

            # Store links of episodes not yet downloaded
            for i, episode in enumerate(episodes):
                filepath = season_path + show + ' S' + season.zfill(2) + 'E' + str(i + 1).zfill(2) + '.mp4'
                if not isfile(filepath):
                    video_link = episode.find_element_by_tag_name('a').get_attribute('href')
                    video_links.append(video_link)
                    indices.append(i + 1)

            # Download episodes
            video_count = 0
            for link in video_links:
                browser.get(link)
                browser.find_element_by_id('player').click()
                time.sleep(5)
                video = browser.find_element_by_class_name('jw-video')
                download_url = video.get_attribute('src')
                video.click()
                filepath = season_path + show + ' S' + season.zfill(2) + 'E' + str(indices[video_count]).zfill(2) + '.mp4'
                print('Downloading ' + show + ' S' + season.zfill(2) + 'E' + str(indices[video_count]).zfill(2) + '...')
                try:
                    request.urlretrieve(download_url, filepath, reporthook)
                except error.ContentTooShortError:
                    print('\nDownload Failed. Internet disconnected in between.')
                    os.remove(filepath)
                except Exception as e:
                    print(str(e))
                    os.remove(filepath)
                finally:
                    video_count += 1

# Safely quit browser
browser.quit()