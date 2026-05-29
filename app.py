from __future__ import annotations

import io
import json
import random
import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


app = Flask(__name__)
DATA_DIR = Path(__file__).parent / "data"
PROFILE_PATH = DATA_DIR / "profile.json"
BASE_URL = "https://www.oktatas.hu/kozneveles/erettsegi/feladatsorok"


@dataclass
class Task:
    title: str
    prompt: str
    max_points: int
    hint: str
    sample_solution: str
    source: str
    topic: str


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
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def _save_profile(profile: dict[str, Any]) -> None:
    _ensure_data_store()
    PROFILE_PATH.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")


SUBJECTS = {
    "matek": "Matematika",
    "irodalom": "Irodalom",
    "tortenelem": "Történelem",
    "nemet": "Német nyelv",
}


def _math_tasks(level: str) -> list[Task]:
    a = random.randint(2, 8)
    b = random.randint(1, 9)
    c = random.randint(1, 6)
    p = random.randint(100, 400)
    q = random.randint(10, 40)
    n = random.randint(12, 25)
    wage = random.randint(2200, 4200)
    discount = random.choice([10, 15, 20, 25])

    tasks = [
        Task(
            title="Algebra és egyenlet",
            prompt=f"Oldd meg az alábbi egyenletet a valós számok halmazán: {a}x^2 - {b}x - {c} = 0.",
            max_points=8,
            hint="Használd a másodfokú egyenlet megoldóképletét, majd ellenőrizd a gyököket.",
            sample_solution=(
                f"A diszkrimináns: D = (-{b})^2 - 4*{a}*(-{c}) = {b**2 + 4*a*c}. "
                "Innen x1,2 = (b ± √D) / (2a)."
            ),
            source="Új, 2027-es gyakorlófeladat",
            topic="Algebra",
        ),
        Task(
            title="Szöveges feladat százalékszámítással",
            prompt=(
                f"Egy termék ára {p} Ft, majd {discount}% kedvezményt kap, "
                f"utána további {q}% áremelést. Mennyi a végső ár?"
            ),
            max_points=10,
            hint="Először szorozz (1-kedvezmény), majd (1+áremelés) tényezővel.",
            sample_solution=(
                f"Végső ár = {p} * (1-{discount/100:.2f}) * (1+{q/100:.2f}) Ft."
            ),
            source="Korábbi érettségik feladattípusai alapján",
            topic="Százalékszámítás",
        ),
        Task(
            title="Statisztika",
            prompt=(
                f"Egy osztályban {n} tanuló van. A havi zsebpénzük átlaga {wage} Ft, "
                "szórása 650 Ft. Értelmezd az átlagot és a szórást, majd készíts rövid következtetést!"
            ),
            max_points=7,
            hint="Az átlag a központi értéket, a szórás az adatok ingadozását mutatja.",
            sample_solution=(
                "Átlag: tipikus zsebpénz. Szórás: az egyéni értékek átlagtól való eltérése. "
                "Nagyobb szórás nagyobb különbségeket jelez."
            ),
            source="Új, kompetenciafókuszú feladat",
            topic="Statisztika",
        ),
        Task(
            title="Geometria",
            prompt="Egy háromszög oldalai: 7 cm, 8 cm, 9 cm. Számítsd ki a területét (Heron-képlettel)!",
            max_points=9,
            hint="Félkerület s = (a+b+c)/2, terület T = √(s(s-a)(s-b)(s-c)).",
            sample_solution="s = 12, T = √(12*5*4*3) = √720 ≈ 26,83 cm².",
            source="Korábbi középszintű geometriás feladattípus alapján",
            topic="Geometria",
        ),
    ]
    if level == "emelt":
        tasks.append(
            Task(
                title="Valószínűségszámítás (emelt)",
                prompt=(
                    "Egy dobozban 5 piros, 4 kék és 3 zöld golyó van. "
                    "Visszatevés nélkül húzunk 3 golyót. Mennyi annak a valószínűsége, "
                    "hogy pontosan 2 piros legyen köztük?"
                ),
                max_points=12,
                hint="Használd a kombinációkat: kedvező / összes eset.",
                sample_solution="P = (C(5,2)*C(7,1)) / C(12,3).",
                source="Új, emelt szintű kombinatorikai feladat",
                topic="Valószínűség",
            )
        )
    return tasks


