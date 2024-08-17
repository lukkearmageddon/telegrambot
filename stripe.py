import stripe
from configure import config

stripe.api_key = config.stripe_api_key.get_secret_value()



# Webhook endpoint secret (можно получить в настройках Stripe)


# Обработчик команды /subscribe для создания подписки
@dp.message(Command("subscribe"))
async def subscribe(message: types.Message):
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='subscription',
        line_items=[{
            'price': 'price_id',  # Замените на ваш идентификатор плана
            'quantity': 1,
        }],
        success_url='https://yourdomain.com/success?session_id={CHECKOUT_SESSION_ID}',  # Замените на ваш URL
        cancel_url='https://yourdomain.com/cancel',  # Замените на ваш URL
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подписаться", url=session.url)]
    ])

    await message.answer("Для доступа к группе оформите подписку:", reply_markup=keyboard)


# Обработчик Webhook для управления доступом к группе
@dp.message(F.content_type == ContentType.WEBHOOK)
async def webhook_handler(request: types.Message):
    payload = request.body.decode('utf-8')
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)

        # Обработка события успешного платежа
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            customer_email = session['customer_email']

            # Здесь добавьте логику для добавления пользователя в группу
            # Возможно, вам нужно будет сопоставить email с user_id в Telegram

            # Пример добавления пользователя (замените user_id на фактический идентификатор):
            user_id = find_user_id_by_email(customer_email)  # Реализуйте функцию поиска
            invite_link = await bot.create_chat_invite_link(chat_id=GROUP_ID, member_limit=1)
            await bot.send_message(user_id, f"Спасибо за подписку! Вот ваша ссылка для вступления в группу: {invite_link.invite_link}")

        return '', 200

    except ValueError as e:
        # Недопустимое событие
        return 'Bad Request', 400
    except stripe.error.SignatureVerificationError as e:
        # Недопустимая подпись
        return 'Bad Request', 400


# Функция для поиска user_id по email (вам нужно реализовать эту функцию)
def find_user_id_by_email(email):
    # Реализуйте логику поиска пользователя в вашей базе данных по email
    return user_id

