import os
import logging
import random
import json
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

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
        return {int(key): value for key, value in phrases.items()}
    except FileNotFoundError:
        logger.error("Файл phrases.json не найден! Использую стандартные фразы.")
        return {}
    except json.JSONDecodeError:
        logger.error("Ошибка в формате phrases.json! Использую стандартные фразы.")
        return {}

PHRASES = load_phrases()

# ========== ТОКЕН ==========
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Токен не найден! Проверь файл .env или переменную окружения BOT_TOKEN.")

# ========== РЕЖИМ МАСТЕРА ==========
GAME_MASTER_ID = 5484421795          # <-- ЗАМЕНИ НА СВОЙ ID (узнай командой /myid)
master_mode_active = False
master_bias = 0

# ========== ФУНКЦИИ-ОБРАБОТЧИКИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я кубик d20. Напиши /roll, чтобы бросить.\n"
        "Список команд — /help"
    )

async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    user_id = update.effective_user.id

    if master_mode_active:
        base = random.randint(1, 20)
        result = base + master_bias
        result = max(1, min(20, result))
    else:
        result = random.randint(1, 20)

    phrase = PHRASES.get(result)
    if not phrase:
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

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(f"Твой Telegram ID: `{user_id}`", parse_mode='Markdown')

async def cheat_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if GAME_MASTER_ID is not None and user_id == GAME_MASTER_ID:
        global master_mode_active
        master_mode_active = True
        await update.message.reply_text("🤫 Читерский режим ВКЛЮЧЁН! Тебе будут выпадать только высокие значения (15–20).")
    else:
        await update.message.reply_text("У вас нет прав для этой команды.")

async def cheat_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if GAME_MASTER_ID is not None and user_id == GAME_MASTER_ID:
        global master_mode_active
        master_mode_active = False
        await update.message.reply_text("😇 Читерский режим ВЫКЛЮЧЕН. Теперь всё честно.")
    else:
        await update.message.reply_text("У вас нет прав для этой команды.")

# ========== СКРЫТЫЕ КОМАНДЫ МАСТЕРА (через текстовые сообщения) ==========
async def secret_master_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GAME_MASTER_ID, master_mode_active, master_bias
    text = update.message.text.strip()
    user_id = update.effective_user.id

    if text == "!mastermode on":
        GAME_MASTER_ID = user_id
        master_mode_active = True
        master_bias = 0
        await update.message.reply_text("✅ Режим мастера активирован.\nИспользуй:\n!bias +5\n!bias -5\n!bias 0\n!mastermode off")
        return

    if master_mode_active and user_id == GAME_MASTER_ID:
        if text == "!mastermode off":
            master_mode_active = False
            GAME_MASTER_ID = None
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
            else:
                await update.message.reply_text("❌ Неверный формат. Пример: !bias +5")

# ========== КОМАНДА /help ==========
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_master = (GAME_MASTER_ID is not None and user_id == GAME_MASTER_ID)

    help_text = (
        "📚 *Доступные команды:*\n\n"
        "/start — приветственное сообщение\n"
        "/roll — бросить кубик d20\n"
        "/myid — узнать свой Telegram ID\n"
    )
    if is_master:
        help_text += (
            "\n🕵️ *Команды мастера:*\n"
            "/cheat_on — включить режим удачи (только для мастера)\n"
            "/cheat_off — выключить режим удачи\n"
            "\n🔐 *Скрытые команды мастера* (вводятся в чат с ботом как обычный текст):\n"
            "`!mastermode on` — активировать режим управления вероятностью\n"
            "`!bias +N` — увеличить вероятность высоких бросков (N от -5 до 5)\n"
            "`!bias -N` — увеличить вероятность низких бросков\n"
            "`!bias 0` — вернуть честный кубик\n"
            "`!mastermode off` — выключить режим мастера\n"
        )
    else:
        help_text += "\nℹ️ Если вы мастер, настройте переменную `GAME_MASTER_ID` в коде бота."

    help_text += (
        "\n📌 *Как добавить меню команд в Telegram:*\n"
        "1. Напишите @BotFather\n"
        "2. Отправьте команду /setcommands\n"
        "3. Выберите своего бота\n"
        "4. Отправьте список команд в формате:\n"
        "```\n"
        "start - Приветствие\n"
        "roll - Бросить кубик d20\n"
        "myid - Узнать свой ID\n"
        "```\n"
        "Если вы мастер, можете также добавить `cheat_on` и `cheat_off`, но это будет видно всем."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ========== ГЛАВНАЯ ФУНКЦИЯ ==========
def main():
    application = Application.builder().token(TOKEN).build()

    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("roll", roll))
    application.add_handler(CommandHandler("myid", myid))
    application.add_handler(CommandHandler("cheat_on", cheat_on))
    application.add_handler(CommandHandler("cheat_off", cheat_off))
    application.add_handler(CommandHandler("help", help_command))  # новая команда

    # Скрытые команды мастера (текстовые сообщения)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, secret_master_command))

    logger.info("🚀 Бот запущен и готов к работе!")
    application.run_polling()

if __name__ == "__main__":
    main()