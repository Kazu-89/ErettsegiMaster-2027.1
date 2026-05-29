from __future__ import annotations

import io
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from content import MODES, SUBJECTS, generate_exam_set


app = Flask(__name__)
DATA_DIR = Path(__file__).parent / "data"
PROFILE_PATH = DATA_DIR / "profile.json"
BASE_URL = "https://www.oktatas.hu/kozneveles/erettsegi/feladatsorok"


def _ensure_data_store() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if not PROFILE_PATH.exists():
        PROFILE_PATH.write_text(
            json.dumps(
                {
                    "name": "Diak",
                    "target_year": 2027,
                    "streak_days": 0,
                    "generated_sets": 0,
                    "completed_sets": 0,
                    "total_points_earned": 0,
                    "subject_stats": {key: {"generated": 0, "earned": 0, "max": 0} for key in SUBJECTS},
                    "history": [],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


def _load_profile() -> dict[str, Any]:
    _ensure_data_store()
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    # Visszafele kompatibilitas: hianyzo tantargy-statisztikak potlasa.
    for key in SUBJECTS:
        profile.setdefault("subject_stats", {})
        profile["subject_stats"].setdefault(key, {"generated": 0, "earned": 0, "max": 0})
    return profile


def _save_profile(profile: dict[str, Any]) -> None:
    _ensure_data_store()
    PROFILE_PATH.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")


def _normalize_text(content: str) -> list[str]:
    normalized = unicodedata.normalize("NFKD", content.lower())
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.findall(r"[a-z0-9]{3,}", ascii_text)


def score_exam(exam_payload: dict[str, Any], answers: list[str]) -> dict[str, Any]:
    task_results: list[dict[str, Any]] = []
    earned_total = 0
    max_total = 0

    for idx, task in enumerate(exam_payload.get("tasks", [])):
        answer = answers[idx] if idx < len(answers) else ""
        # A szobeli feladatok max_points = 0 -> gyakorlasra szolgalnak, pontozas nelkul.
        max_points = task.get("max_points", 0)
        if max_points <= 0:
            task_results.append(
                {
                    "task_index": idx + 1,
                    "title": task["title"],
                    "max_points": 0,
                    "earned_points": 0,
                    "feedback": "Szóbeli gyakorlófeladat – mondd el hangosan, vedd fel magad, és vesd össze a tippel.",
                }
            )
            continue

        keywords = set(_normalize_text(task["sample_solution"]))
        answer_words = set(_normalize_text(answer))
        overlap = len(keywords & answer_words)
        denominator = max(len(keywords), 1)
        quality_ratio = min(overlap / denominator + (0.15 if len(answer_words) > 25 else 0.0), 1.0)
        points = round(max_points * quality_ratio)
        earned_total += points
        max_total += max_points
        task_results.append(
            {
                "task_index": idx + 1,
                "title": task["title"],
                "max_points": max_points,
                "earned_points": points,
                "feedback": (
                    "Erős válasz, jó kulcsszófedés."
                    if quality_ratio >= 0.75
                    else "Közepes: bővítsd több kulcsfogalommal és pontos példákkal."
                    if quality_ratio >= 0.45
                    else "Fejlesztendő: használd a tippet és építs részletesebb választ."
                ),
            }
        )

    percentage = round((earned_total / max_total) * 100, 1) if max_total else 0
    return {
        "earned_total": earned_total,
        "max_total": max_total,
        "percentage": percentage,
        "task_results": task_results,
    }


def _wrap_text(draw: canvas.Canvas, text: str, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        next_candidate = f"{current} {word}".strip()
        if draw.stringWidth(next_candidate, "Helvetica", 11) <= max_width:
            current = next_candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _build_exam_pdf(exam_payload: dict[str, Any]) -> bytes:
    buff = io.BytesIO()
    draw = canvas.Canvas(buff, pagesize=A4)
    width, height = A4
    y = height - 50

    draw.setFont("Helvetica-Bold", 16)
    draw.drawString(40, y, exam_payload.get("title", "Erettsegi feladatsor"))
    y -= 25
    draw.setFont("Helvetica", 11)
    draw.drawString(
        40,
        y,
        f"Szint: {exam_payload.get('level', '')} | Mod: {exam_payload.get('mode_label', '')} | "
        f"Becsult ido: {exam_payload.get('estimated_minutes', 0)} perc",
    )
    y -= 25

    for idx, task in enumerate(exam_payload.get("tasks", []), start=1):
        if y < 120:
            draw.showPage()
            y = height - 50
        points = task.get("max_points", 0)
        suffix = f" ({points} pont)" if points else " (szóbeli)"
        draw.setFont("Helvetica-Bold", 12)
        draw.drawString(40, y, f"{idx}. {task['title']}{suffix}")
        y -= 16
        draw.setFont("Helvetica", 11)
        for line in _wrap_text(draw, task["prompt"], 510):
            draw.drawString(45, y, line)
            y -= 14
            if y < 80:
                draw.showPage()
                y = height - 50
        y -= 6
        draw.setFont("Helvetica-Oblique", 10)
        draw.drawString(45, y, f"Tipp: {task['hint']}")
        y -= 18

    draw.save()
    buff.seek(0)
    return buff.getvalue()


def _fetch_past_exam_links() -> list[dict[str, str]]:
    fallback = [
        {"title": "Oktatási Hivatal - Érettségi feladatsorok főoldal", "url": BASE_URL},
        {
            "title": "Keresési tipp: matematika feladatsorok",
            "url": "https://www.oktatas.hu/kozneveles/erettsegi/feladatsorok?search=matematika",
        },
        {
            "title": "Keresési tipp: történelem feladatsorok",
            "url": "https://www.oktatas.hu/kozneveles/erettsegi/feladatsorok?search=t%C3%B6rt%C3%A9nelem",
        },
        {
            "title": "Keresési tipp: német feladatsorok",
            "url": "https://www.oktatas.hu/kozneveles/erettsegi/feladatsorok?search=n%C3%A9met",
        },
    ]
    try:
        response = requests.get(BASE_URL, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return fallback

    soup = BeautifulSoup(response.text, "html.parser")
    items: list[dict[str, str]] = []
    for anchor in soup.select("a[href]"):
        text = anchor.get_text(" ", strip=True)
        href = anchor["href"].strip()
        lowered = text.lower()
        if any(keyword in lowered for keyword in ("matematika", "történelem", "irodalom", "német", "nemet", "feladatsor")):
            if not href.startswith("http"):
                href = f"https://www.oktatas.hu{href}" if href.startswith("/") else f"{BASE_URL.rstrip('/')}/{href}"
            items.append({"title": text, "url": href})
        if len(items) >= 24:
            break
    if items:
        return items
    return fallback


@app.get("/")
def index() -> str:
    _ensure_data_store()
    return render_template("index.html", subjects=SUBJECTS, modes=MODES)


@app.get("/api/exam")
def exam() -> Any:
    subject = request.args.get("subject", "matek")
    level = request.args.get("level", "kozep")
    mode = request.args.get("mode", "irasbeli")
    payload = generate_exam_set(subject=subject, level=level, mode=mode)
    profile = _load_profile()
    profile["generated_sets"] += 1
    profile["subject_stats"][payload["subject"]]["generated"] += 1
    profile["history"].append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "generated",
            "subject": payload["subject"],
            "level": level,
            "mode": payload["mode"],
            "title": payload["title"],
        }
    )
    profile["history"] = profile["history"][-50:]
    _save_profile(profile)
    return jsonify(payload)


@app.get("/api/profile")
def get_profile() -> Any:
    return jsonify(_load_profile())


@app.post("/api/profile")
def update_profile() -> Any:
    payload = request.get_json(silent=True) or {}
    profile = _load_profile()
    if "name" in payload and payload["name"]:
        profile["name"] = str(payload["name"])[:64]
    if "target_year" in payload:
        profile["target_year"] = int(payload["target_year"])
    if "streak_days" in payload:
        profile["streak_days"] = max(0, int(payload["streak_days"]))
    _save_profile(profile)
    return jsonify(profile)


@app.post("/api/score")
def score() -> Any:
    payload = request.get_json(silent=True) or {}
    exam_payload = payload.get("exam", {})
    answers = payload.get("answers", [])
    result = score_exam(exam_payload, answers)

    subject = exam_payload.get("subject", "matek")
    if subject not in SUBJECTS:
        subject = "matek"
    profile = _load_profile()
    profile["completed_sets"] += 1
    profile["total_points_earned"] += result["earned_total"]
    profile["subject_stats"][subject]["earned"] += result["earned_total"]
    profile["subject_stats"][subject]["max"] += result["max_total"]
    profile["history"].append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "scored",
            "subject": subject,
            "earned_total": result["earned_total"],
            "max_total": result["max_total"],
            "percentage": result["percentage"],
        }
    )
    profile["history"] = profile["history"][-50:]
    _save_profile(profile)
    return jsonify(result)


@app.post("/api/export/pdf")
def export_pdf() -> Any:
    payload = request.get_json(silent=True) or {}
    exam_payload = payload.get("exam", {})
    pdf_bytes = _build_exam_pdf(exam_payload)
    filename = f"erettsegi_{exam_payload.get('subject', 'general')}_{exam_payload.get('mode', 'irasbeli')}.pdf"
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


@app.get("/api/past-exams")
def past_exams() -> Any:
    items = _fetch_past_exam_links()
    return jsonify({"source": BASE_URL, "items": items})


@app.get("/api/health")
def health() -> Any:
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # Dev run: python app.py
    app.run(debug=True, port=5050)
