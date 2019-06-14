import requests
import lxml
import lxml.html
import re
import os
from cairosvg import svg2pdf, svg2png
from fpdf import FPDF

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
