import vk_api
from vk_api import VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

import requests
import json
import random
import re
import os.path

#from test import urls_by_search
from test2 import bids_by_search, get_info, make_pdf

bot_id = '180616350'

def write_msg(user_id, message, attachment = '', keyboard = None):
    if not message:
        message = 'Нет информации'
    data = {'user_id': user_id, 'message': message, 'random_id': get_random_id()}
    if attachment:
        data['attachment'] = attachment
    if keyboard:
        data['keyboard'] = keyboard.get_keyboard()
    vk.method('messages.send', data)

def get_random_id():
    return random.getrandbits(31) * random.choice([-1, 1])

# API-ключ созданный ранее
token = "0f9d50bdad152a9d0154af95ef5a60eb2e8c95a155025bfdd552a9256fe0f195547fefab4f34c77121555"

# Авторизуемся как сообщество
vk = vk_api.VkApi(token=token)

# Работа с сообщениями
longpoll = VkLongPoll(vk)

books = {}
# Основной цикл
for event in longpoll.listen():
    # Если пришло новое сообщение
    if event.type == VkEventType.MESSAGE_NEW:
    
        # Если оно имеет метку для меня( то есть бота)
        if event.to_me:

            # Сообщение от пользователя
            text = event.text
            
            # логика ответа
            # print(event.__dict__)
            if text in books:
                source, book, bid = books[text]
                filename = 'books/{source}/{book}.pdf'.format(source=source, book=book)
                pdf = make_pdf(book, source, output=filename, bid=bid)
                if not pdf:
                    write_msg(event.user_id, 'Ошибка: Неизвестная ЭБС')
                    continue

                upload = VkUpload(vk)
                server_doc = vk.method('docs.getMessagesUploadServer', {'type': 'doc', 'peer_id': event.user_id})
                doc_file = {'file' : open(filename, 'rb')}
                answer = requests.post(server_doc['upload_url'], files=doc_file)
                data_json = json.loads(answer.content)
                server_save = vk.method('docs.save', {'file': data_json['file'], 'title': text, 'tags':'tag2'})
                attachment = f"doc{server_save['doc']['owner_id']}_{server_save['doc']['id']}"
                write_msg(event.user_id, 'Ваша книга', attachment)
            elif text == "привет":
                keyboard = VkKeyboard()
                keyboard.add_button('Поиск: как искать?', color=VkKeyboardColor.DEFAULT)
                write_msg(event.user_id, "Хай", keyboard=keyboard)
            elif text == "Поиск: как искать?":
                write_msg(event.user_id, "Для поиска введите: поиск *что ищете*\nНапример: поиск масич сети")
            elif text == "пока":
                write_msg(event.user_id, "Пока((")
            elif text == 'end':
                break
            elif re.match(r'^[Пп]оиск\s.*', text):
                search_string = re.search(r'^[Пп]оиск\s(.*)', text).group(1)
                #urls = urls_by_search(search_string, 10)


                bids = bids_by_search(search_string, 10)
                # print(bids)
                # print()
                keyboard = VkKeyboard(one_time=True)
                keyboard.add_button('Поиск: как искать?', color=VkKeyboardColor.DEFAULT)

                infos = {}
                for i in bids:
                    infos[i['bid']] = get_info(i['bid'])
                    if 'book' in i:
                        title = "{0} {1}".format(infos[i['bid']]['author'], infos[i['bid']]['name'])
                        books[title] = (i['source'], i['book'], i['bid'])
                        keyboard.add_line()
                        keyboard.add_button(title)
                write_msg(event.user_id, '\n\n'.join([val['to_str'] for _, val in infos.items()]), keyboard=keyboard)
            else:
                write_msg(event.user_id, f"Не поняла вашего ответа...")