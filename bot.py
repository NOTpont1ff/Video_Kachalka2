import logging
import os
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters
from moviepy.editor import AudioFileClip, VideoFileClip
import yt_dlp

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your bot token
TOKEN = 'YOUR_BOT_TOKEN_HERE'

# Dictionary to store user choices
user_choices = {}

# Command handler for /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Пришлите ссылку с ютуба:.')

# Message handler for YouTube links
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text
    chat_id = update.message.chat_id

    # Store the URL for the user
    user_choices[chat_id] = {'url': url}

    # Ask user for the format
    keyboard = [
        [InlineKeyboardButton("MP4", callback_data='mp4')],
        [InlineKeyboardButton("MP3", callback_data='mp3')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите формат:', reply_markup=reply_markup)

# Callback handler for the user's choice
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    format_choice = query.data

    # Retrieve the stored URL for the user
    url = user_choices.get(chat_id, {}).get('url')
    if not url:
        await query.edit_message_text('Ссылка не найдена.')
        return

    await query.edit_message_text(f'Качается {format_choice.upper()}...')

    try:
        with yt_dlp.YoutubeDL() as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_title = ydl.prepare_filename(info_dict)

            if format_choice == 'mp4':
                clip = VideoFileClip(file_title)
                file_name = file_title.replace('.webm', '.mp4')
                clip.write_videofile(file_name, codec='libx264', audio_codec='aac')
            else:
                clip = AudioFileClip(file_title)
                file_name = file_title.replace('.webm', '.mp3')
                clip.write_audiofile(file_name)

            if os.path.exists(file_name):
                with open(file_name, 'rb') as file:
                    if format_choice == 'mp4':
                        await context.bot.send_video(chat_id=chat_id, video=file)
                    else:
                        await context.bot.send_audio(chat_id=chat_id, audio=file)
                os.remove(file_name)
            else:
                await query.edit_message_text('Не удалось скачать.')
    except Exception as e:
        await query.edit_message_text('Не удалось скачать, попробуйте позже.')
        logger.error(e)

# Function to handle graceful shutdown
def graceful_shutdown(sig, frame):
    logger.info('Shutting down gracefully...')
    application.stop()
    sys.exit(0)

# Main function to start the bot
def main() -> None:
    # Create the Application and pass it your bot's token
    global application
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # on noncommand i.e message - ask for format
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    # on callback query for button clicks
    application.add_handler(CallbackQueryHandler(button))

    # Register signal handlers for graceful shutdown
    # signal.signal(signal.SIGINT, graceful_shutdown)
    # signal.signal(signal.SIGTERM, graceful_shutdown)

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    application.run_polling()

if __name__ == '__main__':
    main()

if __name__ == '__main__':
    main()
