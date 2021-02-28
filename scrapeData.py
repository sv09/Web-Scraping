# required libraries
import requests
from bs4 import BeautifulSoup
from bs4 import NavigableString
import csv
import pandas as pd

## global variables
#hashmaps to prevent duplicates
global table_map    
global list_map
#set to check if a url is already visited
global url_set

list_map={}
table_map={}
url_set= set()
flag=True


# helper function to split a word
def split(word):
    return [char for char in word] 

# helper function to check if a tag is preceded by string
def surrounded_by_strings(tag):
    if(tag != None):
        return (isinstance(tag.previous_element, NavigableString))

# helper function to get the index of the required header name from a table
def getHeaderIndex(tables):
    name_idx = None
    type_idx = None
    desc_idx = None
    for table in tables:
        head = table.find_all('th')
        i=0;
        for h in head:
            if(any (item in h.text.split() for item in ['name', 'Name', 'NAME', 'title', 'Title', 'TITLE'])):
                if(name_idx == None):
                    name_idx = i
                else:
                    pass
            if(any (item in h.text.split() for item in ['type', 'Type', 'TYPE'])):
                if(type_idx == None):
                    type_idx = i
                else:
                    pass
            if(any (item in h.text.split() for item in ['description', 'Description', 'DESCRIPTION'])):
                if(desc_idx == None):
                    desc_idx = i
                else:
                    pass
            i+=1;            
    return name_idx, desc_idx, type_idx
    
# function to extract data from a page that is arranged in table format
def getTableData(main, category):   
    tables = []
    h3=None
    h2=None
    temph3=None
    temph2=None
    update = None
    for i in main.find_all(True):
            if(i.has_attr('class') and i['class'][0] == 'mw-headline' and i.text == 'See also'):
                break
            if(i.name == 'table'):
                tables.append(i)
    name_idx, desc_idx, type_idx = getHeaderIndex(tables)
    for i in main.find_all(True):
        if(i.has_attr('class') and i['class'][0] == 'mw-headline' and i.text == 'See also'):
            break
        
        if(i.name == 'h3' and len(split(i.text.split()))>1):
            h3 = i.text.split('[')[0]
            
        if(i.name == 'h2' and len(split(i.text.split()))>1):
            h2 = i.text.split('[')[0]
            
        if(temph3 != h3):
            temph3 = h3
            update = h3
        if(temph2 != h2):
            temph2 = h2
            update = h2
        
        for tr in i.find_all('tr'):
            td = tr.find_all('td')
            row = [i.text for i in td]
            try:
                name = row[name_idx]
                name = name.replace('\n','')

                description = row[desc_idx]
                description = description.replace('\n','')
                
                if(type_idx != None):
                    dish_type = row[type_idx]
                    dish_type = dish_type.replace('\n','')
                else:
                    dish_type=update
                table_map[name] = [description, category, dish_type]
            except Exception as e:
                name = None
                description = None  
    return

# function to extract data from a page that is arranged in list format
def getListData(main, category):
    h3=None
    h2=None
    for i in main.find_all(True):
        if(i.has_attr('class') and i['class'][0] == 'mw-headline' and i.text == 'See also'):
            break
        
        if(i.name == 'h3'and len(split(i.text.split()))>1):
            h3 = i.text.split('[')[0]
            
        if(i.name == 'h2'and len(split(i.text.split()))>1):
            h2 = i.text.split('[')[0]
        
        if(h3 != None):
            dish_type = h3
        else:
            dish_type = h2
        
        for l in i.find_all('li'):
            try:
                ref = l.find('a')
            except Exception as e:
                ref = None
                
            if(surrounded_by_strings(ref)):
                pass
            else:
                try:
                    val = l.find('a')['href']
                    spl = val.split('/')
                    if(any (item in spl for item in ['wiki'])):
                        name = l.find('a')['title']
                        name = name.replace('\n','')
                        u = f'https://en.wikipedia.org/{val}'
                        if('File' not in u):
                            check=True
                            x=0
                            detail = requests.get(u)
                            data = BeautifulSoup(detail.content, 'html.parser')
                            cont = data.find('div', class_='mw-parser-output')
                            while(check):
                                description = cont.find_all('p')[x].get_text()
                                description = description.replace('\n','')
                                if(description):
                                    check=False
                                else:
                                    x+=1
                            if len(description) > 100:
                                description = description.partition('.')[0] + '.'
                            list_map[name] = [description, category, dish_type]
                except Exception as e:
                    u = None   
    return

# open a csv file and add headers
output_file = open('all_dishes.csv', 'w')
csv_writer = csv.writer(output_file)
csv_writer.writerow(['Category', 'Name', 'Type', 'Description'])


## Web Scrape

#starting url
url = 'https://en.wikipedia.org/w/index.php?title=Special:Search&limit=500&offset=0&ns0=1&search=List+of+dishes+AND+dishes&advancedSearch-current={}'

#loop through all the pages of links
while(flag):
    start = requests.get(url);
    itrList = BeautifulSoup(start.content, 'html.parser');
    for item in itrList.find_all('div', class_='mw-search-result-heading'):
        if('List' in item.a.text and any(i.lower() in item.a.text.split() for i in ['dishes', 'foods'])):
            cat = item.a.text.split('of')[1].strip()
            if(cat != 'prepared foods'):
                category = cat
                try:
                    val = item.find('a')['href']
                    url = f'https://en.wikipedia.org{val}'
                    if url not in url_set:
                        url_set.add(url)
                        page = requests.get(url)
                        soup = BeautifulSoup(page.content, 'html.parser')
                        main = soup.find('div', class_='mw-parser-output')
                        res='List'
                        for i in main.find_all(True):
                            if(i.has_attr('class') and i['class'][0] == 'mw-headline' and i.text == 'See also'):
                                break
                            if(i.name == 'table'):
                                res='Table'
                                break
                        if(res == 'Table'):
                            getTableData(main, category)
                        else:
                            getListData(main, category)
                except Exception as e:
                    pass
    #page iterator and break condition
    bottom_nav = itrList.find('p', class_='mw-search-pager-bottom')
    itr = [i.text for i in bottom_nav.find_all('a')]
    if 'next 500'in itr:
        flag = True
        link = bottom_nav.find('a', class_='mw-nextlink')['href']
        url = f'https://en.wikipedia.org/{link}'  
    else:
        flag = False

#write the data to csv file
for key in table_map:
    value = table_map[key]
    if(key != None and value[0] != None):
        csv_writer.writerow([value[1], key, value[2], value[0]])
        
for key in list_map:
    value = list_map[key]
    if(key != None and value[0] != None):
        csv_writer.writerow([value[1], key, value[2], value[0]])

# close the file
output_file.close()