import requests
import lxml
import lxml.html
import re
import os
from cairosvg import svg2pdf, svg2png
from fpdf import FPDF

header_pstu = {
    'Host': 'elib.pstu.ru',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate',
    'Referer': 'http://elib.pstu.ru/vufind/Search/Results?lookfor=%D0%B0%D0%BD%D0%B0%D0%BD%D0%B0%D1%81&type=AllFields&limit=25&sort=relevance',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache'
}

def bids_by_search(search: str, count: int):
    url_search = "http://elib.pstu.ru/vufind/Search/Results?lookfor={0}&type=AllFields&limit={1}&sort=relevance".format(search, count)
    page = requests.get(url_search).text.encode('utf-8')
    doc = lxml.html.document_fromstring(page)

    results = []

    for res in range(count):
        result = {}
        read_online_xpath = f'/html/body/main/article/section/div/div[1]/form/div[{res+2}]/div[2]/table/tr[1]/td[1]'
        book_link = doc.xpath(read_online_xpath+'/a/@href')
        if not book_link:
            print(book_link)
            continue
        bids_find = re.findall(r'/vufind/Record/(\w+)', book_link[0])
        
        result['bid'] = bids_find[0]
        link = doc.xpath(read_online_xpath+'/span/a/@href')
        if link:
            count_pages_query = requests.get('http://elib.pstu.ru{bid}/Description#tabnav'.format(bid=book_link[0]), headers=header_pstu).text.encode('utf-8')
            # print(link)
            with open('page.html', 'wb+') as f:
                f.write(count_pages_query)
                f.close()
            ids_pstu = re.findall(r'fDocumentId=(\d+)', link[0])
            ids_lan = re.findall(r'pl1_id=(\d+)', link[0])
            # print(ids_pstu, ids_lan)
            if ids_pstu:
                result['book'] = int(ids_pstu[0])
                result['source'] = 'pstu'
            elif ids_lan: 
                result['book'] = int(ids_lan[0])
                result['source'] = 'lan'

        results.append(result)
    return results

def whereCanFind(bid):
    url= 'http://elib.pstu.ru/Record/{0}/AjaxTab'.format(bid)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
        'Accept': '*/*',
        'Accept-Encoding':'gzip, deflate',
        'Accept-Language':'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Cache-Control'	:'max-age=0',
        'Connection':'keep-alive',
        'Content-Length':'12',
        'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
        'Host':'elib.pstu.ru',
        'Referer':'http://elib.pstu.ru/Record/{0}/Holdings'.format(bid),
        'X-Requested-With':'XMLHttpRequest',
    }
    data = {'tab':'holdings'}

    response = requests.post(url, data=data,headers=headers).text
    
    regAudit = r'(?<=\<\/i\>&nbsp;).*?(?=\<\/a\>)'
    regName = r'(?<=\<div class\=\"alert alert\-info\" role\=\"alert\"\>\<h4\>).*?(?= \<span)'

    audits = re.findall(regAudit, response)
    names = re.findall(regName, response)
    if audits and names:
        result = [{'aud': audits[i], 'audName': names[i] } for i in range(len(audits))]
    else:
        result = {}
    return result

def get_info(bid):
    #Get title+author
    
    urlBook = "http://elib.pstu.ru/Record/{0}/Holdings#tabnav".format(bid)
    pageBook = requests.get(urlBook).text.encode('utf-8')
    
    docBook = lxml.html.document_fromstring(pageBook)

    author_find = docBook.xpath('.//*[@property="author"]/a/text()')
    if author_find:
        author = ', '.join(author_find)
    else:
        author = 'нет информации'
    name_find = docBook.xpath('/html/body/main/article/section/div/div[2]/h2/text()')
    if name_find:
        name = name_find[0]
    else:
        name = 'нет информации'

    place_find = whereCanFind(bid)
    if place_find:
        places = '\n'.join(['\t{0} ({1})'.format(place['audName'], place['aud']) for place in place_find])
    else:
        places = '\tнет информации'
    book = {'bid':bid, 'author': author , 'name': name, 'places' : places}
    
    answer = 'Автор(ы): {0}\nНазвание: {1}\nГде найти:\n{2}\nСсылка:\n\t{3}\n\n'.format(book['author'], book['name'], places, urlBook)
    book['to_str'] = answer
    return book

def get_book_pstu(book_id: int, bid: str):
    print(book_id)
    header_referer = {'Referer': 'http://elib.pstu.ru/Record/{0}/Holdings'.format(bid)}

    url0 = "http://elib.pstu.ru/docview/?fDocumentId={id}".format(id=book_id)

    response = requests.get(url0, headers=header_referer).text.encode('utf-8')
    doc = lxml.html.document_fromstring(response)
    xpath_hash = '/html/head/script[8]/text()'
    with open('file.txt', 'w+') as f:
        f.write(doc.text)
        f.close()
    text = doc.xpath(xpath_hash)[0]
    hash_param = re.search(r'hash=\d+', text).group(0)
   
    url = "http://elib.pstu.ru/docview/pdf.php?id={id}&{hashcode}".format(id=book_id, hashcode=hash_param)

    response = requests.get(url).content
    return response

def make_pdf(book_id: int, source: str, count_pages: int = 10, output: str = '', bid: str = ''):
    print(book_id, source)
    if not output:
        if not os.path.exists('books/{source}'.format(source=source)):
            os.makedirs('books/{source}'.format(source=source))
        output = "books/{source}/{book_id}.pdf".format(source=source, book_id=book_id)
    if os.path.exists(output):
        return True

    if source == 'lan':
        header_lan = {
            'Host': 'fs1.e.lanbook.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0',
            'Accept': 'image/webp,*/*',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            # 'Cookie': '_ym_uid=1554291458895024437; _ym_d=1554291458; ice_unique_user_id=4ab7acd995f1bec6ece7843caf64294e5ca49b021fe6b4.84088336; _ym_isad=1; _ga=GA1.2.941592967.1559471217; _gid=GA1.2.1868796177.1559471217; _ym_visorc_6173539=w; PHPSESSID=ui36f1htksc6u03aet4cppopp7',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
        }

        url_pages = "https://fs1.e.lanbook.com/api/book/{id}/page/{page}/img".format(id=book_id, page='{page}')
        
        pdf = FPDF()
        if count_pages > 10:
            count_pages = 10
        headers_lan_book = header_lan
        headers_lan_book['Referer'] = f'https://e.lanbook.com/reader/book/{book_id}/'
        for page in range(1, count_pages + 1):
        
            # load and save svg
            response = requests.get(url_pages.format(page=page), headers=headers_lan_book)
            if response.status_code != 200:
                break
            svg2png(response.content, write_to='qwe/file.png', dpi=144)
            pdf.add_page()
            pdf.image('qwe/file.png' ,0,0,270,400)
        
        with open(output,'w+') as f:
            f.close()
        pdf.output(output, "F")
    elif source == 'pstu':
        pdf = get_book_pstu(book_id, bid)
        
        with open(output,'wb+') as f:
            f.write(pdf)
            f.close()
    else:
        return False
    return True
