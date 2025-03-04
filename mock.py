import gspread
from google.oauth2.service_account import Credentials
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Google Sheets setup
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
client = gspread.authorize(creds)

# Replace with your Google Sheet name
sheet = client.open("Mock Exam Registrations")

# Get worksheet references
cefr_sheet = sheet.worksheet("CEFR Registrations")  # Replace with the tab name for CEFR
ielts_sheet = sheet.worksheet("IELTS Registrations")  # Replace with the tab name for IELTS

# Telegram Bot setup
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    reply_keyboard = [["CEFR Mock Exam", "IELTS Mock Exam"]]
    context.user_data.clear()  # Clear any previous session data
    await update.message.reply_text(
        "Welcome! Which exam would you like to register for?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles user's exam choice."""
    text = update.message.text
    print(f"User selected exam: {text}")  # Debugging line

    if text == "CEFR Mock Exam":
        context.user_data["exam"] = "CEFR"
        context.user_data["step"] = "register"  # Move to the registration step
        await update.message.reply_text(
            "Great! Please send your full name and phone number in this format:\nFull Name, Phone Number"
        )
    elif text == "IELTS Mock Exam":
        context.user_data["exam"] = "IELTS"
        context.user_data["step"] = "register"  # Move to the registration step
        await update.message.reply_text(
            "Great! Please send your full name and phone number in this format:\nFull Name, Phone Number"
        )
    else:
        await update.message.reply_text("Please select a valid option.")

async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles user registration details."""
    # Check if the user is in the registration step
    if context.user_data.get("step") != "register":
        await update.message.reply_text("Please choose an exam first by typing /start.")
        return

    text = update.message.text
    exam = context.user_data.get("exam")
    print(f"User input for registration: {text}")  # Debugging line

    # Process registration after the exam choice has been made
    if "," in text:
        try:
            full_name, phone_number = map(str.strip, text.split(",", 1))  # Ensure we split correctly
            print(f"Parsed Full Name: {full_name}, Phone Number: {phone_number}")  # Debugging line

            # Check if the phone number is valid (only digits)
            if not phone_number.isdigit():
                raise ValueError("Phone number should only contain digits.")
            
            # Append data to the correct sheet
            if exam == "CEFR":
                cefr_sheet.append_row([full_name, phone_number])
            elif exam == "IELTS":
                ielts_sheet.append_row([full_name, phone_number])
            
            await update.message.reply_text(f"Your details have been registered for the {exam} Mock Exam!")
            context.user_data.clear()  # Clear the exam choice after registration
        except ValueError as e:
            await update.message.reply_text(f"Invalid format! Please use:\nFull Name, Phone Number\nError: {str(e)}")
    else:
        await update.message.reply_text("Invalid format! Please use:\nFull Name, Phone Number")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /stop command."""
    # Clear user data to stop the registration process
    context.user_data.clear()

    await update.message.reply_text(
        "The registration process has been stopped. You can type /start to begin again."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /help command."""
    await update.message.reply_text(
        "To register for a mock exam, type /start and follow the instructions.\nTo stop the process, type /stop."
    )

def main():
    # Replace 'YOUR_BOT_TOKEN' with your Telegram bot token
    bot_token = "8192600685:AAG2Kxr8mTS81XRuWhNCwKRtn80yea4JhKQ"

    app = ApplicationBuilder().token(bot_token).build()

    # Add command and message handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stop", stop))  # Add stop handler

    # Handle exam choice first, then registration based on state
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"CEFR Mock Exam|IELTS Mock Exam"), handle_choice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_registration))  # Handle registration input

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
