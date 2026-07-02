import os
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = '8780993922:AAGFaTJn2VlPD8IV1NzleJ6q5XsKQt3nX0I'

# --- بخش فیک برای راضی کردن وب‌سرویس رندر ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is Running!")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()
# ----------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('سلام! لینک ویدیوی یوتیوب رو برام بفرست تا دانلودش کنم.')

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    chat_id = update.message.chat_id
    
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text('لطفاً یک لینک معتبر ارسال کنید.')
        return

    status_message = await update.message.reply_text('در حال بررسی و دانلود ویدیو... لطفا کمی صبر کنید.')

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': f'downloads/{chat_id}_%(id)s.%(ext)s',
        'max_filesize': 50 * 1024 * 1024,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
        await status_message.edit_text('دانلود انجام شد! در حال ارسال به تلگرام...')
        with open(filename, 'rb') as video_file:
            await update.message.reply_video(video=video_file, caption=info.get('title', 'Video'))
            
        os.remove(filename)
        await status_message.delete()

    except Exception as e:
        logging.error(f"Error: {e}")
        await status_message.edit_text('متأسفانه در دانلود یا ارسال ویدیو خطایی رخ داد. ممکنه حجم ویدیو خیلی بالا باشه.')

def main():
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    # اجرای سرور فیک در یک ترد جداگانه برای رندر
    threading.Thread(target=run_health_check_server, daemon=True).start()

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    application.run_polling()

if __name__ == '__main__':
    main()
