"""
bot.py — Telegram bot for the Timely Date Extractor
Receives images, PDFs, text messages, and email files from Telegram,
runs them through dateExtractor.py, and replies with the found dates.

Setup:
    1. pip install python-telegram-bot
    2. Create a bot via @BotFather on Telegram and get your token
    3. Paste your token in BOT_TOKEN below
    4. Run: python bot.py
"""

from datetime import datetime
import json
import os
import tempfile
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from dateExtractor import DateExtractor

# ─────────────────────────────────────────
# PASTE YOUR BOT TOKEN FROM @BotFather HERE
BOT_TOKEN = "8443448673:AAGPwcGdf18RWQVT1hZYU1WiqTCLPp5B-jI"
# ─────────────────────────────────────────


# File to store saved dates
SAVED_DATES_FILE = "saved_dates.json"


def load_saved_dates():
    """Load previously saved dates from JSON file"""
    if os.path.exists(SAVED_DATES_FILE):
        with open(SAVED_DATES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_date_to_file(event_name, date):
    """Append a new date to the saved dates JSON file"""
    saved = load_saved_dates()
    saved.append({
        'event_name': event_name,
        'date': date,
        'saved_at': datetime.now().isoformat()
    })
    with open(SAVED_DATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(saved, f, indent=2, ensure_ascii=False)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *Timely — Date Extractor*!\n\n"
        "Send me:\n"
        "📄 PDF file\n"
        "🖼 Image (JPG, PNG, etc.)\n"
        "📧 Email file (.eml)\n"
        "💬 Plain text\n\n"
        "If I find multiple dates, you can choose which ones to save!\n\n"
        "Commands:\n"
        "/saved - View all saved dates\n"
        "/clear - Clear all saved dates",
        parse_mode="Markdown"
    )


async def view_saved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all saved dates"""
    saved = load_saved_dates()
    if not saved:
        await update.message.reply_text("📭 No dates saved yet.")
        return

    lines = ["📅 *Your Saved Dates:*\n"]
    for i, item in enumerate(saved, 1):
        lines.append(f"{i}. *{item['event_name']}* — `{item['date']}`")
    
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def clear_saved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear all saved dates"""
    if os.path.exists(SAVED_DATES_FILE):
        os.remove(SAVED_DATES_FILE)
    await update.message.reply_text("🗑 All saved dates cleared.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file_name = doc.file_name or "received_file"
    await update.message.reply_text(f"📥 Received: `{file_name}`\nExtracting dates...", parse_mode="Markdown")

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = Path(tmp_dir) / file_name
        tg_file = await context.bot.get_file(doc.file_id)
        await tg_file.download_to_drive(file_path)
        await process_and_respond(update, context, file_path)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🖼 Photo received — extracting dates...")
    photo = update.message.photo[-1]

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = Path(tmp_dir) / "photo.jpg"
        tg_file = await context.bot.get_file(photo.file_id)
        await tg_file.download_to_drive(file_path)
        await process_and_respond(update, context, file_path)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text("💬 Text received — extracting dates...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = Path(tmp_dir) / "message.txt"
        file_path.write_text(text, encoding="utf-8")
        await process_and_respond(update, context, file_path)


async def process_and_respond(update: Update, context: ContextTypes.DEFAULT_TYPE, file_path: Path):
    """Run extractor and handle single vs multiple dates"""
    extractor = DateExtractor()
    extractor.process_file(file_path)

    if not extractor.extracted_dates:
        await update.message.reply_text("❌ No dates found in this file.")
        return

    result = extractor.extracted_dates[0]
    event_name = result.get('event_name', 'Unknown Event')
    dates = result.get('dates', [])

    if len(dates) == 0:
        await update.message.reply_text("❌ No dates found.")
    elif len(dates) == 1:
        # Single date — auto-save it
        save_date_to_file(event_name, dates[0])
        await update.message.reply_text(
            f"✅ *{event_name}*\n📅 `{dates[0]}`\n\n💾 Automatically saved!",
            parse_mode="Markdown"
        )
    else:
        # Multiple dates — let user choose
        keyboard = []
        # Store data in user context to keep callback_data short (<= 64 bytes)
        message_id = update.message.message_id if update.message else "unknown"
        data_key = f"dates_{message_id}"
        context.user_data[data_key] = {
            "event_name": event_name,
            "dates": dates,
        }

        for idx, date in enumerate(dates):
            # Each button callback format: "save:message_id:idx"
            callback_data = f"save:{message_id}:{idx}"
            keyboard.append([InlineKeyboardButton(f"📅 {date}", callback_data=callback_data)])

        keyboard.append([InlineKeyboardButton("✅ Save All", callback_data=f"save_all:{message_id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"✅ *{event_name}*\n\nFound {len(dates)} dates. Select which to save:",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks for date selection"""
    query = update.callback_query
    await query.answer()

    data = query.data.split(':')
    action = data[0]

    if action == "save":
        # Single date selected
        if len(data) < 3:
            await query.edit_message_text("❌ Invalid selection data.")
            return
        message_id = data[1]
        idx = int(data[2])
        payload = context.user_data.get(f"dates_{message_id}")
        if not payload:
            await query.edit_message_text("❌ Selection expired. Please resend the file.")
            return
        event_name = payload.get("event_name", "Unknown Event")
        dates = payload.get("dates", [])
        if idx < 0 or idx >= len(dates):
            await query.edit_message_text("❌ Invalid date index.")
            return
        date = dates[idx]
        save_date_to_file(event_name, date)
        await query.edit_message_text(
            f"✅ *{event_name}*\n📅 `{date}`\n\n💾 Saved!",
            parse_mode="Markdown"
        )

    elif action == "save_all":
        if len(data) < 2:
            await query.edit_message_text("❌ Invalid selection data.")
            return
        message_id = data[1]
        payload = context.user_data.get(f"dates_{message_id}")
        if not payload:
            await query.edit_message_text("❌ Selection expired. Please resend the file.")
            return
        event_name = payload.get("event_name", "Unknown Event")
        dates = payload.get("dates", [])
        for date in dates:
            save_date_to_file(event_name, date)
        await query.edit_message_text(
            f"✅ *{event_name}*\n\n💾 Saved all {len(dates)} dates!",
            parse_mode="Markdown"
        )


def main():
    print("🤖 Timely bot is running... Press Ctrl+C to stop.")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("saved", view_saved))
    app.add_handler(CommandHandler("clear", clear_saved))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_callback))

    app.run_polling()


if __name__ == "__main__":
    main()