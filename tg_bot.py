import logging
import re
from pathlib import Path

import telebot
from PIL import Image

import pytesseract

# from transformers import TrOCRProcessor, VisionEncoderDecoderModel

# from transformers import AutoProcessor, AutoModelForVision2Seq

# import easyocr

from config import TOKEN

# reader = easyocr.Reader(['ru'])

# processor = TrOCRProcessor.from_pretrained("raxtemur/trocr-base-ru")
# model = VisionEncoderDecoderModel.from_pretrained("raxtemur/trocr-base-ru")

# MODEL_NAME = "HuggingFaceM4/idefics2-8b"
# processor = AutoProcessor.from_pretrained(MODEL_NAME)
# model = AutoModelForVision2Seq.from_pretrained(MODEL_NAME).to("cpu")


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
        telebot.types.BotCommand('photo', 'отправить фото состава')
    ],
)


# def ocr_image(image_path):
#     image = Image.open(image_path).convert("RGB")
#     pixel_values = processor(image, return_tensors="pt").pixel_values
#     generated_ids = model.generate(pixel_values)
#     generated_text = processor.batch_decode(
#         generated_ids, skip_special_tokens=True)[0]
#     return generated_text


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

    # TrOCR:
    # text = ocr_image(file_name)
    # print(text)

    # easyOCR:
    # result = reader.readtext(file_name)
    # text = "\n".join([item[1] for item in result])

    # Idefics2
    # image = Image.open(file_name)

    # # Prepare inputs for the model
    # inputs = processor(images=image, return_tensors="pt").to(model.device)
    # # generated_ids = model.generate(inputs.input_ids, attention_mask=inputs.attention_mask)
    # generated_ids = model.generate(**inputs)
    # generated_texts = processor.batch_decode(generated_ids, skip_special_tokens=True)
    # text = generated_texts[0]

    text = re.sub(r'-\n', '', text)
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'\s-\s', ':', text)
    cleaned_text = re.sub(r'[^\w\s\-,\.;\:\(\)\[\]]', '', text)
    ingredients = [item.strip().lower()
                   for item in re.split(r'[,\.;\:\(\)\[\]]+', cleaned_text)]
    bot.reply_to(message, '\n'.join(ingredients))


@bot.message_handler(content_types=['text'])
def message_reply(message):
    log_message(message, message.text)
    bot.send_message(message.chat.id, 'Неизвестная команда')


bot.infinity_polling()
