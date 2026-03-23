# photo_to_story

Минимальное CLI-приложение: анализ изображения через OpenAI Vision, короткая история на заданном языке и озвучка (TTS). Результаты сохраняются в `outputs/<timestamp>/`.

## Требования

- Python 3.11+
- Переменные окружения (см. `.env.example`): `OPENAI_API_KEY`, `OPENAI_MODEL` (чат и vision), `OPENAI_TTS_MODEL`, `OPENAI_TTS_VOICE`

## Установка

```bash
cd /path/to/Project
python -m venv .venv
```

Активация виртуального окружения:

- Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`
- Linux/macOS: `source .venv/bin/activate`

```bash
pip install -r requirements.txt
copy .env.example .env
```

Отредактируйте `.env`: укажите `OPENAI_API_KEY` и при необходимости модели (`OPENAI_MODEL`, `OPENAI_TTS_MODEL`, `OPENAI_TTS_VOICE`).

## Запуск

Из корня проекта:

```bash
python main.py --image path/to/photo.jpg
```

Опции:

- `--image` — путь к файлу изображения (обязательно)
- `--output-dir` — базовая папка для прогонов (по умолчанию `outputs`)
- `--lang` — язык истории (по умолчанию `ru`)

Пример:

```bash
python main.py --image .\photos\sample.png --output-dir outputs --lang ru
```

В каталоге `outputs/<YYYYMMDD_HHMMSS>/` появятся:

- `vision.json` — поля `summary`, `objects`, `mood`, `setting`
- `story.txt` — текст истории (ориентир 500–900 символов)
- `story.mp3` — озвучка

## Ошибки

- Нет или неверный ключ: сообщение о необходимости `.env` / `OPENAI_API_KEY`
- Файл изображения не найден: явное указание пути из `--image`
- Ошибка API OpenAI: краткое описание ответа сервиса

Логи пишутся в консоль (уровень INFO).
