import requests
from bs4 import BeautifulSoup

data = requests.get('https://en.wikipedia.org/w/index.php?search=list+of+dishes&title=Special:Search&profile=advanced&fulltext=1&advancedSearch-current=%7B%7D&ns0=1')

# print(data.status_code)
# print(data.content)

soup = BeautifulSoup(data.content, 'html.parser')
print(soup.prettiyfy())