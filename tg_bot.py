import logging
import re
from pathlib import Path

import telebot
from PIL import Image

import pytesseract

from config import TOKEN


Path('photos').mkdir(exist_ok=True)

ARROW_SYMBOL = '\u2198\uFE0F'

bot = telebot.TeleBot(TOKEN)

telebot.logging.basicConfig(filename='log.csv',
                            level=logging.INFO,
                            encoding='utf-8',
                            format=' %(asctime)s; %(levelname)s; %(message)s')

logger = telebot.logger
logger.setLevel(logging.INFO)

bot.set_my_commands(
    commands=[
        telebot.types.BotCommand('start', 'начало работы'),
        # telebot.types.BotCommand('photo', 'отправить фото состава')
    ],
)


def log_message(msg, txt):
    logger.info('%(chat_id)s; %(username)s; %(full_name)s; %(txt)s', {
        'chat_id': msg.chat.id,
        'username': msg.from_user.username,
        'full_name': msg.from_user.full_name,
        'txt': txt
    })


def get_ingredients(text):
    text = re.sub(r'[-–—]+\s*\|*\n+\s*', '', text)
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'\s[-–—]\s', ':', text)
    text = re.sub(r'^[eе][-–—]*(?=\d)', 'е', text)
    cleaned_text = re.sub(r'[^\w\s\-\–\—,\.;\:\(\)\[\]]', '', text)
    ingredients = [item.strip().lower()
                   for item in re.split(r'[,\.;\:\(\)\[\]]+', cleaned_text)]

    return ingredients


def find_partial_matches(list1, list2):
    matches = set()

    for elem1 in list1:
        for elem2 in list2:
            if elem1 in elem2:
                matches.add(elem2)

    return matches


def find_word_matches(list1, list2):
    matches = set()

    for word in list1:
        pattern = re.compile(rf'\b{word}\b')
        for item in list2:
            if pattern.search(item):
                matches.add(item)

    return matches


def get_reply(message, ingredients):
    with open('stoplist_forms_lg.txt', 'r', encoding='utf-8') as file:
        stoplist = [line.strip().lower()
                    for line in file.readlines() if line.strip()]

    with open('exceptions_sm_forms.txt', 'r', encoding='utf-8') as file:
        stoplist.extend([line.strip().lower()
                         for line in file.readlines() if line.strip()])

    with open('exceptions_md_forms.txt', 'r', encoding='utf-8') as file:
        stoplist.extend([line.strip().lower()
                         for line in file.readlines() if line.strip()])

    with open('exceptions.txt', 'r', encoding='utf-8') as file:
        stoplist.extend([line.strip().lower()
                         for line in file.readlines() if line.strip()])

    reply = f'Распознано слов/словосочетаний: {len(ingredients)}\n\n'

    # if matches := find_partial_matches(stoplist, ingredients):
    if matches := find_word_matches(stoplist, ingredients):
        sorted_matches_string = ',\n'.join(sorted(matches))
        reply += (
            f'К сожалению, в составе есть запрещенные ингредиенты:\n\n'
            f'`{sorted_matches_string}`'
        )
        log_message(message, f'result:\n{sorted_matches_string}')
    else:
        reply += 'Все ингредиенты в составе разрешены'
    return reply


@bot.message_handler(commands=['start'])
def start_message(message):
    log_message(message, message.text)
    with open('hello.md', 'r', encoding='utf-8') as file:
        hello_text = file.read()
    bot.send_message(message.chat.id, hello_text)


@bot.message_handler(commands=['photo'])
def photo_message(message):
    log_message(message, message.text)
    bot.send_message(
        message.chat.id,
        f'Пришлите фото для определения состава продуктов {ARROW_SYMBOL}'
    )


@bot.message_handler(content_types=['photo'])
def photo_reply(message):
    file_id = message.photo[-1].file_id
    log_message(message, file_id)
    file_info = bot.get_file(file_id)
    file_name = file_info.file_path
    downloaded_file = bot.download_file(file_name)
    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)

    text = pytesseract.image_to_string(Image.open(file_name), lang='rus')

    log_message(message, 'text:\n' + text)

    ingredients = get_ingredients(text)
    log_message(message, 'ingredients:\n' + '\n'.join(ingredients))
    reply = get_reply(message, ingredients)

    bot.reply_to(message, reply, parse_mode='MarkdownV2')


@bot.message_handler(content_types=['text'])
def message_reply(message):
    log_message(message, message.text)

    ingredients = get_ingredients(message.text)
    log_message(message, 'ingredients:\n' + '\n'.join(ingredients))
    reply = get_reply(message, ingredients)

    bot.reply_to(message, reply, parse_mode='MarkdownV2')


bot.infinity_polling()
