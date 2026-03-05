# Zakaz Bot

Bu Telegram bot Instagram kanaldan kelgan foydalanuvchilar uchun zakazlarni qabul qiladi. Mijozlar xizmatlarni tanlab, tafsilotlarni kiritib zakaz berishlari mumkin.

## Xizmatlar
- Veb-sayt yaratish
- Bot yaratish (Telegram, Instagram, boshqa)
- Telegram bot yaratish
- Kichik print (vizetka, flayer, taklifnoma, A4 formatidagi barcha narsa)

## O'rnatish
1. Python 3.8+ o'rnating.
2. Kutubxonalarni o'rnating: `pip install -r requirements.txt`
3. `.env` faylida TELEGRAM_TOKEN ni BotFather'dan olingan token bilan almashtiring.
4. Botni ishga tushiring: `python bot.py`

## Ma'lumotlar bazasi
Zakazlar `orders.db` faylida saqlanadi (SQLite).

## Ishga tushirish
Bot ishga tushganda, foydalanuvchilar /start buyrug'i bilan boshlashlari mumkin.