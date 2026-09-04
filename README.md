# mediaLoader

Telegram-бот для скачивания видео с YouTube, Instagram, TikTok и других платформ.  
✅ Поддерживает до **1080p** (автоматически объединяет видео и аудио через `ffmpeg`)  
✅ Работает на **Python 3.14** (через `kurigram` — актуальный форк Pyrogram)  
✅ Обходит JS-челленджи YouTube через механизм **EJS** — для YouTube `cookies` не нужны  
✅ Поддерживает приватный контент через опциональный `cookies.txt` (Instagram и т.п.)  
✅ Показывает **прогресс скачивания и отправки** в консоли и в чате  
✅ Асинхронная обработка — быстро отвечает даже при множестве пользователей  
✅ Отправляет видео (сразу доступно для стриминга в Telegram) и, при наличии, комментарии в виде `.txt`  
✅ Показывает рекламу хостинга во время загрузки 😊

---

## 🛠 Требования

- Windows 10 / 11  
- Python 3.13+ (проверено на 3.14)  
- [`ffmpeg`](https://www.gyan.dev/ffmpeg/builds/) — склейка видео и аудио  
- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) — скачивание видео  
- [`kurigram`](https://pypi.org/project/kurigram/) — актуальный форк Pyrogram (импортируется как `pyrogram`)  
- [`Deno`](https://deno.com/) — JS-рантайм для обхода защиты YouTube (EJS)  
- Токен бота от [@BotFather](https://t.me/BotFather) **+** `API_ID` и `API_HASH` от [my.telegram.org](https://my.telegram.org)

> ⚠️ **Важно:** бот работает через MTProto (Pyrogram/kurigram), поэтому нужны **все три** параметра: `API_ID`, `API_HASH`, `BOT_TOKEN`.  
> (В старой версии на `python-telegram-bot` был нужен только `BOT_TOKEN` — это изменилось.)

> 💡 **Необязательно:** `tgcrypto` ускоряет шифрование MTProto в несколько раз. На Python 3.14 оригинальный пакет не собирается без Visual C++ Build Tools — вместо них попробуйте форк: `pip install tgcrypto2`. Без него бот тоже работает, просто отправляет медленнее.

---

## 📥 Установка

### 1. Установите Python

Рекомендуется новый **Python Install Manager**: на [python.org/downloads](https://www.python.org/downloads/) скачайте `python-manager-*.msix` (первая ссылка на странице) и установите двойным кликом. Затем:

```cmd
py install 3.14
```

> Подойдёт и классический установщик (Windows installer 64-bit со страницы конкретного релиза).

Проверка:
```cmd
python --version
pip --version
```

### 2. Установите `ffmpeg`

1. Перейдите на [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/)
2. Скачайте **`ffmpeg-release-essentials.zip`**
3. Распакуйте, например, в `C:\py\ffmpeg`
4. Добавьте путь к папке `bin` (например, `C:\py\ffmpeg\bin`) в `PATH`:

   **Вручную:** `Win + R` → `sysdm.cpl` → **Дополнительные параметры → Переменные среды** → в разделе **Переменные среды пользователя** выберите `Path` → **Изменить** → **Создать** → вставьте путь → OK

Проверка (в **новом** окне терминала):
```cmd
ffmpeg -version
```

### 3. Установите Deno

Нужен yt-dlp для обхода JS-челленджей YouTube (механизм EJS):

```cmd
winget install DenoLand.Deno
```

или с [deno.com](https://deno.com/) (установщик сам добавит его в `PATH`).

Проверка (в **новом** окне терминала):
```cmd
deno --version
```

### 4. Установите зависимости Python

Откройте терминал в папке проекта и выполните:

```cmd
pip install kurigram yt-dlp
```

> ❗ Если после установки появится предупреждение вида  
> `WARNING: The script yt-dlp.exe is installed in '...\Scripts' which is not on PATH` —  
> добавьте указанную там папку `Scripts` в `PATH`. Это нормальное поведение нового Python-менеджера: он не трогает `PATH` автоматически.  
> Путь обычно такой: `C:\Users\<имя>\AppData\Local\Python\pythoncore-<версия>-64\Scripts`  
> Альтернатива — запускать yt-dlp через `python -m yt_dlp`.

### 5. Настройте бота

1. `API_ID` и `API_HASH`: зайдите на [my.telegram.org](https://my.telegram.org) → **API development tools** → создайте приложение → скопируйте значения.
2. `BOT_TOKEN`: напишите [@BotFather](https://t.me/BotFather) → `/newbot` → получите токен.
3. Откройте `main.py` и заполните:

```python
API_ID = 1234567              # <-- Ваш api_id
API_HASH = "your_api_hash"    # <-- Ваш api_hash
BOT_TOKEN = "your_bot_token"  # <-- Ваш бот token
```

> 🔒 **Не коммитьте свои токены в Git!**  
> Для продвинутой настройки используйте `.env` или переменные среды.

### 6. (Опционально) Добавьте `cookies.txt`

YouTube обычно работает **без** cookies благодаря EJS. Cookies понадобятся для **приватного контента** (Instagram и т.п.):

- Экспортируйте cookies из браузера с авторизацией (например, расширение **Get cookies.txt LOCALLY** или аналогичное)
- Сохраните файл как `cookies.txt` в корень проекта (рядом с `main.py`)

Если файла нет — бот просто работает без него (проверка автоматическая).

---

## ▶️ Запуск

```cmd
python main.py
```

Бот запустится и начнёт принимать ссылки. Отправьте ему URL в личные сообщения — и через пару минут получите видео до 1080p (прогресс виден в консоли и в чате).

- Файлы сохраняются в папку `downloads` рядом со скриптом.
- За удаление после отправки отвечает флаг в начале `main.py`:
  ```python
  DELETE_AFTER_SEND = False   # True — удалять файлы с диска после отправки
  ```
- При первом запуске рядом со скриптом создастся файл сессии `mediaLoaderBot.session` — не удаляйте его без необходимости.

---

## ❓ Возникли проблемы?

- **`'yt-dlp' не является внутренней или внешней командой`** → добавьте папку `Scripts` в `PATH` (см. шаг 4) и откройте **новое** окно терминала. Уже открытые окна не видят изменений `PATH` (вкладки Windows Terminal закрывайте целиком).
- **`ffmpeg -version` не находится** → проверьте, что путь к `bin` попал в `PATH`, и перезапустите терминал.
- **`ERROR: Unable to create directory ... Отказано в доступе`** → бот запущен из папки без прав на запись (например, `System32`). Скрипт сохраняет всё рядом с собой — проверьте, что рядом с `main.py` нет **файла** с именем `downloads`.
- **`TgCrypto is missing!`** → это не ошибка, бот работает. Для ускорения: `pip install tgcrypto2` (оригинальный `tgcrypto` на 3.14 требует Visual C++ Build Tools).
- **`Sign in to confirm you're not a bot`** (YouTube) → положите свежий `cookies.txt` рядом со скриптом и повторите.
- **Бот «завис» после скачивания** → скорее всего, идёт отправка видео в Telegram (файлы по 200+ МБ грузятся несколько минут). Следите за прогрессом в консоли: `Отправка в Telegram: X%`.
- **Файлы больше ~2 ГБ не отправляются** → это лимит Telegram для ботов, не баг.
- **Старые скрипты на pyrogram не работают на Python 3.14** (ошибка `There is no current event loop`) → замените `pyrogram` на `kurigram`: код менять не нужно, импорт тот же.

Удачи! 🚀  
— [Nazorej](https://github.com/Nazorej)
