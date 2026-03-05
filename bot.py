import logging
import sqlite3
import os
from datetime import datetime
from openpyxl import Workbook, load_workbook
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler,
    ConversationHandler, MessageHandler, filters, ContextTypes
)
from config import TELEGRAM_TOKEN, ADMIN_ID

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Fayl yo'li ───────────────────────────────────────
EXCEL_FILE = os.path.join(os.path.dirname(__file__), "works.xlsx")

# ── States ───────────────────────────────────────────
SELECT_CATEGORY, SELECT_SUB, ENTER_DETAILS, CONFIRM_STATE, BROADCAST_STATE = range(5)

# ── Menyu ma'lumotlari ───────────────────────────────
MAIN_BUTTONS = ["🌐 Veb-sayt", "🤖 Telegram Bot", "🖨️ Print xizmati"]
ADMIN_ONLY_BUTTONS = ["📊 Statistika", "📂 Excelni yuklab olish", "📢 Xabar yuborish"]

SUB_BUTTONS = {
    "🌐 Veb-sayt": [
        "📄 Landing page (1 sahifa)",
        "🗂️ Portfolio sayt",
        "🛒 Internet do'kon",
        "🏢 Korporativ sayt",
        "⚙️ Boshqa / Maxsus buyurtma",
        "⬅️ Orqaga",
    ],
    "🤖 Telegram Bot": [
        "💬 Oddiy chatbot",
        "📦 Zakaz bot (buyurtma qabul qilish)",
        "🍔 Bot + Veb (Fast-food / Do'kon)",
        "⚙️ Boshqa / Maxsus buyurtma",
        "⬅️ Orqaga",
    ],
    "🖨️ Print xizmati": [
        "💳 Vizitka",
        "📩 Taklifnoma",
        "📰 Flayer / Buklet",
        "🖼️ Banner / Poster",
        "📋 A4 formatdagi boshqa print",
        "⬅️ Orqaga",
    ],
}

CONFIRM_BUTTONS = ["✅ Tasdiqlash", "✏️ Tahrirlash", "❌ Bekor qilish"]


def make_keyboard(buttons: list, columns: int = 2) -> ReplyKeyboardMarkup:
    """Buttons ro'yxatidan ReplyKeyboardMarkup yasaydi."""
    rows = [buttons[i:i + columns] for i in range(0, len(buttons), columns)]
    return ReplyKeyboardMarkup(
        [[KeyboardButton(b) for b in row] for row in rows],
        resize_keyboard=True,
        is_persistent=True,
    )


CONFIRM_KB = make_keyboard(CONFIRM_BUTTONS, columns=1)


def get_main_keyboard(user_id):
    buttons = MAIN_BUTTONS.copy()
    if user_id == ADMIN_ID:
        buttons.extend(ADMIN_ONLY_BUTTONS)
    return make_keyboard(buttons, columns=2)


# ── Excel ─────────────────────────────────────────────
HEADERS = ["ID", "Sana", "User ID", "Username", "Kategoriya", "Xizmat", "Tafsilot"]

def init_excel():
    """Faylni tekshiradi va sarlavhalar yo'q bo'lsa qo'shadi."""
    if not os.path.exists(EXCEL_FILE):
        wb = Workbook()
        ws = wb.active
        ws.title = "Zakazlar"
        ws.append(HEADERS)
    else:
        wb = load_workbook(EXCEL_FILE)
        ws = wb.active
        # Agar fayl butkul bo'sh bo'lsa yoki birinchi qator sarlavha bo'lmasa
        if ws.max_row < 1 or (ws.cell(row=1, column=1).value != "ID" and ws.cell(row=1, column=1).value != "#"):
            # Faylni tozalab sarlavha qo'shish
            ws.delete_rows(1, ws.max_row)
            ws.append(HEADERS)
    
    # Ustun kengliklarini yangilash
    ws.column_dimensions["A"].width = 5
    ws.column_dimensions["B"].width = 20
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 15
    ws.column_dimensions["E"].width = 20
    ws.column_dimensions["F"].width = 35
    ws.column_dimensions["G"].width = 50
    wb.save(EXCEL_FILE)
    logger.info("✅ works.xlsx tayyor holatga keltirildi.")

def save_to_excel(user_id, username, category, service, details):
    wb = load_workbook(EXCEL_FILE)
    ws = wb.active
    last_row = ws.max_row
    next_id = 1
    if last_row > 1:
        val = ws.cell(row=last_row, column=1).value
        try: next_id = int(val) + 1
        except: next_id = last_row
    sana = datetime.now().strftime("%Y-%m-%d %H:%M")
    ws.append([next_id, sana, user_id, username, category, service, details])
    wb.save(EXCEL_FILE)
    return next_id

def order_count() -> int:
    wb = load_workbook(EXCEL_FILE)
    ws = wb.active
    return max(0, ws.max_row - 1)

