# This is a script that scrapes all the data from espncricinfo.com, based on user's input of class (Tests, ODI's, T20's,
#  etc.) for all types (Batting, Bowling, Fielding, etc.), and dumps all the data into separate CSV files.
import requests
import os
from bs4 import BeautifulSoup

classes = {
    'tests': 1,
    'odis': 2,
    't20s': 3,
    'all': 11,
    'womens tests': 8,
    'womens odis': 9,
    'womens t20s': 10,
    'youth tests': 20,
    'youth odis': 21
}

def spider(class_type):
    types = ['batting', 'bowling', 'fielding', 'allround', 'fow', 'team', 'official', 'aggregate']
    for type in types:
        if not os.path.exists('Downloads'):
            os.makedirs('Downloads')
        f = open('Downloads/' + class_type + '_' + type + '.csv', 'w+')
        print('\nFor file ' + f.name + ':')
        params = []
        url = 'http://stats.espncricinfo.com/ci/engine/stats/index.html?template=results;type=' + type + ';class=' + str(classes[class_type]) + ";page=1"
        while url:
            params = url.split(';')
            for item in params:
                if 'page' in item:
                    print('\r\t' + item.capitalize(), end='')
                    break
            source_code = requests.get(url)
            plain_text = source_code.text
            soup = BeautifulSoup(plain_text, "html.parser")
            for row in soup.findAll('tr', {'class': 'data1'}):
                for cell in row.findAll('td'):
                    if row.td['class'] != 'padDD':
                        try:
                            f.write(cell.text + ',')
                        except:
                            pass
                f.write('\n')
            pagination_links = soup.find_all('a', {'class': 'PaginationLink'})
            if pagination_links:
                for link in pagination_links:
                    if link.text == 'Next \n':
                        url = 'http://stats.espncricinfo.com/' + link['href']
                        break
                    else:
                        url = None
            else:
                break
        f.close()
spider(input('Enter class:\n').lower().replace('\'', ''))
