import gspread
from google.oauth2.service_account import Credentials
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Google Sheets sozlamalari
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
client = gspread.authorize(creds)

# Google Sheet nomini kiriting
table = client.open("Mock Exam Registrations")

# Worksheetlar
cefr_sheet = table.worksheet("CEFR Registrations")  # CEFR ro‘yxati
ielts_sheet = table.worksheet("IELTS Registrations")  # IELTS ro‘yxati

# Telegram bot funksiyalari
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /start buyrug‘ini qayta ishlaydi. """
    reply_keyboard = [["CEFR Mock Imtihoni", "IELTS Mock Imtihoni"]]
    context.user_data.clear()
    await update.message.reply_text(
        "Assalomu alaykum! Qaysi imtihonga ro‘yxatdan o‘tmoqchisiz?", 
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Imtihon tanlash jarayonini boshqaradi. """
    text = update.message.text
    if text == "CEFR Mock Imtihoni":
        context.user_data["exam"] = "CEFR"
    elif text == "IELTS Mock Imtihoni":
        context.user_data["exam"] = "IELTS"
    else:
        await update.message.reply_text("Iltimos, berilgan variantlardan birini tanlang.")
        return
    
    context.user_data["step"] = "full_name"
    await update.message.reply_text("Iltimos, to‘liq ismingizni kiriting.")

async def handle_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Foydalanuvchidan to‘liq ismini qabul qiladi. """
    if context.user_data.get("step") != "full_name":
        await update.message.reply_text("Iltimos, /start tugmasini bosib, imtihonni tanlang.")
        return
    
    context.user_data["full_name"] = update.message.text
    context.user_data["step"] = "phone_number"
    
    phone_button = ReplyKeyboardMarkup(
        [[KeyboardButton("📞 Telefon raqamni yuborish", request_contact=True)]],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    await update.message.reply_text("Endi telefon raqamingizni yuboring:", reply_markup=phone_button)

async def handle_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Foydalanuvchidan telefon raqamini qabul qiladi. """
    if context.user_data.get("step") != "phone_number":
        await update.message.reply_text("Iltimos, /start tugmasini bosib, imtihonni tanlang.")
        return
    
    contact = update.message.contact
    if not contact:
        await update.message.reply_text("Iltimos, pastdagi tugma orqali telefon raqamingizni yuboring.")
        return
    
    full_name = context.user_data.get("full_name")
    phone_number = contact.phone_number
    exam = context.user_data.get("exam")
    
    if exam == "CEFR":
        cefr_sheet.append_row([full_name, phone_number])
    elif exam == "IELTS":
        ielts_sheet.append_row([full_name, phone_number])
    
    await update.message.reply_text(f"Tabriklaymiz! Siz {exam} imtihoniga ro‘yxatdan o‘tdingiz!")
    context.user_data.clear()

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /stop buyrug‘i ro‘yxatdan o‘tish jarayonini bekor qiladi. """
    context.user_data.clear()
    await update.message.reply_text("Ro‘yxatdan o‘tish bekor qilindi. Yangi ro‘yxatdan o‘tish uchun /start ni bosing.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /help buyrug‘ini boshqaradi. """
    await update.message.reply_text(
        "Mock imtihoniga ro‘yxatdan o‘tish uchun /start ni bosing va yo‘riqnomalarga amal qiling. \nRo‘yxatdan o‘tishni to‘xtatish uchun /stop buyrug‘idan foydalaning."
    )

def main():
    bot_token = "8192600685:AAG2Kxr8mTS81XRuWhNCwKRtn80yea4JhKQ"
    app = ApplicationBuilder().token(bot_token).build()
    
    # Buyruqlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stop", stop))
    
    # Imtihon tanlash va ro‘yxatdan o‘tish jarayonlari
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"CEFR Mock Imtihoni|IELTS Mock Imtihoni"), handle_choice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_full_name))
    app.add_handler(MessageHandler(filters.CONTACT, handle_phone_number))
    
    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
