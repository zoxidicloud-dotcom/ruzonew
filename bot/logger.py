"""
Bot loglari.

Fayllar (loyihaning ROOT papkasidagi logs/ ichida, avtomatik yaratiladi):
  - logs/bot.log    - barcha muhim voqealar (INFO va undan yuqori)
  - logs/error.log  - faqat xatoliklar (traceback bilan)

Foydalanuvchiga texnik xato ko'rsatilmaydi - u faqat shu fayllarga yoziladi.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)


def _build_logger() -> logging.Logger:
    log = logging.getLogger("gaming_bot")
    if log.handlers:
        return log

    log.setLevel(logging.INFO)
    log.propagate = False
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    bot_file = RotatingFileHandler(
        os.path.join(LOG_DIR, "bot.log"), maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    bot_file.setLevel(logging.INFO)
    bot_file.setFormatter(formatter)

    error_file = RotatingFileHandler(
        os.path.join(LOG_DIR, "error.log"), maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    error_file.setLevel(logging.ERROR)
    error_file.setFormatter(formatter)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)

    log.addHandler(bot_file)
    log.addHandler(error_file)
    log.addHandler(console)
    return log


logger = _build_logger()
