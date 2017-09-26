# This is a script that scrapes all the data from espncricinfo.com, based on user's input of class (Tests, ODI's, T20's,
# etc.) and type (Batting, Bowling, Fielding, etc.), and dumps all the data into a CSV file.
import requests
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

def spider(class_type, type):
    f = open(class_type + '_' + type + '.csv', 'w+')
    params = []
    url = 'http://stats.espncricinfo.com/ci/engine/stats/index.html?template=results;type=' + type + ';class=' + str(classes[class_type]) + ";page=1"
    while url:
        params = url.split(';')
        for item in params:
            if 'page' in item:
                print('\r' + item.capitalize(), end='')
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

class_type = input('Enter class:\n').lower().replace('\'', '')
type = input('Enter type:\n').lower()

spider(class_type, type)
