import yaml
import logging
from pathlib import Path
import argparse
import os
from datetime import datetime
from typing import Optional

from aiogram import Bot, Dispatcher, types, executor
from sqlalchemy import func

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
    for volume in (50, 100, 200, 500, 1000):
        volume_buttons.append(types.KeyboardButton(str(volume)))

    markup.row(*volume_buttons)
    markup.add(types.KeyboardButton('Сегодня'))

    await message.answer('Давай жми на кнопку', reply_markup=markup)


@dp.message_handler(regexp='Сегодня')
async def view_today_volume(message: types.Message) -> None:
    volume = drunk_today(message.from_user.id)
    if volume:
        output_text = f'За сегодня выпито: {volume}'
    elif volume == 0:
        output_text = 'Данных за сегодня нет'
    else:
        output_text = 'Ошибка получения данных =('
    await message.answer(output_text)


@dp.message_handler(regexp=r'\d{2,4}')
async def process_regular_message(message: types.Message):
    global postgres_engine

    try:
        amount = int(message.text)
    except Exception as e:
        amount = 0
        logging.error(e)

    if amount:
        try:
            session = postgres_engine.session()
            try:
                session.add(
                    Volume(
                        amount=amount,
                        ts=datetime.now(),
                        user_telegram_id=message.from_user.id
                    )
                )
                session.commit()
                output_text = f'Добавлено: {amount}'
                amount_today = drunk_today(message.from_user.id)
                if amount_today:
                    output_text += f'\nЗа сегодня выпито: {amount_today}'

            except Exception as e:
                raise e
            finally:
                session.close()
        except Exception as e:
            output_text = 'Ошибка в процессе сохранения данных =('
            logging.error(e)
    else:
        output_text = 'Ошибка в процессе обработки данных =('
    await message.answer(output_text)


def drunk_today(tg_user_id: int) -> Optional[int]:
    global postgres_engine

    try:
        session = postgres_engine.session()

        try:
            res = session.query(func.sum(Volume.amount)).where(
                Volume.ts >= datetime.now().strftime('%Y/%m/%d')
            ).where(
                Volume.user_telegram_id == tg_user_id
            ).scalar()
            print(res)
            return res if res else 0
        except Exception:
            raise
        finally:
            session.close()
    except Exception as e:
        logging.error(e)
        return None


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
