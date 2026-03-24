"""Minimal Flask UI for photo_to_story."""

from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from uuid import uuid4

from flask import Flask, abort, redirect, render_template, request, send_from_directory, url_for
from openai import APIError
from app.pipeline import run_pipeline
from app.utils.files import (
    FILENAME_RUN_META_JSON,
    FILENAME_STORY_MP3,
    FILENAME_STORY_TXT,
    FILENAME_VISION_JSON,
)
from app.utils.image import ALLOWED_IMAGE_SUFFIXES

ROOT = Path(__file__).resolve().parent.parent

ALLOWED_MEDIA = frozenset(
    {
        FILENAME_VISION_JSON,
        FILENAME_STORY_TXT,
        FILENAME_STORY_MP3,
        FILENAME_RUN_META_JSON,
    }
)

RUN_NAME_RE = re.compile(r"^\d{8}_\d{6}$")


def _human_error(exc: BaseException) -> str:
    if isinstance(exc, APIError):
        return getattr(exc, "message", None) or str(exc)
    return str(exc)


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(ROOT / "templates"),
        static_folder=str(ROOT / "static"),
        static_url_path="/static",
    )
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")

    output_root = (ROOT / "outputs").resolve()
    upload_root = (ROOT / "static" / "uploads")
    upload_root.mkdir(parents=True, exist_ok=True)

    @app.route("/")
    def index():
        return render_template("index.html", default_lang="ru")

    @app.post("/generate")
    def generate():
        if "image" not in request.files:
            return render_template("error.html", message="Файл изображения не выбран."), 400
        file = request.files["image"]
        if not file or file.filename == "":
            return render_template("error.html", message="Файл изображения не выбран."), 400

        lang = (request.form.get("lang") or "ru").strip() or "ru"
        style = (request.form.get("style") or "creative").strip().lower()
        if style not in ("creative", "factual"):
            style = "creative"
        suffix = Path(file.filename).suffix.lower()
        if suffix not in ALLOWED_IMAGE_SUFFIXES:
            return render_template(
                "error.html",
                message="Неподдерживаемый формат. Используйте PNG, JPG, JPEG или WEBP.",
            ), 400

        uid = uuid4().hex
        tmp_path = upload_root / f"{uid}{suffix}"
        file.save(tmp_path)

        try:
            result = run_pipeline(tmp_path, ROOT / "outputs", lang, style)
        except ValueError as exc:
            tmp_path.unlink(missing_ok=True)
            if "OPENAI_API_KEY" in str(exc):
                msg = "Проверьте OPENAI_API_KEY в файле .env."
            else:
                msg = str(exc)
            return render_template("error.html", message=msg), 400
        except FileNotFoundError:
            tmp_path.unlink(missing_ok=True)
            return render_template("error.html", message="Файл изображения не найден."), 404
        except OSError as exc:
            tmp_path.unlink(missing_ok=True)
            if "Failed to write output files" in str(exc):
                msg = "Не удалось сохранить результаты на диск."
            else:
                msg = "Не удалось прочитать изображение."
            return render_template("error.html", message=msg), 500
        except RuntimeError as exc:
            tmp_path.unlink(missing_ok=True)
            return render_template("error.html", message=_human_error(exc)), 502
        except APIError as exc:
            tmp_path.unlink(missing_ok=True)
            return render_template("error.html", message=_human_error(exc)), 502

        preview_path = upload_root / f"preview_{result['run_name']}{suffix}"
        shutil.copy2(tmp_path, preview_path)
        tmp_path.unlink(missing_ok=True)

        return redirect(url_for("result_page", run_name=result["run_name"]))

    @app.route("/result/<run_name>")
    def result_page(run_name: str):
        if not RUN_NAME_RE.match(run_name):
            return render_template("error.html", message="Некорректный идентификатор прогона."), 400
        run_path = output_root / run_name
        if not run_path.is_dir():
            return render_template("error.html", message="Результат не найден."), 404

        story_text = (run_path / FILENAME_STORY_TXT).read_text(encoding="utf-8")
        meta = json.loads((run_path / FILENAME_RUN_META_JSON).read_text(encoding="utf-8"))

        previews = list(upload_root.glob(f"preview_{run_name}.*"))
        preview_url = None
        if previews:
            preview_url = url_for("static", filename=f"uploads/{previews[0].name}")

        vision_path = run_path / FILENAME_VISION_JSON
        story_path = run_path / FILENAME_STORY_TXT
        vision_data = json.loads(vision_path.read_text(encoding="utf-8"))

        return render_template(
            "result.html",
            run_name=run_name,
            story_text=story_text,
            meta=meta,
            preview_url=preview_url,
            vision_path_str=str(vision_path),
            story_path_str=str(story_path),
            audio_url=url_for("media", run_name=run_name, filename=FILENAME_STORY_MP3),
            download_mp3_url=url_for("download_mp3", run_name=run_name),
            vision_data=vision_data,
        )

    @app.route("/media/<run_name>/<filename>")
    def media(run_name: str, filename: str):
        if not RUN_NAME_RE.match(run_name) or filename not in ALLOWED_MEDIA:
            abort(404)
        d = output_root / run_name
        if not d.is_dir():
            abort(404)
        return send_from_directory(d, filename, as_attachment=False)

    @app.route("/download/<run_name>/story.mp3")
    def download_mp3(run_name: str):
        if not RUN_NAME_RE.match(run_name):
            abort(404)
        d = output_root / run_name
        if not d.is_dir():
            abort(404)
        return send_from_directory(
            d,
            FILENAME_STORY_MP3,
            as_attachment=True,
            download_name=f"story_{run_name}.mp3",
        )

    return app
