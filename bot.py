import logging
import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters
)

# Загрузка токена из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния диалога
SELECT_SERVICE, CAR_DETAILS, PROBLEM_DESCRIPTION, CONTACT_INFO, CONFIRM_BOOKING = range(5)

# Данные СТО
STO_NAME = "СТО Е95"
STO_ADDRESS = "Одесса, Дальницкое шоссе, 16"
STO_PHONE = "0672949352"
WORKING_HOURS = "Пн-Пт 9:00-19:00, Сб 10:00-15:00"


# Старт / Главное меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🛠 Консультация", "📅 Запись на сервис"],
        ["📞 Контакты", "ℹ️ О компании"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    user = update.effective_user
    await update.message.reply_html(
        f"<b>Добро пожаловать в {STO_NAME}, {user.first_name}!</b>\n\nЧем могу помочь?",
        reply_markup=reply_markup
    )


# Консультация: начало
async def start_consultation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Опишите проблему с вашим автомобилем:\n\n"
        "• Какие симптомы наблюдаете?\n"
        "• Когда появилась проблема?\n"
        "• Какая марка и модель авто?",
        reply_markup=ReplyKeyboardRemove()
    )
    return PROBLEM_DESCRIPTION


# Обработка описания проблемы
async def process_problem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    problem = update.message.text
    context.user_data['problem'] = problem

    await update.message.reply_html(
        f"Ваша проблема записана! Наш механик свяжется с вами в течение 15 минут.\n\n"
        f"<b>Ваше обращение:</b>\n{problem}\n\n"
        "Хотите записаться на диагностику?",
        reply_markup=ReplyKeyboardMarkup([["✅ Да", "❌ Нет"]], resize_keyboard=True)
    )
    return CONFIRM_BOOKING


# Обработка решения: запись или нет
async def process_booking_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    decision = update.message.text
    if decision == "✅ Да":
        return await start_booking(update, context)
    elif decision == "❌ Нет":
        await update.message.reply_text(
            "Хорошо! Если решите записаться позже, используйте кнопку «📅 Запись на сервис».",
            reply_markup=ReplyKeyboardMarkup([["🏠 Главное меню"]], resize_keyboard=True)
        )
        return ConversationHandler.END


# Начало записи
async def start_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    services = [
        ["🔧 Техническое обслуживание"],
        ["🛠 Диагностика", "🚗 Ремонт двигателя"],
        ["🔩 Ходовая часть", "⚡️ Электрика"]
    ]
    await update.message.reply_text(
        "Выберите тип услуги:",
        reply_markup=ReplyKeyboardMarkup(services, resize_keyboard=True)
    )
    return SELECT_SERVICE


# Выбор услуги
async def select_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['service'] = update.message.text
    await update.message.reply_text(
        "Введите данные автомобиля:\n\n• Марка и модель\n• Год выпуска\n• Пробег",
        reply_markup=ReplyKeyboardRemove()
    )
    return CAR_DETAILS


# Информация об авто
async def car_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['car_info'] = update.message.text
    await update.message.reply_text(
        "Введите ваши контактные данные:\n\n• Имя\n• Телефон\n• Удобное время связи"
    )
    return CONTACT_INFO


# Контактная информация
async def contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.text
    context.user_data['contact'] = contact

    summary = (
        f"<b>Запись подтверждена!</b>\n\n"
        f"<b>Услуга:</b> {context.user_data['service']}\n"
        f"<b>Авто:</b> {context.user_data['car_info']}\n"
        f"<b>Контакты:</b> {contact}\n\n"
        f"<b>Адрес:</b> {STO_ADDRESS}\n"
        f"<b>Телефон:</b> {STO_PHONE}\n\n"
        "Наш менеджер скоро с вами свяжется."
    )

    await update.message.reply_html(
        summary,
        reply_markup=ReplyKeyboardMarkup([["🏠 Главное меню"]], resize_keyboard=True)
    )
    logger.info(f"Новая заявка: {context.user_data}")
    return ConversationHandler.END


# О компании и контакты
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        f"<b>{STO_NAME}</b>\n\n"
        f"<b>Адрес:</b> {STO_ADDRESS}\n"
        f"<b>Телефон:</b> {STO_PHONE}\n"
        f"<b>Время работы:</b> {WORKING_HOURS}\n\n"
        "<b>Специализация:</b>\n"
        "• Комплексное ТО\n"
        "• Диагностика и ремонт\n"
        "• Электрика и подвеска\n"
        "• Работа с трансмиссией"
    )


# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Диалог отменён.",
        reply_markup=ReplyKeyboardMarkup([["🏠 Главное меню"]], resize_keyboard=True)
    )
    return ConversationHandler.END


# Основной запуск
def main():
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"^🛠 Консультация$"), start_consultation),
            MessageHandler(filters.Regex(r"^📅 Запись на сервис$"), start_booking)
        ],
        states={
            PROBLEM_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_problem)],
            CONFIRM_BOOKING: [MessageHandler(filters.Regex(r"^(✅ Да|❌ Нет)$"), process_booking_decision)],
            SELECT_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_service)],
            CAR_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_details)],
            CONTACT_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_info)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    # Команды и меню
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.Regex(r"^📞 Контакты$"), about))
    application.add_handler(MessageHandler(filters.Regex(r"^ℹ️ О компании$"), about))
    application.add_handler(MessageHandler(filters.Regex(r"^🏠 Главное меню$"), start))

    print("Бот запущен! Нажми Ctrl+C для остановки.")
    application.run_polling()


if __name__ == "__main__":
    main()