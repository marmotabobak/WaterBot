from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, BigInteger, Text, Integer, DateTime, BIGINT, Float
from pydantic import BaseModel
from typing import List


Base = declarative_base()


class TelegramUserConfig(BaseModel):
    tg_bot_user_id: int
    tg_bot_user_name: str


class TelegramConfig(BaseModel):
    tg_bot_api_token: str


class DatabaseConfig(BaseModel):
    host: str
    port: int
    user: str
    password: str
    db_name: str


class Config(BaseModel):
    db: DatabaseConfig
    telegram: TelegramConfig


class Volume(Base):
    __tablename__ = 'volume'
    __table_args__ = {'schema': 'water_bot'}

    id = Column('volume_id', BigInteger, quote=False, primary_key=True)
    amount = Column('volume_amount', Float, quote=False)
    ts = Column('volume_ts', DateTime, quote=False)
    user_telegram_id = Column('user_tg_id', BIGINT, quote=False)