import logging
import os
import signal
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters
from yt_dlp import YoutubeDL
from moviepy.editor import VideoFileClip, AudioFileClip

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = 'YOUR_BOT_TOKEN_HERE'

user_choices = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Пришлите ссылку с ютуба:.')

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text
    chat_id = update.message.chat_id

    user_choices[chat_id] = {'url': url}

    keyboard = [
        [InlineKeyboardButton("MP4", callback_data='mp4')],
        [InlineKeyboardButton("MP3", callback_data='mp3')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите формат:', reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    format_choice = query.data

    url = user_choices.get(chat_id, {}).get('url')
    if not url:
        await query.edit_message_text('Ссылка не найдена.')
        return

    await query.edit_message_text(f'Качается {format_choice.upper()}...')

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if format_choice == 'mp4' else 'bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor' if format_choice == 'mp4' else 'FFmpegExtractAudio',
            'preferedformat': 'mp4' if format_choice == 'mp4' else 'mp3',
        }],
        'noplaylist': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_title = ydl.prepare_filename(info_dict)
            if format_choice == 'mp4':
                file_name = file_title.replace('.webm', '.mp4')
            else:
                file_name = file_title.replace('.webm', '.mp3')

            if not os.path.exists(file_name) and os.path.exists(file_title):
                file_name = file_title

            if os.path.exists(file_name):
                with open(file_name, 'rb') as file:
                    if format_choice == 'mp4':
                        await context.bot.send_video(chat_id=chat_id, video=file)
                    else:
                        await context.bot.send_audio(chat_id=chat_id, audio=
