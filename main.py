import logging
import asyncio
import sqlite3

import stripe
from configure import config

from aiogram import (
    Bot,
    Dispatcher,
    types,
    html,
    Router,
    F,
    filters
)
from aiogram.types import (
    LabeledPrice,
    PreCheckoutQuery,
    Message,
    ContentType
)
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.formatting import Text, Bold
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# from aiogram.utils.executor import start_polling

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),  # логи будут храниться в этом файле
        logging.StreamHandler()  # Логи будут выводиться в консоль
    ]
)

logger = logging.getLogger(__name__)

bot = Bot(
    token=(config.bot_token.get_secret_value()),
)
provider_token = config.payment_provider_token.get_secret_value()
stripe.api_key = config.stripe_api_key.get_secret_value()

GROUP_ID = '-1001948401030'  # ID группы sun house

# Инициализация бота и диспетчера
dp = Dispatcher(storage=MemoryStorage())

# Подключение к базе данных
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS payments (user_id INTEGER PRIMARY KEY)''')
conn.commit()


# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} отправил команду /start")
    content = Text(
        "Добро пожаловать, ",
        Bold(message.from_user.full_name), ". Для доступа к группе, оплатите доступ с помощью /pay ."
    )
    await message.answer(
        **content.as_kwargs()
    )


# Обработчик команды /pay для старта процесса оплаты
@dp.message(Command("pay"))
async def cmd_pay(message: types.Message):
    title = "Оплата доступа"
    description = "Оплата за доступ к закрытой группе"
    payload = "Custom-Payload"
    currency = "EUR"
    price = 10 * 100  # цена в копейках
    prices = [LabeledPrice(label="Доступ", amount=price)]

    if provider_token.split(':')[1] == 'TEST':
        await bot.send_message(message.chat.id, "Тестовый платеж!")

    await bot.send_invoice(chat_id=message.chat.id,
                           title=title,
                           description=description,
                           payload=payload,
                           provider_token=provider_token,
                           currency=currency,
                           prices=prices)

# Обработчик предчеков (PreCheckoutQuery)
@dp.pre_checkout_query(lambda query: True)
async def pre_checkout_query(query: PreCheckoutQuery):
    if query.invoice_payload != 'Custom-Payload':
        await query.answer(ok=False, error_message="Что-то пошло не так...")
    else:
        await query.answer(ok=True)


# Обработчик успешной оплаты
# @router.message(F.SUCCESSFUL_PAYMENT)
@dp.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("INSERT OR REPLACE INTO payments (user_id) VALUES (?)", (user_id,))
    conn.commit()
    logger.info(f"Оплата от пользователя {user_id} успешнро завершена")
    await bot.send_message(message.chat.id,
                           f"Оплата на сумму {message.successful_payment.total_amount // 100} {message.successful_payment.currency} успешно завершена! Теперь отправьте команду /join, чтобы присоединиться к группе.")


@dp.message(Command("join"))
async def cmd_join(message: types.Message):
    user_id = message.from_user.id
    check = await bot.get_chat_member(GROUP_ID, user_id)
    cursor.execute("SELECT * FROM payments WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    if result and check:
        await bot.send_message(message.chat.id, f"You are already in this group")

    elif not result and check:
        try:
            invite_link = await bot.create_chat_invite_link(chat_id=GROUP_ID, member_limit=1)
            logger.info(f"Создана пригласительная ссылка для пользователя {user_id}")
            await message.answer(f"Ссылка на вступление в группу: {invite_link.invite_link}!")
            # await bot.revoke_chat_invite_link(chat_id=GROUP_ID, invite_link=invite_link.invite_link)
        except Exception as e:
            logger.error(f"Ошибка при создании пригласительной ссылки для пользователя {user_id}: {e}")
            await message.answer(
                f"Произошла ошибка при создании пригласительной ссылки. Пожалуйста попробуйте позже или обратитетсь к администратору @astro_lvica")
    else:
        logger.warning(f"Попытка присоединиться к группе без оплаты от пользователя {user_id}")
        await message.answer("Сначала необходимо оплатить доступ с помощью /pay.")


# @dp.message()
# async def catch_all_messages(message: types.Message):
#     logger.info(f"Получено сообщение: {message.text} от {message.from_user.id}")
#     await message.answer(f"Вы отправили: {message.text}")


async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
