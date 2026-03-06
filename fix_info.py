import os

file_path = r"c:\Users\ki770\OneDrive\Desktop\zakaz bot\bot.py"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Update Bog'lanish (approx lines 424-431)
for i in range(len(lines)):
    if 'if text == "📞 Bog\'lanish":' in lines[i]:
        lines[i+1] = '        await update.message.reply_text(\n'
        lines[i+2] = '            "📞 *Bog\'lanish:*\\n\\n"\n'
        lines[i+3] = '            "👨‍💻 Admin: @khusniddinkhamidov\\n"\n'
        lines[i+4] = '            "📢 Reklama bo\'yicha Admin: @TSH_Jamshidbek\\n"\n'
        lines[i+5] = '            "📱 Telefon: Telegram orqali yozing\\n\\n"\n'
        lines[i+6] = '            "Ish vaqti: 09:00 — 22:00",\n'
        lines[i+7] = '            parse_mode="Markdown"\n'
        lines[i+8] = '        )\n'

# Update Biz haqimizda (approx lines 434-442)
for i in range(len(lines)):
    if 'if text == "ℹ️ Biz haqimizda":' in lines[i]:
        lines[i+1] = '        await update.message.reply_text(\n'
        lines[i+2] = '            "ℹ️ *JAKHPRINT haqida:*\\n\\n"\n'
        lines[i+3] = '            "🌐 Veb-sayt yaratish\\n"\n'
        lines[i+4] = '            "🤖 Telegram bot ishlab chiqish\\n"\n'
        lines[i+5] = '            "🖨️ Print xizmatlari (vizitka, flayer, taklifnomalar)\\n\\n"\n'
        lines[i+6] = '            "👨‍💻 Asosiy Admin: @khusniddinkhamidov\\n"\n'
        lines[i+7] = '            "📢 Reklama Admini: @TSH_Jamshidbek\\n\\n"\n'
        lines[i+8] = '            "Biz bilan ishlaganingiz uchun rahmat! 🙏",\n'
        lines[i+9] = '            parse_mode="Markdown"\n'
        lines[i+10] = '        )\n'

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(lines)
