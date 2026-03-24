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
| `FLASK_DEBUG` | Режим отладки при `python webapp.py`: `true` / `false` (по умолчанию `false`) |

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
- `--style` — режим текста: `creative` (художественный рассказ) или `factual` (сухое описание без метафор), по умолчанию `creative`

## Example inputs

В `static/examples/` лежат четыре демо-изображения для тестов и отчётов:

| Файл | Кейс |
|------|------|
| `example_1_ordinary.png` | **Ordinary image** — обычная фото-сцена с понятным содержимым. |
| `example_2_text_screenshot.png` | **Text screenshot** — скриншот с текстом / интерфейсом. |
| `example_3_plain_background.png` | **Plain background** — много пустого фона, мало объектов. |
| `example_4_overloaded_collage.png` | **Overloaded collage** — плотная коллажная композиция, много деталей. |

Подробное описание: [`docs/EXAMPLES_README.md`](docs/EXAMPLES_README.md).

Пример запуска CLI:

```bash
python main.py --image static/examples/example_1_ordinary.png --lang ru
```

## Demo cases

Ориентиры для демо-файлов в `static/examples/` (фактический `scene_type` / текст зависят от модели и эвристик):

| Кейс | Что ожидается | Типичный результат |
|------|----------------|-------------------|
| **ordinary image** | Богатая сцена, `scene_type` ≈ `photo`, уверенность обычно высокая | Связный рассказ / фактическое описание по выбранному `--style` |
| **text screenshot** | Много текста/UI → `screenshot` | Описание интерфейса или экрана, без выдуманного сюжета в factual |
| **plain background** | Мало объектов → часто `low_info` или низкая уверенность | Короткий fallback-текст вместо длинной истории, если сцена признана малоинформативной |
| **overloaded collage** | Много элементов → `collage` | Акцент на множестве фрагментов; при перегрузе возможна более осторожная формулировка |

## Запуск веб-интерфейса (Flask)

Из корня проекта (с активированным venv):

```bash
python webapp.py
```

Или:

```bash
flask --app webapp run
```

По умолчанию сервер: `http://127.0.0.1:5000`. Режим отладки выключен (`FLASK_DEBUG=false`). Чтобы включить автоперезагрузку и страницу с трассировкой ошибок, задайте в `.env` строку `FLASK_DEBUG=true` и снова запустите `python webapp.py`.

### Маршруты

| Метод | Путь | Описание |
|--------|------|----------|
| GET | `/` | Форма: загрузка изображения, язык и режим `style` (creative / factual) |
| POST | `/generate` | Запуск пайплайна, редирект на страницу результата |
| GET | `/result/<timestamp>` | Текст истории, превью, аудио, метаданные |
| GET | `/media/<timestamp>/<file>` | Раздача `story.mp3`, `vision.json` и др. из папки прогона |

Загрузки сохраняются под `static/uploads/` (превью для страницы результата). Сгенерированные артефакты — в `outputs/<YYYYMMDD_HHMMSS>/`, как у CLI.

## Выходные файлы

В каталоге `outputs/<YYYYMMDD_HHMMSS>/` (или ваш `--output-dir`):

- `vision.json` — сцена: `summary`, `objects`, `mood`, `setting`, `scene_type`, `confidence`
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
