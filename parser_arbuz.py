import requests
from bs4 import BeautifulSoup
import json
import re
import sqlite3
import datetime

toplink = "https://arbuz.kz"
city1 = "nur-sultan"
city2 = "almaty"
headers = {
    "authority": "www.yeezysupply.com",
    "cache-control": "max-age=0",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36",
    "sec-fetch-dest": "document",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "accept-language": "en-US,en;q=0.9",
}

db = "/home/user200/python/services/parsers/arbuz.db"
postfix = "?available=0&sort=available%3A1%3B&limit=50&page="


class Product:
    name = str
    price = str
    link = str

    def __init__(self, name, price, link):
        self.name = name
        self.price = price
        self.link = link

    def __repr__(self):
        return str(self.__dict__)


# получение цен продуктов по категории
def getProducts(toplink, plink, headers, postfix):
    result = []
    pageCount = getProductPageCount(toplink, plink, headers, postfix)
    # print("page number for " + plink + " is " + str(pageCount))
    for i in range(1, pageCount + 1):
        # print("curlink is " + toplink + plink + postfix + str(i))
        response = session.get(toplink + plink + postfix + str(i), headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        # Find product list
        product_list = soup.find("div", class_="product-card-list")
        children = product_list.findChildren()
        for child in children:
            # get json via regexp
            r1 = re.findall(r":product='(.*)'", str(child))
            # load json
            y = json.loads(r1[0])

            name = y['name']
            price = y['priceActual']
            link = toplink + y['uri']
            product = Product(name, price, link)
            # print(name, price, link, product, "00")
            # print(product.__repr__())
            result.append(product)
    return result


# insert product to db
def addProduct(name, price, link, date, db):
    # create connection to DB
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS products(
    productid INT PRIMARY KEY,
    name TEXT,
    price TEXT,
    date TEXT,
    link TEXT);
    """
    )
    conn.commit()
    entry = (name, price, date, link)
    cur.execute("INSERT INTO products (name,price,date,link) VALUES (?,?,?,?)", entry)
    # print(entry[0], entry[1])
    conn.commit()


# получение количества страниц по категории продуктов
# точность иногда не совпадает на 1-2
def getProductPageCount(toplink, link, headers, postfix):
    response = session.get(toplink + link + postfix + "1", headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    li = soup.find_all("li", class_=re.compile("page-item"))
    if len(li) == 0:
        return 1
    return len(li) - 1


# Start
# get links of pages with items
session = requests.session()
response = session.get(toplink, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")
# get json via regexp
r1 = re.findall(r"Object.values\(({.*}}}})\)", str(soup))
# load json
y = json.loads(r1[0])
# fill links
links = []
for category in y:
    for subcategory in y[category]["children"]:
        links.append(y[category]["children"][subcategory]["uri"])

products = []
cnt = 0

for link in links:
    link = str(link).replace(city2, city1)
    products.append(getProducts(toplink, link, headers, postfix))
    # print("working with " + link + " (" + str(cnt) + " out of " + str(len(links)) + ")")
    cnt += 1

cnt = 0
for product in products:
    for item in product:
        addProduct(item.name, item.price, item.link, datetime.datetime.now(), db)
        cnt += 1
print(datetime.datetime.today().strftime('%Y-%m-%d'), "inserted number of rows:", cnt)

"""soup = BeautifulSoup(response.text, 'html.parser')
response = session.get('https://arbuz.kz/ru/almaty/catalog/cat/20118-hleb_vypechka?available=0&sort=available%3A1%3B&limit=50&page=1#/', headers=headers)
with open('page.txt', 'w+', encoding='utf-8') as f:
    f.write(str(soup))"""
