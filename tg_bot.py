import logging
import re
from pathlib import Path

import telebot
import pytesseract
from PIL import Image

from config import TOKEN

Path('photos').mkdir(exist_ok=True)

ARROW_SYMBOL = '\u2198\uFE0F'

bot = telebot.TeleBot(TOKEN)

telebot.logging.basicConfig(filename='log.csv', level=logging.INFO, encoding='utf-8',
                            format=' %(asctime)s; %(levelname)s; %(message)s')

logger = telebot.logger
logger.setLevel(logging.INFO)

bot.set_my_commands(
    commands=[
        telebot.types.BotCommand('start', 'начало работы'),
        telebot.types.BotCommand('photo', 'отправить фото состава')
    ],
)


def log_message(msg, txt):
    logger.info('%(chat_id)s; %(username)s; %(full_name)s; %(txt)s', {
        'chat_id': msg.chat.id,
        'username': msg.from_user.username,
        'full_name': msg.from_user.full_name,
        'txt': txt
    })


@bot.message_handler(commands=['start'])
def start_message(message):
    log_message(message, message.text)
    bot.send_message(message.chat.id, 'Готов к работе!')


@bot.message_handler(commands=['photo'])
def photo_message(message):
    log_message(message, message.text)
    bot.send_message(
        message.chat.id, f'Пришлите фото для определения состава продуктов {ARROW_SYMBOL}')


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

    cleaned_text = re.sub(r'[^\w\s]', '', text)
    words = re.findall(r'\b\w+\b', cleaned_text)
    bot.reply_to(message, '\n'.join(words))


@bot.message_handler(content_types=['text'])
def message_reply(message):
    log_message(message, message.text)
    bot.send_message(message.chat.id, 'Неизвестная команда')


bot.infinity_polling()
