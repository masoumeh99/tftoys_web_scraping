import requests
from requests.api import options
from lxml import etree, html
from io import StringIO, BytesIO
import json
from xml.dom import minidom
import time

# to scrape data created by dynamic drop-down selection, I used selenium
from selenium import webdriver
from selenium.webdriver.support.ui import Select


country = 'au'
siteId = 590
siteUrl = 'https://www.tftoys.com.au/'

# I could not take all pictures with fetch 1, so I used fetch 2
fetchingType = 2

parser = etree.HTMLParser()


def remove_newline(name):
    converted_list = []
    for element in name:
        item = element.strip()
        if (item):
            converted_list.append(item)
    return converted_list


def fetch(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'}
    print('url =', url)
    try:
        res = requests.get(url, headers=headers, timeout=60)
        print(res)
        return res
    except Exception as e:
        print('Err =', e, '\n')


# since I did not use sitemap, i write a function to take urls of all categories
def getCategoryUrls():
    categories = ['https://www.tftoys.com.au/shop/']
    categoryUrls = []

    for url in categories:
        res = fetch(url)
        categoryUrls += onGetCategoryUrls(res.content)

    return categoryUrls[0]


def onGetCategoryUrls(html_content):
    categoryUrls = []

    doc = html.fromstring(html_content)
    ulTags = doc.xpath('//ul[@class="product-categories"]')

    for ultag in ulTags:
        categoryUrls.append(ultag.xpath('.//li/a/@href'))

    return categoryUrls


def getProductUrls(categoryUrls):
    links = []

    for url in categoryUrls:
        res = fetch(url)
        pUrls = onGetProductUrls(res.content)
        for pUrl in pUrls[0]:
            links.append(pUrl)

    return links


def onGetProductUrls(html_content):
    links = []

    doc = html.fromstring(html_content)
    ulTags = doc.xpath('//ul[contains(@class, "products columns")]')

    for ultag in ulTags:
        links.append(ultag.xpath(
            './/li/a[contains(@class, "button")]/@href'))

    return links


# scrape data which are created dynamically by selecting options from select tag
def dynamicDataScraper(driver, drop, options):
    price = {}
    description = {}
    meta = {}

    for option in options:

        try:
            drop.select_by_visible_text(f'{option}')
        except:
            pass

        try:
            price[f'{option}'] = driver.find_elements_by_xpath(
                '//span[@class="price"]/span/bdi')[0].text
        except:
            pass

        if price[f'{option}'] == '':
            try:
                price[f'{option}'] = driver.find_elements_by_xpath(
                    '//p[@class="price"]//span/bdi')[0].text
            except:
                pass

        try:
            description[f'{option}'] = driver.find_elements_by_xpath(
                '//div[@class="woocommerce-variation-description"]/p')[0].text
        except:
            pass

        availability = ''

        try:
            availability = driver.find_elements_by_xpath(
                '//button[contains(@class, "unavailable")]')
        except:
            pass

        try:
            availability = driver.find_elements_by_xpath(
                "//p[contains(@class, 'out-of-stock')]")
        except:
            pass

        if len(availability) == 0:
            meta[f'isNotAvailable {option}'] = False
        else:
            meta[f'isNotAvailable {option}'] = True

        time.sleep(2)

    time.sleep(2)

    return price, description, meta


def scrape(url, tree):
    title = ''
    try:
        title = tree.xpath(
            "//div[contains(@class, 'summary')]/h1[contains(@class, 'product_title')]/text()")
        title = remove_newline(title)
        title = ' \n'.join(title)
    except:
        pass
    if title == '':
        return

    oldPrice = ''
    try:
        oldPrice = ''
    except:
        pass

    brand = ''
    try:
        brand = 'tftoys'
    except:
        pass

    model = ''
    try:
        model = ''
    except:
        pass

    category = []
    try:
        for item in tree.xpath("//nav/a/text()")[2:]:
            category.append(item)
    except:
        pass

    pics = []
    try:
        for item in tree.xpath("//div[contains(@id, 'description')]//p//img/@src"):
            pics.append(item)
    except:
        pass

    details = ''
    try:
        for item in tree.xpath("//span[@class = 'humm-price']//text()"):
            details = f'humm price is {item}'
    except:
        pass

    colors = []
    try:
        colors = []
    except:
        pass

    sizes = []
    try:
        sizes = []
    except:
        pass

    meta = {}
    options = []

    try:
        options = tree.xpath(
            "//table[contains(@class, 'variations')]/tbody/tr/td[contains(@class, 'value')]/select/option/text()")[1:]
    except:
        pass

    # check if we have multiple options for a product or not
    if len(options) >= 1:
        price = {}
        description = {}

        chromeDriverPath = 'C:\webdrivers/chromedriver.exe'
        driver = webdriver.Chrome(chromeDriverPath)
        driver.get(url)

        try:
            element = driver.find_element_by_id('pa_preorder-payment')
        except:
            pass

        drop = Select(element)

        # scrape dynamic data
        price, description, meta = dynamicDataScraper(driver, drop, options)

    # if there are no options, we will scrape data as usual
    else:
        description = ''
        try:
            description = tree.xpath(
                "//div[contains(@class, 'description')]/h5/span/strong/text()")
        except:
            pass

        price = ''
        try:
            price = tree.xpath(
                "//p[contains(@class, 'price')]/span/bdi/text()")[0]
        except:
            pass

        availability = ''

        try:
            availability = tree.xpath(
                "//button[contains(@class, 'unavailable)]")
        except:
            pass

        try:
            availability = tree.xpath(
                "//p[contains(@class, 'out-of-stock')]")
        except:
            pass

        if len(availability) == 0:
            meta['isNotAvailable'] = False
        else:
            meta['isNotAvailable'] = True

    current_product = {
        'url': url,
        'description': description,
        'model': model,
        'category': category,
        'brand': brand,
        'title': title,
        'price': price,
        'oldPrice': oldPrice,
        'colors': colors,
        'sizes': sizes,
        'pics': pics,
        'details': details,
        'meta': meta,
        'currency': "AUD",
    }
    return current_product


# zzz
# test --------------------------------------------
# categoryUrls = getCategoryUrls()
# print('categoryUrls =', len(categoryUrls), categoryUrls[0:4])

# productUrls = getProductUrls(categoryUrls[:5])
# print('productUrls =', len(productUrls), productUrls[0:3])


productUrls = [
    # One option - isNotAvailable
    'https://www.tftoys.com.au/shop/3rd-party-transformers/newbrands/transarttoys-ta-bwm-05-4-mode-commander-24cm/',

    # # One option - isAvailable
    # 'https://www.tftoys.com.au/shop/3rd-party-transformers/newage-na/newage-na-h-2934-hephaestus/',

    # # 2 option - isAvailable & isAvailable
    # 'https://www.tftoys.com.au/shop/hasbro/studio-series/hasbro-studio-series-ss-86-movie-blurr/',

    # # 2 option - isAvailable & isNotAvailable
    # 'https://www.tftoys.com.au/shop/takara-tomy/generations-selects/takaratomy-generations-selects-volcanicus-set-of-5/',

    # # 2 option - isNotAvailable & isNotAvailable
    # 'https://www.tftoys.com.au/shop/3rd-party-transformers/iron-factory-if/ironfactory-if-ex-46-honekumoki/',

    # # no option - isNotAvailable
    # 'https://www.tftoys.com.au/shop/hasbro/platium-edition/hasbro-platium-edition-unicron/',

    # # no option - isAvailable
    # 'https://www.tftoys.com.au/shop/hasbro/studio-series/hasbro-studio-series-ss-50-roadbuster/',

]


count = 0
for url in productUrls:
    if count >= 1:
        break
    count += 1
    print(url)
    if fetchingType == 1:
        res = requests.get(url)
        print(res)
        tree = etree.parse(StringIO(res.text), parser)
    else:
        res = requests.post(
            'https://zmp4s6v1hd.execute-api.ap-southeast-2.amazonaws.com/dev/', json={'url': url})
        print(res)
        tree = etree.parse(StringIO(json.loads(res.text)['html']), parser)
    cp = scrape(url, tree)
    print(json.dumps(cp, sort_keys=True, indent=4))
