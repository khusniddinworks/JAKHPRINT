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
SELECT_CATEGORY, SELECT_SUB, ENTER_DETAILS, CONFIRM_STATE = range(4)

# ── Menyu ma'lumotlari ───────────────────────────────
MAIN_BUTTONS = ["🌐 Veb-sayt", "🤖 Telegram Bot", "🖨️ Print xizmati"]
ADMIN_ONLY_BUTTONS = ["📊 Statistika", "📂 Excelni yuklab olish"]

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
    conn.commit()
    conn.close()

def save_to_db(user_id, username, category, service, details):
    conn = sqlite3.connect("orders.db")
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, username, category, service, details) VALUES (?,?,?,?,?)", (user_id, username, category, service, details))
    conn.commit()
    conn.close()

# ── Handlers ──────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    user = update.effective_user
    name = user.first_name or "Mehmon"
    
    msg = f"👋 *Assalomu alaykum, {name}!*\n\nQuyidagi xizmatlardan birini tanlang 👇"
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
    
    # Check for Admin buttons
    if user_id == ADMIN_ID:
        if text == "📊 Statistika":
            count = order_count()
            await update.message.reply_text(f"📊 Jami zakazlar soni: *{count} ta*", parse_mode="Markdown")
            return SELECT_CATEGORY
        elif text == "📂 Excelni yuklab olish":
            if os.path.exists(EXCEL_FILE):
                await update.message.reply_document(document=open(EXCEL_FILE, "rb"), filename="works.xlsx")
            else:
                await update.message.reply_text("❌ Fayl topilmadi.")
            return SELECT_CATEGORY

    if text not in MAIN_BUTTONS:
        return SELECT_CATEGORY

    context.user_data["category"] = text
    await update.message.reply_text(
        f"{text} bo'yicha yo'nalishni tanlang 👇",
        reply_markup=make_keyboard(SUB_BUTTONS[text], columns=1),
    )
    return SELECT_SUB

async def sub_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == "⬅️ Orqaga":
        return await start(update, context)

    category = context.user_data.get("category", "")
    if category and text in SUB_BUTTONS.get(category, []):
        context.user_data["service"] = text
        await update.message.reply_text(
            f"*{text}* tanlandi ✅\n\n✍️ Buyurtmangiz haqida batafsil yozing:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ENTER_DETAILS
    return SELECT_SUB

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
        
        # Dublikatdan himoya: agar ma'lumotlar bo'sh bo'lsa (allaqachon saqlangan), qaytadan saqlama
        if not category or not service:
            return SELECT_CATEGORY

        username = user.username or user.first_name

        # Ma'lumotlarni saqlashdan oldin xotirani tozalash (double-click oldini olish)
        context.user_data.clear()

        order_id = save_to_excel(user.id, username, category, service, details)
        save_to_db(user.id, username, category, service, details)

        # Adminni faqat tasdiqlanganda xabardor qilish
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
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, category_selected)],
            SELECT_SUB: [MessageHandler(filters.TEXT & ~filters.COMMAND, sub_selected)],
            ENTER_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_details)],
            CONFIRM_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_handler)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: start(u, c))],
        allow_reentry=True,
    )
    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()