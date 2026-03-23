# photo_to_story

CLI: анализ фото (OpenAI Vision), короткая история на выбранном языке, озвучка (TTS). Результаты пишутся в каталог `<output-dir>/<timestamp>/`.

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

Устаревшее имя `OPENAI_MODEL` (если задано без vision/chat) используется как значение по умолчанию для обеих LLM-моделей.

## Запуск

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

## Выходные файлы

В каталоге `outputs/<YYYYMMDD_HHMMSS>/` (или ваш `--output-dir`):

- `vision.json` — сцена: `summary`, `objects`, `mood`, `setting`
- `story.txt` — текст истории
- `story.mp3` — озвучка
- `run_meta.json` — метаданные прогона (пути, модели, время, статус)

В конце работы в консоль выводится краткий итог: каталог, список файлов, время выполнения.

## Коды выхода

| Код | Ситуация |
|-----|----------|
| 0 | Успех |
| 1 | Нет или неверная конфигурация (например, нет `OPENAI_API_KEY`) |
| 2 | Файл изображения не найден или ошибка чтения |
| 3 | Ошибка API OpenAI |
| 4 | Ошибка записи результатов |
| 5 | Неподдерживаемое расширение файла изображения |

Логи: уровень INFO в stderr.
