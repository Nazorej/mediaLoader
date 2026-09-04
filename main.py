import asyncio
import os
import re
import json
import subprocess
import time
from pyrogram import Client, filters
import yt_dlp

API_ID = 1234567              # <-- Ваш api_id
API_HASH = "your_api_hash"    # <-- Ваш api_hash
BOT_TOKEN = "your_bot_token"  # <-- Ваш бот token

DELETE_AFTER_SEND = False     # True — удалять файлы с диска после успешной отправки

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
COOKIES_PATH = os.path.join(BASE_DIR, "cookies.txt")

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
    loop = asyncio.get_running_loop()
    def blocking():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return info, filename
    return await loop.run_in_executor(None, blocking)

async def upload_progress(current, total, status_msg, base_text, state):
    """Прогресс отправки: проценты в консоль + обновление сообщения раз в 10 секунд."""
    if not total:
        return
    pct = current * 100 // total
    mb = current // (1024 * 1024)
    total_mb = total // (1024 * 1024)
    print(f"Отправка в Telegram: {pct}% ({mb}/{total_mb} МБ)", end="\r")
    if current >= total:
        print()  # перевод строки, чтобы не затереть следующие логи
        return
    now = time.monotonic()
    if now - state["t"] >= 10:  # защита от флуд-лимита Telegram
        state["t"] = now
        try:
            await status_msg.edit(f"{base_text}\n\n📤 Отправка: {mb} / {total_mb} МБ ({pct}%)")
        except Exception:
            pass

app = Client(
    "mediaLoaderBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workdir=BASE_DIR,
)

@app.on_message(filters.private & filters.text)
async def download_video(client, message):
    url = message.text.strip()
    if not is_valid_url(url):
        await message.reply("Пожалуйста, отправьте корректную ссылку на видео!")
        return

    status_text = f"Загружаю видео (до 1080p)...\n\n{ADV_TEXT}"
    status_msg = await message.reply(status_text + "\n\nОжидайте, загрузка может занять время.")

    ydl_opts = {
        'format': 'bestvideo[height<=1080]+bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'concurrent_fragment_downloads': 4,
    }
    if os.path.exists(COOKIES_PATH):
        ydl_opts['cookiefile'] = COOKIES_PATH

    video_file = None
    txt_file = None
    try:
        info, filename = await async_download_video_and_info(ydl_opts, url)
        video_file = filename
        await message.reply_video(
            video=filename,
            caption="✅ Ваше видео готово (до 1080p)!",
            supports_streaming=True,
            progress=upload_progress,
            progress_args=(status_msg, status_text, {"t": 0.0}),
        )

        base = os.path.splitext(os.path.basename(filename))[0]
        info_json_path = os.path.join(DOWNLOAD_DIR, f"{base}.info.json")

        yt_dlp_cmd = ["yt-dlp", "-J", "--write-comments", "--remote-components", "ejs:github"]
        if os.path.exists(COOKIES_PATH):
            yt_dlp_cmd += ["--cookies", COOKIES_PATH]
        yt_dlp_cmd.append(url)

        print("Получаю комментарии...")
        with open(info_json_path, "w", encoding="utf-8") as fjson:
            subprocess.run(yt_dlp_cmd, stdout=fjson, check=True)

        if os.path.exists(info_json_path):
            with open(info_json_path, "r", encoding="utf-8") as f:
                info_json_data = json.load(f)
            if info_json_data.get("comments"):
                txt_filename = os.path.join(DOWNLOAD_DIR, f"{base}.txt")
                with open(txt_filename, "w", encoding="utf-8") as ftxt:
                    ftxt.write(format_comments(info_json_data, url))
                txt_file = txt_filename
                await client.send_document(
                    message.chat.id,
                    txt_filename,
                    caption="✅ Комментарии к видео (.txt)",
                )

        await status_msg.delete()
        print("Готово ✅")
    except Exception as e:
        error_text = f"❌ Ошибка загрузки: {e}"
        low = str(e).lower()
        if "cookies" in low or "login_required" in low or "confirm you" in low:
            error_text += "\n\nВозможно, требуется авторизация. Положите свежий cookies.txt рядом со скриптом и повторите."
        try:
            await status_msg.edit(error_text)
        except Exception:
            pass
    finally:
        if DELETE_AFTER_SEND:
            for path in (video_file, txt_file):
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass

if __name__ == "__main__":
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    print("Бот запущен. Ожидание сообщений...")
    app.run()
