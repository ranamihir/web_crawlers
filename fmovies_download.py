from selenium import webdriver
from urllib import request, error
from os import makedirs, path, listdir, remove
from os.path import isfile, join
import time
import sys

def reporthook(count, block_size, total_size):
    progress_size = int(count * block_size)
    if total_size > 0:
        global start_time
        if count == 0:
            start_time = time.time()
            return
        seconds = time.time() - start_time
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        speed = int(progress_size / (1024 * seconds))
        percent = min(float(count * block_size * 100 / total_size), 100.0)
        s = '\r%5.1f%% %*.2f MB / %.2f MB %5d KB/s\tTime elapsed: %d:%d:%s seconds' % (percent, len(str(total_size)), progress_size / (1024 * 1024), total_size / (1024 * 1024), speed, hours, minutes, str(int(seconds)).zfill(2))
        sys.stdout.write(s)
        sys.stdout.flush()
    else:
        sys.stderr.write('Read %d\n' % (progress_size,))

tv_shows = {
    'Mad Men': {
        '1': 'https://fmovies.to/film/mad-men-1.y4xp',
        '2': 'https://fmovies.to/film/mad-men-2.x398',
        '3': 'https://fmovies.se/film/mad-men-3.w2v6',
        '4': 'https://fmovies.to/film/mad-men-4.zjy2'
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
            print('\nDownloading episodes of ' + season_name + '...')

            season_path = './FMovies/' + show + '/' + season_name + '/'
            if not path.exists(season_path):
                makedirs(season_path)

            # Check if all episodes have already been downloaded.
            episodes = browser.find_element_by_class_name('episodes').find_elements_by_tag_name('li')
            num_episodes = len(episodes)
            num_files = len([f for f in listdir(season_path) if isfile(join(season_path, f))])
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
                    remove(filepath)
                except Exception as e:
                    print(str(e))
                    remove(filepath)
                finally:
                    video_count += 1

# Safely quit browser
browser.quit()