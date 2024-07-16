import logging
import os
import signal
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters
import yt_dlp

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your bot token
TOKEN = '7240209800:AAFnyLI0VPIYWB3sVAR84UUztLnokNQjUhE'

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

    if format_choice == 'mp4':
        ydl_opts = {
            'format': 'best[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'ffmpeg_location': r'C:/ffmpeg-master-latest-win64-gpl/ffmpeg-master-latest-win64-gpl/bin',
            'noplaylist': True,
        }
        

    else:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'ffmpeg_location': r'C:/ffmpeg-master-latest-win64-gpl/ffmpeg-master-latest-win64-gpl/bin',
            'noplaylist': True,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_title = ydl.prepare_filename(info_dict)
            if format_choice == 'mp4':
                file_name = file_title.replace('.webm', '.mp4')
            else:
                file_name = file_title.replace('.webm', '.mp3')

            if not os.path.exists(file_name) and os.path.exists(file_title):
                # Fallback to the original filename if conversion didn't happen
                file_name = file_title

            if os.path.exists(file_name):
                with open(file_name, 'rb') as file:
                    if format_choice == 'mp4':
                        await context.bot.send_video(chat_id=chat_id, video=file)
                    else:
                        await context.bot.send_audio(chat_id=chat_id, audio=file)
                os.remove(file_name)
            else:
                await query.edit_message_text('Не удалос скачать.')
    except Exception as e:
        await query.edit_message_text('Не далось скачать, попробуйте позже.')
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
