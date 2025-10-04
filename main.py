import asyncio
import re
from pyrogram import Client, filters
import yt_dlp

API_ID = 1234567            # <-- Ваш api_id
API_HASH = "your_api_hash"  # <-- Ваш api_hash
BOT_TOKEN = "your_bot_token" # <-- Ваш бот token

ADV_TEXT = (
    "🚀 Пока видео загружается, подпишитесь на наш Telegram-канал @example_channel!\n"
    "Там конкурсы, новости и бонусы. [Реклама]"
)

def is_valid_url(text):
    return re.match(r'^https?://', text) is not None

async def async_download_video(ydl_opts, url):
    loop = asyncio.get_event_loop()
    def blocking():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    return await loop.run_in_executor(None, blocking)

app = Client("mediaLoaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.private & filters.text)
async def download_video(client, message):
    url = message.text.strip()
    if not is_valid_url(url):
        await message.reply("Пожалуйста, отправьте корректную ссылку на видео!")
        return
    status_msg = await message.reply(f"Загружаю видео...\n\n{ADV_TEXT}\n\nОжидайте, загрузка может занять время.")
    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'merge_output_format': 'mp4',
        'cookiefile': 'cookies.txt',
    }
    try:
        filename = await async_download_video(ydl_opts, url)
        await message.reply_video(video=filename, caption="✅ Ваше видео готово (до 720p)!")
        await status_msg.delete()
    except Exception as e:
        error_text = f"❌ Ошибка загрузки: {e}"
        if "cookies" in str(e).lower() or "login_required" in str(e).lower():
            error_text += "\n\nВозможно, cookies устарели. Обновите cookies.txt — экспортируйте их из браузера с авторизацией в Instagram."
        await status_msg.edit(error_text)

if __name__ == "__main__":
    print("Бот запущен. Ожидание сообщений...")
    app.run()