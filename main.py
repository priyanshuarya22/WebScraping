import csv
import os

import requests
from bs4 import BeautifulSoup

URL = "https://www.amazon.in/s?k=bags&crid=2M096C61O4MLT&qid=1653308124&sprefix=ba%2Caps%2C283&ref=sr_pg_1"
BASE_URL = 'https://www.amazon.in'
header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.50'
}
params = {
    'api_key': os.environ.get('apiKey'),  # '4d9d18648c7e5b4ce5dcf9f0bf27bc23'
    'url': URL
}

# number of result pages scraped
counter = 1
# list of products
products = []
# scraping result pages
while counter <= 20:
    r = requests.get(url='http://api.scraperapi.com', headers=header, params=params)
    soup = BeautifulSoup(r.content, 'html5lib')
    try:
        # finding the div which contain the product information
        table = soup.find('div', attrs={'class': 's-main-slot s-result-list s-search-results sg-row'})
        # iterating over those divs
        for row in table.find_all('div', attrs={'class': 'a-section a-spacing-small a-spacing-top-small'}):
            product = {
                'url': BASE_URL + row.find('a', attrs={'class': 'a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal'})['href'],
                'name': row.find('span', attrs={'class': 'a-size-medium a-color-base a-text-normal'}).text,
                'price': row.find('span', attrs={'class': 'a-price-symbol'}).text + row.find('span', attrs={'class': 'a-price-whole'}).text,
                'rating': row.find('span', attrs={'class': 'a-icon-alt'}).text,
                'number_of_reviews': row.find('span', attrs={'class': 'a-size-base s-underline-text'}).text
            }
            products.append(product)
    except Exception as e:
        print(e)
    finally:
        counter += 1
        # url of next page
        params['url'] = BASE_URL + soup.find('a', attrs={'aria-label': 'Go to next page, page ' + str(counter)})['href']

for i in range(len(products)):
    try:
        product = products[i]
        params['url'] = product['url']
        r = requests.get(url='http://api.scraperapi.com', headers=header, params=params)
        soup = BeautifulSoup(r.content, 'html5lib')
        # finding the unordered list which contain description
        ul = soup.find('ul', attrs={'class': 'a-unordered-list a-vertical a-spacing-mini'})
        description = ''
        for li in ul.find_all('li'):
            description += li.text
        product['description'] = ' '.join(description.split())
        # finding the table which contain the asin
        table = soup.find('table', attrs={'id': 'productDetails_detailBullets_sections1'})
        for tr in table.find_all('tr'):
            if tr.th.text.strip() == 'ASIN':
                product['asin'] = tr.td.text.strip()
                break

        # function to recursively find the product description avoiding the images and scripts
        def product_description(div):
            divs = div.find_all('div')
            response = ''
            if divs:
                for div_child in divs:
                    output = product_description(div_child)
                    if output not in response:
                        response += output
            else:
                response = ' '.join(div.text.split())
            return response


        div = soup.find('div', attrs={'class': 'aplus-v2 desktop celwidget'})
        product['product_description'] = product_description(div)
        # finding the table which contains manufacturer
        table = soup.find('table', attrs={'id': 'productDetails_techSpec_section_1'})
        for tr in table.find_all('tr'):
            if tr.th.text.strip() == 'Manufacturer':
                product['manufacturer'] = tr.td.text.strip()
                break
        products[i] = product
    except Exception as e:
        print(e)

if products:
    filename = 'product_info.csv'
    fields = products[0].keys()
    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        writer.writerows(products)
print('Done')
