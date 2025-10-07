import asyncio
import os
import re
import json
import subprocess
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import yt_dlp

BOT_TOKEN = "your_bot_token"  # ← ЕДИНСТВЕННЫЙ необходимый параметр

ADV_TEXT = (
    "🚀 Пока видео загружается, посетите https://hosting.zp.ua — испытайте наш хостинг с 30-дневным бесплатным пробным периодом, карта не нужна.\n"
    "[Реклама]"
)

def is_valid_url(text):
    return re.match(r'^https?://', text) is not None

def format_comments(info, url):
    lines = [f"{url}\n", info.get('title', ''), "--------------------------------------------------"]
    lines.append(f"Просмотров: {info.get('view_count', 'N/A')}   "
                 f"Лайков: {info.get('like_count', 'N/A')}   "
                 f"Комментариев: {info.get('comment_count', 'N/A')}")
    lines.append("--------------------------------------------------")
    for c in info.get('comments', []):
        prefix = "+" if c.get('parent') == "root" else "\t+"
        lines.append(f"{prefix}{c.get('like_count', 0)} @{c.get('author', '')} >>> {c.get('text', '').replace('\n', ' ')}")
    return "\n".join(lines)

async def download_video_and_info(url):
    loop = asyncio.get_running_loop()
    def blocking():
        with yt_dlp.YoutubeDL({
            'format': 'bestvideo[height<=720]+bestaudio/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
            'cookiefile': 'cookies.txt'
        }) as ydl:
            info = ydl.extract_info(url, download=True)
            return info, ydl.prepare_filename(info)
    return await loop.run_in_executor(None, blocking)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not is_valid_url(url):
        await update.message.reply_text("Пожалуйста, отправьте корректную ссылку на видео!")
        return

    status = await update.message.reply_text(f"Загружаю видео...\n\n{ADV_TEXT}\n\nОжидайте.")
    try:
        info, video_path = await download_video_and_info(url)
        await update.message.reply_video(video=open(video_path, 'rb'), caption="✅ Видео готово (до 720p)!")

        # Комментарии
        base = os.path.splitext(os.path.basename(video_path))[0]
        json_path = f'downloads/{base}.info.json'
        subprocess.run([
            "yt-dlp", "--write-comments", "--dump-single-json", "--no-download", url
        ], stdout=open(json_path, "w", encoding="utf-8"), check=True)

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("comments"):
            txt_path = f'downloads/{base}.txt'
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(format_comments(data, url))
            await context.bot.send_document(update.effective_chat.id, open(txt_path, 'rb'), caption="✅ Комментарии (.txt)")
            os.remove(txt_path)

        os.remove(video_path)
        os.remove(json_path)
        await status.delete()

    except Exception as e:
        msg = f"❌ Ошибка: {e}"
        if "cookie" in str(e).lower() or "login" in str(e).lower():
            msg += "\n\nОбновите cookies.txt из браузера с авторизацией."
        await status.edit_text(msg)

if __name__ == "__main__":
    os.makedirs("downloads", exist_ok=True)
    print("Бот запущен...")
    Application.builder().token(BOT_TOKEN).build().run_polling(drop_pending_updates=True)
