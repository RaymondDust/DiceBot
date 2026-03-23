import os
import logging
import random
import json
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ========== ЗАГРУЗКА ПЕРЕМЕННЫХ ==========
load_dotenv()

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== ЗАГРУЗКА ФРАЗ ИЗ JSON ==========
def load_phrases():
    try:
        with open('phrases.json', 'r', encoding='utf-8') as f:
            phrases = json.load(f)
        return {int(k): v for k, v in phrases.items()}
    except FileNotFoundError:
        logger.error("Файл phrases.json не найден! Использую стандартные фразы.")
        return {}
    except json.JSONDecodeError:
        logger.error("Ошибка в формате phrases.json! Использую стандартные фразы.")
        return {}

PHRASES = load_phrases()

# ========== ПРОВЕРКА ТОКЕНА ==========
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Токен не найден! Проверь файл .env или переменную окружения BOT_TOKEN.")

# ========== НАСТРОЙКИ РЕЖИМА МАСТЕРА ==========
# ВСТАВЬ СВОЙ TELEGRAM ID ПОСЛЕ ПОЛУЧЕНИЯ ЧЕРЕЗ /myid
GAME_MASTER_ID = None   # Замени None на число, например 123456789

# Состояние режима мастера (меняется только мастером)
master_active = False
master_bias = 0          # смещение: от -5 до +5, влияет на все броски

# ========== ФУНКЦИИ-КОМАНДЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я кубик d20. Напиши /roll, чтобы бросить."
    )

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает ID пользователя (нужно для настройки мастера)"""
    user_id = update.effective_user.id
    await update.message.reply_text(f"Твой Telegram ID: `{user_id}`", parse_mode='Markdown')

async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name

    # Применяем режим мастера (если активен) ко ВСЕМ броскам
    if master_active:
        base = random.randint(1, 20)
        result = base + master_bias
        result = max(1, min(20, result))   # ограничиваем 1..20
    else:
        result = random.randint(1, 20)

    # Получаем фразу
    phrase = PHRASES.get(result)
    if not phrase:
        # запасные фразы (на случай, если нет JSON)
        if result == 1:
            phrase = "💥💥 Критическая неудача! Всё пошло не по плану.\nАтака: Атака промахнулась! Вместо атаки по врагу, ты нанёс себе малейший урон.\nДействие: Действие не удалось произвести, либо ты сделал его ужасно!"
        elif result == 20:
            phrase = "🎉🎉 Крит! Ты превзошёл ожидания!\nАтака: Ты поражаешь противника, нанося ему дополнительный урон!\nДействие: Действие проделано с первого раза и даже лучше, чем задумывалось!"
        elif 2 <= result <= 5:
            phrase = "😕 Очень плохо.\nАтака: Атака лишь чуть задела противника, нанеся маленький урон или вовсе не нанеся его.\nДействие: Действие произошло гораздо хуже, чем ты предполагал."
        elif 6 <= result <= 10:
            phrase = "🤔 Так себе.\nАтака: Атака прошла лишь вскользь, но всё равно нанесла урон, хоть и меньше.\nДействие: Твоё действие прошло хуже, чем предполагалось, произошла неудача."
        elif 11 <= result <= 15:
            phrase = "👍👍 Неплохо.\nАтака: Атака прошла чуть слабее, чем задумывалось.\nДействие: Действие просто получилось, ничего отрицательного или положительного."
        elif 16 <= result <= 19:
            phrase = "🌟🌟 Отлично! Это ещё не крит, но и не неудача.\nАтака: Ты просто поражаешь противника, никакого доп. урона.\nДействие: Действие проделано хорошо, без ошибок, но можно было и лучше."
        else:
            phrase = f"Выпало {result}. Судите сами."

    await update.message.reply_text(
        f"{user_name}, ты выбросил(а): **{result}**\n{phrase}",
        parse_mode='Markdown'
    )

# ========== СКРЫТЫЕ КОМАНДЫ МАСТЕРА (обрабатываются как обычные сообщения) ==========
async def secret_master_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текстовые сообщения (не команды) и реагирует на секретные команды мастера."""
    global master_active, master_bias
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # Если сообщение не от мастера — игнорируем
    if user_id != GAME_MASTER_ID:
        return

    # Секретные команды:
    if text == "!mastermode on":
        master_active = True
        master_bias = 0
        await update.message.reply_text("✅ Режим мастера активирован. Используй:\n!bias +5\n!bias -5\n!bias 0\n!mastermode off")
    elif text == "!mastermode off":
        master_active = False
        master_bias = 0
        await update.message.reply_text("🔒 Режим мастера деактивирован.")
    elif text.startswith("!bias"):
        parts = text.split()
        if len(parts) == 2:
            try:
                new_bias = int(parts[1])
                if -5 <= new_bias <= 5:
                    master_bias = new_bias
                    await update.message.reply_text(f"⚖️ Смещение вероятности установлено: {master_bias}")
                else:
                    await update.message.reply_text("❌ Допустимые значения: от -5 до 5")
            except ValueError:
                await update.message.reply_text("❌ Неверный формат. Пример: !bias +5")
    # Любые другие сообщения от мастера игнорируем

# ========== ГЛАВНАЯ ФУНКЦИЯ ЗАПУСКА ==========
def main():
    application = Application.builder().token(TOKEN).build()

    # Регистрация команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("roll", roll))
    application.add_handler(CommandHandler("myid", myid))

    # Обработчик скрытых команд мастера (реагирует на любые текстовые сообщения, не начинающиеся с /)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, secret_master_handler))

    # Запуск
    logger.info("🚀 Бот запущен и готов к работе!")
    application.run_polling()

if __name__ == "__main__":
    main()