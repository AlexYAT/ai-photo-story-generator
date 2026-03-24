# photo_to_story

CLI и минимальный веб-интерфейс (Flask): анализ фото (OpenAI Vision), короткая история на выбранном языке, озвучка (TTS). Результаты пишутся в каталог `<output-dir>/<timestamp>/`.

Общая логика вынесена в `app/pipeline.py` (`run_pipeline`): её вызывают и `main.py`, и Flask — без subprocess.

## Требования

- Python 3.11+
- Ключ OpenAI и имена моделей в `.env` (см. `.env.example`)

## Установка

```bash
cd /path/to/Project
python -m venv .venv
```

Активация venv: Windows PowerShell `.\.venv\Scripts\Activate.ps1`; Linux/macOS `source .venv/bin/activate`.

```bash
pip install -r requirements.txt
copy .env.example .env
```

## Настройка `.env`

Заполните `OPENAI_API_KEY`. При необходимости задайте модели:

| Переменная | Назначение |
|------------|------------|
| `OPENAI_API_KEY` | API-ключ |
| `OPENAI_VISION_MODEL` | Модель для анализа изображения |
| `OPENAI_CHAT_MODEL` | Модель для текста истории |
| `OPENAI_TTS_MODEL` | Модель озвучки |
| `OPENAI_TTS_VOICE` | Голос TTS |
| `FLASK_SECRET_KEY` | Секрет сессий Flask (для веб-интерфейса; в продакшене задайте случайную строку) |

Устаревшее имя `OPENAI_MODEL` (если задано без vision/chat) используется как значение по умолчанию для обеих LLM-моделей.

## Запуск CLI

Из корня проекта:

```bash
python main.py --image path/to/photo.jpg
```

Пример:

```bash
python main.py --image .\photos\sample.png --output-dir outputs --lang ru
```

Аргументы:

- `--image` — путь к изображению (`.png`, `.jpg`, `.jpeg`, `.webp`)
- `--output-dir` — базовая папка для прогонов (по умолчанию `outputs`)
- `--lang` — язык текста истории (по умолчанию `ru`)

## Запуск веб-интерфейса (Flask)

Из корня проекта (с активированным venv):

```bash
python webapp.py
```

Или:

```bash
flask --app webapp run
```

По умолчанию сервер: `http://127.0.0.1:5000`.

### Маршруты

| Метод | Путь | Описание |
|--------|------|----------|
| GET | `/` | Форма: загрузка изображения и язык (по умолчанию `ru`) |
| POST | `/generate` | Запуск пайплайна, редирект на страницу результата |
| GET | `/result/<timestamp>` | Текст истории, превью, аудио, метаданные |
| GET | `/media/<timestamp>/<file>` | Раздача `story.mp3`, `vision.json` и др. из папки прогона |

Загрузки сохраняются под `static/uploads/` (превью для страницы результата). Сгенерированные артефакты — в `outputs/<YYYYMMDD_HHMMSS>/`, как у CLI.

## Выходные файлы

В каталоге `outputs/<YYYYMMDD_HHMMSS>/` (или ваш `--output-dir`):

- `vision.json` — сцена: `summary`, `objects`, `mood`, `setting`
- `story.txt` — текст истории
- `story.mp3` — озвучка
- `run_meta.json` — метаданные прогона (пути, модели, время, статус)

В конце работы CLI в консоль выводится краткий итог: каталог, список файлов, время выполнения.

## Коды выхода (CLI)

| Код | Ситуация |
|-----|----------|
| 0 | Успех |
| 1 | Нет или неверная конфигурация (например, нет `OPENAI_API_KEY`) |
| 2 | Файл изображения не найден или ошибка чтения |
| 3 | Ошибка API OpenAI |
| 4 | Ошибка записи результатов |
| 5 | Неподдерживаемое расширение файла изображения |

Логи CLI: уровень INFO в stderr.
