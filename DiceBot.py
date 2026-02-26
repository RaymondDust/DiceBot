import os
import logging
import random
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Загружаем переменные из .env (токен)
load_dotenv()

# Настраиваем логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Проверяем, что токен есть
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Токен не найден! Проверь файл .env или переменную окружения BOT_TOKEN.")

# ---- Функции-обработчики команд ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я кубик d20. Напиши /roll, чтобы бросить."
    )

async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    result = random.randint(1, 20)

    if result == 1:
        phrase = "💥 Критическая неудача! Всё пошло не по плану."
    elif result == 20:
        phrase = "🎉 Крит! Ты превзошёл ожидания!"
    elif 2 <= result <= 5:
        phrase = "😕 Плохо. Результат оставляет желать лучшего."
    elif 6 <= result <= 10:
        phrase = "🤔 Так себе. Могло быть и хуже, но и не хорошо."
    elif 11 <= result <= 15:
        phrase = "👍 Неплохо. Достойный результат."
    elif 16 <= result <= 19:
        phrase = "🌟 Отлично! Но до крита чуть-чуть не хватило."
    else:
        phrase = f"Выпало {result}. Судите сами."

    await update.message.reply_text(
        f"{user_name}, ты выбросил(а): **{result}**\n{phrase}",
        parse_mode='Markdown'
    )

# ---- Главная функция запуска ----
def main():
    # Создаём приложение (бота)
    application = Application.builder().token(TOKEN).build()

    # Регистрируем команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("roll", roll))

    # Запускаем бота
    logger.info("🚀 Бот запущен и готов к работе!")
    application.run_polling()

if __name__ == "__main__":
    main()