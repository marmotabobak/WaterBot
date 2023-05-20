import yaml
import logging
from pathlib import Path
import argparse
import os

from aiogram import Bot, Dispatcher, types, executor
from sqlalchemy import select, func

from model import Config, Volume
from postgres import PostgresEngine


logging.basicConfig(
    format='[%(asctime)s | %(levelname)s]: %(message)s',
    datefmt='%m.%d.%Y %H:%M:%S',
    level=logging.INFO
)

parser = argparse.ArgumentParser()
parser.add_argument('--config', '-c', type=str, help='config path')
args = parser.parse_args()
config_path_str = args.config or os.environ.get('APP_CONFIG_PATH')

if config_path_str:
    config_path = Path(config_path_str).resolve()
    logging.info(f'Starting service with config {config_path}')
else:
    raise ValueError('App config path should be provided in -c argument')

with open(config_path) as f:
    data = yaml.safe_load(f)

config = Config.parse_obj(data)
logging.info(f'[x] Service started')

try:
    bot = Bot(token=config.telegram.tg_bot_api_token)
    dp = Dispatcher(bot)
    logging.info(f'[x] Telegram bot initialized')
except Exception:
    logging.error(f'[x] Error while initializing Telegram bot')
    raise

try:
    postgres_engine = PostgresEngine(config=config.db)
except Exception:
    logging.error(f'[x] Error while initializing Postgres engine')
    raise


@dp.message_handler(commands=['start', 'help'])
async def process_start_command(message: types.Message) -> None:
    markup = types.ReplyKeyboardMarkup()

    volume_buttons = []
    for volume in (0.1, 0.2, 0.5, 1.0):
        volume_buttons.append(types.KeyboardButton(str(volume)))

    markup.row(*volume_buttons)
    markup.add(types.KeyboardButton('Сегодня'))

    await message.answer('Давай жми на кнопку', reply_markup=markup)


@dp.message_handler(regexp='Сегодня')
async def view_my_costs(message: types.Message) -> None:
    output_text = 'Здесь будет отчет за сегодня'
    await message.answer(output_text)


@dp.message_handler(regexp=r'\d\.\d')
async def process_regular_message(message: types.Message):
    output_text = 'Здесь будет запись в БД'
    await message.answer(output_text)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