def _literature_tasks(level: str) -> list[Task]:
    tasks = [
        Task(
            title="Műelemzés",
            prompt=(
                "Elemezd egy 20. századi magyar vers (pl. József Attila vagy Radnóti) "
                "hangnemét, motívumrendszerét és versbeszédét kb. 300-350 szóban!"
            ),
            max_points=20,
            hint="Térj ki a megszólaló helyzetére, képekre, ritmusra és történeti kontextusra.",
            sample_solution=(
                "Erős válasz: világos tételmondat, idézetekkel alátámasztott elemzés, "
                "a forma és tartalom kapcsolatának bemutatása."
            ),
            source="Korábbi írásbeli elemzési szempontrendszer alapján",
            topic="Líraelemzés",
        ),
        Task(
            title="Összehasonlító esszé",
            prompt=(
                "Hasonlíts össze két tanult epikai művet a hősábrázolás szempontjából "
                "(pl. egy klasszikus és egy modern alkotást)!"
            ),
            max_points=18,
            hint="Legyen világos szemponttáblád: jellem, konfliktus, értékrend, narráció.",
            sample_solution="A jó megoldás párhuzamos szerkezetben, példákkal hasonlít.",
            source="Új, 2027-es összehasonlító feladat",
            topic="Epika",
        ),
        Task(
            title="Nyelvi-stilisztikai feladat",
            prompt="Azonosíts és értelmezz legalább 5 stíluseszközt egy rövid prózarészletben!",
            max_points=12,
            hint="Pl. metafora, megszemélyesítés, alliteráció, ismétlés, ellentét.",
            sample_solution=(
                "Minden eszköznél: megnevezés + idézet + funkció magyarázata a szövegben."
            ),
            source="Korábbi középszintű feladattípusok mintájára",
            topic="Stilisztika",
        ),
    ]
    if level == "emelt":
        tasks.append(
            Task(
                title="Irodalomtörténeti érvelés (emelt)",
                prompt=(
                    "Fejtsd ki: hogyan változott a költőszerep a romantikától a modernségig, "
                    "konkrét szerzőkkel és művekkel!"
                ),
                max_points=25,
                hint="Korszakonként legalább 1-1 szerző és 1 tételmondat.",
                sample_solution="A válasz korszaklogikára épít, és művekre hivatkozik.",
                source="Új, emelt szintű esszéfeladat",
                topic="Irodalomtörténet",
            )
        )
    return tasks


def _history_tasks(level: str) -> list[Task]:
    year = random.choice([1848, 1867, 1918, 1945, 1956, 1989])
    tasks = [
        Task(
            title="Forráselemzés",
            prompt=(
                "Elemezz egy történelmi forrásrészletet! Térj ki a szerző nézőpontjára, "
                "a keletkezés körülményeire és a forrás megbízhatóságára."
            ),
            max_points=14,
            hint="Különítsd el a tényt, véleményt és propagandisztikus elemeket.",
            sample_solution=(
                "Jó válasz: pontos korszakmeghatározás, kontextus, kritikus forráshasználat."
            ),
            source="Korábbi írásbeli forráselemző feladatok mintája",
            topic="Forráselemzés",
        ),
        Task(
            title="Magyar történelem esszé",
            prompt=f"Mutasd be a(z) {year}-hez kapcsolódó események rövid és hosszú távú következményeit!",
            max_points=16,
            hint="Szerkezet: előzmény -> esemény -> következmény (politikai, társadalmi, gazdasági).",
            sample_solution="A magas pontszámú megoldás ok-okozati láncokat is megmutat.",
            source="Új, 2027-es témavariáció",
            topic="Magyar történelem",
        ),
        Task(
            title="Egyetemes történelem",
            prompt=(
                "Készíts időrendi táblázatot 6 kulcseseménnyel a hidegháború korszakából, "
                "majd röviden értékeld ezek jelentőségét!"
            ),
            max_points=12,
            hint="Ne csak dátumokat írj: minden ponthoz legyen rövid magyarázat.",
            sample_solution="Pl. 1947 Truman-doktrína, 1962 kubai rakétaválság, stb.",
            source="Korábbi adat- és időrend fókuszú feladatok alapján",
            topic="20. század",
        ),
    ]
    if level == "emelt":
        tasks.append(
            Task(
                title="Komplex összehasonlítás (emelt)",
                prompt=(
                    "Hasonlíts össze két eltérő politikai rendszert (pl. dualizmus és Horthy-korszak) "
                    "államszervezet, társadalompolitika és külpolitika szempontjából!"
                ),
                max_points=22,
                hint="Készíts összehasonlító szempontmátrixot és példákat.",
                sample_solution="A jó esszé mindhárom szempontot következetesen végigviszi.",
                source="Új, emelt szintű kompetenciamérő feladat",
                topic="Összehasonlító esszé",
            )
        )
    return tasks