def init_db():
    conn = sqlite3.connect("orders.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, category TEXT, service TEXT, details TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_seen DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()

def save_user(user_id, username, first_name):
    conn = sqlite3.connect("orders.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (user_id, username, first_name, last_seen) VALUES (?, ?, ?, CURRENT_TIMESTAMP)", (user_id, username, first_name))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect("orders.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def save_to_db(user_id, username, category, service, details):
    conn = sqlite3.connect("orders.db")
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, username, category, service, details) VALUES (?,?,?,?,?)", (user_id, username, category, service, details))
    conn.commit()
    conn.close()

# ── Handlers ──────────────────────────────────────────
async def keep_alive(context: ContextTypes.DEFAULT_TYPE):
    """Botni uxlamasligi uchun har 10 daqiqada getMe so'rovini yuboradi."""
    try:
        await context.bot.get_me()
        logger.info("❇️ Keep-alive: Bot faol.")
    except Exception as e:
        logger.error(f"Keep-alive xatosi: {e}")

async def set_bot_info(context: ContextTypes.DEFAULT_TYPE):
    """Botning tavsifini va ma'lumotlarini o'rnatadi."""
    try:
        # "What can this bot do?" qismi
        await context.bot.set_my_description(
            "🤖 Ushbu bot orqali Veb-sayt yaratish, Telegram botlar yasash va barcha turdagi Print xizmatlariga buyurtma berishingiz mumkin.\n\n"
            "👨‍💻 Admin: @khusniddinkhamidov"
        )
        # Qisqa tavsif
        await context.bot.set_my_short_description(
            "Veb-sayt, Bot va Print xizmatlari uchun rasmiy zakaz boti. Admin: @khusniddinkhamidov"
        )
        logger.info("✅ Bot tavsiflari o'rnatildi.")
    except Exception as e:
        logger.error(f"Bot ma'lumotlarini o'rnatishda xato: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    user = update.effective_user
    save_user(user.id, user.username, user.first_name)
    name = user.first_name or "Mehmon"
    
    msg = (
        f"👋 *Assalomu alaykum, {name}!*\n\n"
        "Men orqali veb-sayt, bot yoki print xizmatlariga zakaz berishingiz mumkin.\n\n"
        "👨‍💻 Admin bilan bog'lanish: @khusniddinkhamidov\n\n"
        "Quyidagi xizmatlardan birini tanlang 👇"
    )
    if user.id == ADMIN_ID:
        count = order_count()
        msg += f"\n\n👑 *Admin Panel:* Jami zakazlar: *{count} ta*"

    await update.message.reply_text(
        msg,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(user.id),
    )
    return SELECT_CATEGORY

async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user_id = update.effective_user.id
    
    # Admin tugmalarini tekshirish
    if user_id == ADMIN_ID:
        if text == "📊 Statistika":
            count = order_count()
            u_count = len(get_all_users())
            await update.message.reply_text(f"📊 *Statistika:*\n\n✅ Jami zakazlar: *{count} ta*\n👥 Jami foydalanuvchilar: *{u_count} ta*", parse_mode="Markdown")
            return SELECT_CATEGORY
        elif text == "📂 Excelni yuklab olish":
            if os.path.exists(EXCEL_FILE):
                await update.message.reply_document(document=open(EXCEL_FILE, "rb"), filename="works.xlsx")
            else:
                await update.message.reply_text("❌ Fayl topilmadi.")
            return SELECT_CATEGORY
        elif text == "📢 Xabar yuborish":
            await update.message.reply_text("📢 Barchaga yubormoqchi bo'lgan xabaringizni yozing (yoki /cancel):", reply_markup=ReplyKeyboardRemove())
            return BROADCAST_STATE

    if text not in MAIN_BUTTONS:
        return SELECT_CATEGORY

    context.user_data["category"] = text
    await update.message.reply_text(
        f"{text} bo'yicha yo'nalishni tanlang 👇",
        reply_markup=make_keyboard(SUB_BUTTONS[text], columns=1),
    )
    return SELECT_SUB

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Admin yozgan xabarni barcha foydalanuvchilarga yuboradi."""
    msg = update.message
    admin_id = update.effective_user.id
    
    if admin_id != ADMIN_ID:
        return SELECT_CATEGORY

    users = get_all_users()
    count = 0
    await update.message.reply_text(f"🚀 {len(users)} ta foydalanuvchiga xabar yuborish boshlandi...")

    for uid in users:
        try:
            await context.bot.copy_message(chat_id=uid, from_chat_id=admin_id, message_id=msg.message_id)
            count += 1
        except Exception:
            continue
    
    await update.message.reply_text(f"✅ Xabar {count} ta foydalanuvchiga yetkazildi.", reply_markup=get_main_keyboard(admin_id))
    return SELECT_CATEGORY

async def sub_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == "⬅️ Orqaga":
        return await start(update, context)

    category = context.user_data.get("category", "")
    if category and text in SUB_BUTTONS.get(category, []):
        context.user_data["service"] = text
        
        msg = f"*{text}* tanlandi ✅\n\n✍️ Buyurtmangiz haqida batafsil yozing:"
        if "Maxsus buyurtma" in text:
            msg += "\n\n💡 _Ushbu yo'nalishda buyurtmangizni *Ovozli xabar (Audio)* orqali ham yuborishingiz mumkin!_"
            
        await update.message.reply_text(
            msg,
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ENTER_DETAILS
    return SELECT_SUB

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ovozli xabarlarni qabul qilish va adminga yuborish."""
    service = context.user_data.get("service", "")
    if "Maxsus buyurtma" not in service:
        await update.message.reply_text("❌ Bu bo'limda faqat matnli xabar qabul qilinadi.")
        return ENTER_DETAILS

    user = update.effective_user
    username = user.username or user.first_name
    category = context.user_data.get("category", "")
    sana = datetime.now().strftime('%Y-%m-%d %H:%M')

    # Excel va DB ga saqlash
    order_id = save_to_excel(user.id, username, category, service, "Ovozli xabar yuborildi")
    save_to_db(user.id, username, category, service, "Ovozli xabar yuborildi")

    # Adminga audio va info yuborish
    admin_msg = (
        f"🎙 *YANGI OVOZLI BUYURTMA #{order_id}*\n\n"
        f"👤 *Mijoz:* {user.mention_markdown(name=username)}\n"
        f"🆔 *ID:* `{user.id}`\n"
        f"🗂 *Kategoriya:* {category}\n"
        f"📌 *Xizmat:* {service}\n"
        f"📅 *Sana:* {sana}"
    )
    
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")
        await context.bot.send_voice(chat_id=ADMIN_ID, voice=update.message.voice.file_id)
    except Exception as e:
        logger.error(f"Admin xabar yuborishda xato: {e}")

    await update.message.reply_text(
        "✅ *Ovozli buyurtmangiz qabul qilindi!*\nTez orada bog'lanamiz. 🙏",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(user.id),
    )
    return SELECT_CATEGORY

async def enter_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["details"] = update.message.text
    category = context.user_data.get("category", "")
    service  = context.user_data.get("service", "")

    await update.message.reply_text(
        f"📋 *Buyurtma ma'lumotlari:*\n\n"
        f"🗂 *Kategoriya:* {category}\n"
        f"📌 *Xizmat:* {service}\n"
        f"📝 *Tafsilot:* {update.message.text}\n\n"
        "Tasdiqlaysizmi?",
        parse_mode="Markdown",
        reply_markup=CONFIRM_KB,
    )
    return CONFIRM_STATE

async def confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user = update.effective_user
    
    if text == "✅ Tasdiqlash":
        category = context.user_data.get("category")
        service  = context.user_data.get("service")
        details  = context.user_data.get("details")
        
        if not category or not service:
            return SELECT_CATEGORY

        username = user.username or user.first_name
        context.user_data.clear()

        order_id = save_to_excel(user.id, username, category, service, details)
        save_to_db(user.id, username, category, service, details)

        admin_warning = (
            f"🔔 *YANGI TASDIQLANGAN BUYURTMA #{order_id}*\n\n"
            f"👤 *Mijoz:* {user.mention_markdown(name=username)}\n"
            f"🆔 *ID:* `{user.id}`\n"
            f"🗂 *Kategoriya:* {category}\n"
            f"📌 *Xizmat:* {service}\n"
            f"📝 *Tafsilot:* {details}\n"
            f"📅 *Sana:* {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_warning, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Admin xabar yuborishda xato: {e}")

        await update.message.reply_text(
            f"✅ *Buyurtmangiz qabul qilindi!*\nTez orada bog'lanamiz. 🙏",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(user.id),
        )
        return SELECT_CATEGORY
    elif text == "✏️ Tahrirlash":
        await update.message.reply_text("✏️ Yangi tafsilotlarni yozing:", reply_markup=ReplyKeyboardRemove())
        return ENTER_DETAILS
    else:
        await update.message.reply_text("❌ Bekor qilindi.", reply_markup=get_main_keyboard(user.id))
        return SELECT_CATEGORY

def main():
    init_db()
    init_excel()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Bot ma'lumotlarini o'rnatish
    app.job_queue.run_once(set_bot_info, when=0)
    # Anti-sleep: har 10 daqiqada bot o'zini "uyg'otadi"
    app.job_queue.run_repeating(keep_alive, interval=600, first=10)

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, category_selected)],
            SELECT_SUB: [MessageHandler(filters.TEXT & ~filters.COMMAND, sub_selected)],
            ENTER_DETAILS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_details),
                MessageHandler(filters.VOICE, voice_handler),
            ],
            CONFIRM_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_handler)],
            BROADCAST_STATE: [MessageHandler(filters.ALL & ~filters.COMMAND, broadcast_handler)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: start(u, c))],
        allow_reentry=True,
    )
    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()