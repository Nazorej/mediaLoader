import asyncio
import os
import re
import json
import subprocess
from pyrogram import Client, filters
import yt_dlp

API_ID = 1234567            # <-- Ваш api_id
API_HASH = "your_api_hash"  # <-- Ваш api_hash
BOT_TOKEN = "your_bot_token" # <-- Ваш бот token

ADV_TEXT = (
    "🚀 Пока видео загружается, посетите https://hosting.zp.ua — испытайте наш хостинг с 30-дневным бесплатным пробным периодом, карта не нужна.\n"
    "[Реклама]"
)

def is_valid_url(text):
    return re.match(r'^https?://', text) is not None

def format_comments(info, url):
    lines = [f"{url}\n"]
    lines.append(info.get('title', ''))
    lines.append("--------------------------------------------------")
    view_count = info.get('view_count', 'N/A')
    like_count = info.get('like_count', 'N/A')
    comment_count = info.get('comment_count', 'N/A')
    lines.append(f"Просмотров: {view_count}   Лайков: {like_count}   Комментариев: {comment_count}")
    lines.append("--------------------------------------------------")
    comments = info.get('comments', [])
    for c in comments:
        prefix = "+" if c.get('parent') == "root" else "\t+"
        like = c.get('like_count', 0)
        author = c.get('author', '')
        text = c.get('text', '').replace('\n', ' ')
        lines.append(f"{prefix}{like} @{author} >>> {text}")
    return "\n".join(lines)

async def async_download_video_and_info(ydl_opts, url):
    loop = asyncio.get_event_loop()
    def blocking():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return info, filename
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
        'cookiefile': 'cookies.txt'
    }
    try:
        # Скачиваем видео обычным API yt-dlp
        info, filename = await async_download_video_and_info(ydl_opts, url)
        await message.reply_video(video=filename, caption="✅ Ваше видео готово (до 720p)!")

        # Теперь --dump-single-json для полного info (comments) как в bash.sh
        base = os.path.splitext(os.path.basename(filename))[0]
        info_json_path = f'downloads/{base}.info.json'
        yt_dlp_cmd = [
            "yt-dlp",
            "--write-comments",
            "--dump-single-json",
            "--no-download",
            url
        ]
        with open(info_json_path, "w", encoding="utf-8") as fjson:
            subprocess.run(yt_dlp_cmd, stdout=fjson, check=True)
        # Читаем info.json и, если есть comments, пишем .txt
        if os.path.exists(info_json_path):
            with open(info_json_path, "r", encoding="utf-8") as f:
                info_json_data = json.load(f)
            comments = info_json_data.get("comments", [])
            if comments:
                txt_filename = f'downloads/{base}.txt'
                with open(txt_filename, "w", encoding="utf-8") as ftxt:
                    ftxt.write(format_comments(info_json_data, url))
                await client.send_document(message.chat.id, txt_filename, caption="✅ Комментарии к видео (.txt)")
        await status_msg.delete()
    except Exception as e:
        error_text = f"❌ Ошибка загрузки: {e}"
        if "cookies" in str(e).lower() or "login_required" in str(e).lower():
            error_text += "\n\nВозможно, cookies устарели. Обновите cookies.txt — экспортируйте их из браузера с авторизацией в Instagram."
        await status_msg.edit(error_text)

if __name__ == "__main__":
    print("Бот запущен. Ожидание сообщений...")
    app.run()