def _german_tasks(level: str) -> list[Task]:
    city = random.choice(["Berlin", "Wien", "München", "Hamburg"])
    tasks = [
        Task(
            title="Leseverstehen",
            prompt=(
                "Olvass el egy kb. 250 szavas német szöveget az iskolai életről, "
                "majd válaszolj 8 igaz-hamis és 4 rövid kifejtős kérdésre!"
            ),
            max_points=16,
            hint="A válaszoknál keresd a kulcsszavak szinonimáit a szövegben.",
            sample_solution="Pont jár a helyes információ-visszakeresésért és nyelvi pontosságért.",
            source="Korábbi német érettségik feladatszerkezete alapján",
            topic="Olvasott szöveg értése",
        ),
        Task(
            title="Hörverstehen",
            prompt=(
                "Hallásértés szimuláció: képzeld el, hogy egy rádióinterjút hallgatsz a környezetvédelemről. "
                "Írj 10 kulcspontot németül!"
            ),
            max_points=12,
            hint="Rövid, információszerű mondatokban rögzítsd a lényeget.",
            sample_solution="A jó válasz témánként csoportosít és tömören fogalmaz.",
            source="Új, 2027-es kompetenciaalapú hallásértés-feladat",
            topic="Hallott szöveg értése",
        ),
        Task(
            title="Schreiben",
            prompt=(
                f"Írj 140-170 szavas e-mailt németül egy {city}-i csereprogramról, "
                "amelyben érdeklődsz a szállásról, programokról és költségekről!"
            ),
            max_points=18,
            hint="Legyen megszólítás, világos bekezdések, udvarias zárás.",
            sample_solution=(
                "Szerkezet: Einleitung -> Fragen zu Unterkunft/Programm/Kosten -> Schlussformel."
            ),
            source="Korábbi levélírás-feladatok mintájára",
            topic="Íráskészség",
        ),
    ]
    if level == "emelt":
        tasks.append(
            Task(
                title="Mediation (emelt)",
                prompt=(
                    "Foglalj össze németül egy magyar nyelvű, kb. 200 szavas cikket "
                    "iskolai stresszkezelés témában (90-120 szó)!"
                ),
                max_points=20,
                hint="Ne szó szerint fordíts: információt közvetíts célzottan.",
                sample_solution="A jó közvetítés tömör, pontos, koherens.",
                source="Új, emelt szintű közvetítési feladat",
                topic="Sprachmittlung",
            )
        )
    return tasks


def generate_exam_set(subject: str, level: str) -> dict[str, Any]:
    mapping = {
        "matek": _math_tasks,
        "irodalom": _literature_tasks,
        "tortenelem": _history_tasks,
        "nemet": _german_tasks,
    }
    task_builder = mapping.get(subject, _math_tasks)
    tasks = [asdict(task) for task in task_builder(level)]

    return {
        "title": f"{SUBJECTS.get(subject, subject)} - 2027 Prémium gyakorlófeladatsor",
        "subject": subject,
        "subject_label": SUBJECTS.get(subject, subject),
        "level": level,
        "estimated_minutes": 90 if level == "kozep" else 120,
        "tasks": tasks,
    }


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
        keywords = set(_normalize_text(task["sample_solution"]))
        answer_words = set(_normalize_text(answer))
        overlap = len(keywords & answer_words)
        denominator = max(len(keywords), 1)
        quality_ratio = min(overlap / denominator + (0.15 if len(answer_words) > 25 else 0.0), 1.0)
        points = round(task["max_points"] * quality_ratio)
        earned_total += points
        max_total += task["max_points"]
        task_results.append(
            {
                "task_index": idx + 1,
                "title": task["title"],
                "max_points": task["max_points"],
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
    draw.drawString(40, y, exam_payload["title"])
    y -= 25
    draw.setFont("Helvetica", 11)
    draw.drawString(40, y, f"Szint: {exam_payload['level']} | Becsult ido: {exam_payload['estimated_minutes']} perc")
    y -= 25

    for idx, task in enumerate(exam_payload["tasks"], start=1):
        if y < 120:
            draw.showPage()
            y = height - 50
        draw.setFont("Helvetica-Bold", 12)
        draw.drawString(40, y, f"{idx}. {task['title']} ({task['max_points']} pont)")
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
    return render_template("index.html", subjects=SUBJECTS)


@app.get("/api/exam")
def exam() -> Any:
    subject = request.args.get("subject", "matek")
    level = request.args.get("level", "kozep")
    payload = generate_exam_set(subject=subject, level=level)
    profile = _load_profile()
    profile["generated_sets"] += 1
    profile["subject_stats"][subject]["generated"] += 1
    profile["history"].append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "generated",
            "subject": subject,
            "level": level,
            "title": payload["title"],
        }
    )
    profile["history"] = profile["history"][-50:]
    _save_profile(profile)
    return jsonify(payload)


@app.get("/api/profile")
def get_profile() -> Any:
    profile = _load_profile()
    return jsonify(profile)


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
    filename = f"erettsegi_{exam_payload.get('subject', 'general')}_{exam_payload.get('level', 'kozep')}.pdf"
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
