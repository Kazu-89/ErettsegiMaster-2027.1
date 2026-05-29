"""Feladattartalom: irasbeli es szobeli erettsegi feladatok tantargyankent.

A szobeli feladatok felepitese a hivatalos vizsgaszerkezetet koveti:
- Irodalom / Tortenelem: tetelek (a tortenelemnel forrasokkal),
- Nemet: tarsalgas + szerepjatek/vita + onallo temakifejtes,
- Matematika: tetel-kifejtes (definiciok, tetelek, bizonyitas, alkalmazas).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, asdict
from typing import Any, Callable


@dataclass
class Task:
    title: str
    prompt: str
    max_points: int
    hint: str
    sample_solution: str
    source: str
    topic: str


SUBJECTS = {
    "matek": "Matematika",
    "irodalom": "Irodalom",
    "tortenelem": "Történelem",
    "nemet": "Német nyelv",
}

MODES = {
    "irasbeli": "Írásbeli",
    "szobeli": "Szóbeli",
}


def _pick(pool: list[Task], k: int) -> list[Task]:
    if k >= len(pool):
        return random.sample(pool, len(pool))
    return random.sample(pool, k)


# ---------------------------------------------------------------------------
# MATEMATIKA
# ---------------------------------------------------------------------------

def _math_written(level: str) -> list[Task]:
    a, b, c = random.randint(2, 8), random.randint(1, 9), random.randint(1, 6)
    p, q = random.randint(100, 400), random.randint(10, 40)
    n, wage = random.randint(12, 25), random.randint(2200, 4200)
    discount = random.choice([10, 15, 20, 25])
    r = random.randint(3, 9)
    a1, d = random.randint(2, 9), random.randint(2, 7)
    base = random.choice([2, 3, 5])
    exp = random.randint(2, 5)

    pool = [
        Task("Másodfokú egyenlet",
             f"Oldd meg a valós számok halmazán: {a}x² - {b}x - {c} = 0.",
             8, "Használd a megoldóképletet, és ellenőrizd a diszkriminánst.",
             f"D = {b}² + 4·{a}·{c} = {b*b + 4*a*c}. x₁,₂ = (b ± √D)/(2a).",
             "Új, 2027-es gyakorlófeladat", "Algebra"),
        Task("Százalékszámítás",
             f"Egy termék ára {p} Ft. Először {discount}% kedvezményt, majd {q}% áremelést kap. Mennyi a végső ár?",
             10, "Szorozz (1 - kedvezmény), majd (1 + áremelés) tényezővel.",
             f"Végső ár = {p}·(1-{discount/100:.2f})·(1+{q/100:.2f}) Ft.",
             "Korábbi érettségik feladattípusa alapján", "Százalék"),
        Task("Statisztika",
             f"Egy {n} fős osztály zsebpénzének átlaga {wage} Ft, szórása 650 Ft. Értelmezd az adatokat!",
             7, "Átlag = központi érték, szórás = ingadozás mértéke.",
             "Az átlag a tipikus értéket, a szórás az átlagtól való eltérést mutatja.",
             "Kompetenciafókuszú feladat", "Statisztika"),
        Task("Geometria – terület",
             "Egy háromszög oldalai 7, 8 és 9 cm. Számítsd ki a területét Heron-képlettel!",
             9, "s = (a+b+c)/2, T = √(s(s-a)(s-b)(s-c)).",
             "s = 12, T = √(12·5·4·3) = √720 ≈ 26,83 cm².",
             "Középszintű geometria feladattípus", "Geometria"),
        Task("Számtani sorozat",
             f"Egy számtani sorozat első tagja {a1}, különbsége {d}. Mennyi az első 20 tag összege?",
             8, "Sₙ = n·(2a₁+(n-1)d)/2.",
             f"S₂₀ = 20·(2·{a1}+19·{d})/2 = {10*(2*a1 + 19*d)}.",
             "Új gyakorlófeladat", "Sorozatok"),
        Task("Exponenciális egyenlet",
             f"Oldd meg: {base}^x = {base**exp}.",
             6, "Azonos alapnál a kitevők egyenlők.",
             f"x = {exp}.",
             "Korábbi feladattípus alapján", "Exponenciális"),
        Task("Trigonometria",
             f"Egy derékszögű háromszög egyik befogója {r} cm, a vele szemközti szög 30°. Mekkora az átfogó?",
             7, "sin(szög) = szemközti befogó / átfogó.",
             f"átfogó = {r}/sin30° = {r}/0,5 = {2*r} cm.",
             "Új gyakorlófeladat", "Trigonometria"),
        Task("Koordinátageometria",
             "Add meg az A(1;2) és B(5;6) pontok távolságát és a felezőpontot!",
             8, "d = √((x₂-x₁)²+(y₂-y₁)²), F = ((x₁+x₂)/2; (y₁+y₂)/2).",
             "d = √(16+16) = √32 ≈ 5,66; F(3;4).",
             "Középszintű feladattípus", "Koordinátageometria"),
        Task("Kombinatorika",
             "Hányféleképpen ülhet le 6 tanuló egy padsorba?",
             6, "Permutáció: n!.",
             "6! = 720 lehetőség.",
             "Új gyakorlófeladat", "Kombinatorika"),
        Task("Logaritmus",
             "Számítsd ki: log₂ 8 + log₃ 27 értékét!",
             6, "logₐ aᵏ = k.",
             "log₂8 = 3, log₃27 = 3, összeg = 6.",
             "Korábbi feladattípus alapján", "Logaritmus"),
    ]
    if level == "emelt":
        pool.append(
            Task("Valószínűség (emelt)",
                 "Egy dobozban 5 piros, 4 kék, 3 zöld golyó van. Visszatevés nélkül húzunk 3-at. "
                 "Mennyi a valószínűsége, hogy pontosan 2 piros lesz?",
                 12, "Kedvező / összes = C(5,2)·C(7,1) / C(12,3).",
                 "P = (10·7)/220 = 70/220 ≈ 0,318.",
                 "Emelt szintű kombinatorika", "Valószínűség"))
        pool.append(
            Task("Térgeometria (emelt)",
                 "Egy gömb sugara 6 cm. Számítsd ki a felszínét és a térfogatát!",
                 11, "A = 4r²π, V = (4/3)r³π.",
                 "A = 144π ≈ 452,4 cm², V = 288π ≈ 904,8 cm³.",
                 "Emelt szintű feladat", "Térgeometria"))
    return _pick(pool, 6 if level == "emelt" else 5)


def _math_oral(level: str) -> list[Task]:
    pool = [
        Task("Tétel: Függvények",
             "Fejtsd ki a függvények témakört: definíció, megadási módok, alaptulajdonságok "
             "(értelmezési tartomány, értékkészlet, monotonitás, szélsőérték), példák.",
             0, "Kezdj a definícióval, majd példákkal szemléltesd a tulajdonságokat.",
             "Definíció + nevezetes függvények (lineáris, másodfokú, exponenciális) tulajdonságai.",
             "Szóbeli tétel-kifejtés", "Függvények"),
        Task("Tétel: Számtani és mértani sorozat",
             "Mondd ki a számtani és mértani sorozat definícióját, az n-edik tag és az összegképletet, "
             "és vezesd le a számtani sorozat összegképletét!",
             0, "Az összegképlet levezetése a kulcs (Gauss-trükk).",
             "aₙ = a₁+(n-1)d; Sₙ = n(a₁+aₙ)/2. Mértani: aₙ = a₁qⁿ⁻¹.",
             "Szóbeli tétel-kifejtés", "Sorozatok"),
        Task("Tétel: Trigonometria",
             "Definiáld a hegyesszögek szögfüggvényeit, ismertesd a nevezetes szögek értékeit "
             "és a szinusztételt!",
             0, "Egységkör segít az általánosításban.",
             "sin, cos, tg definíciók; sin30/45/60; szinusztétel: a/sinα = 2R.",
             "Szóbeli tétel-kifejtés", "Trigonometria"),
        Task("Tétel: Valószínűség-számítás",
             "Ismertesd a klasszikus valószínűség fogalmát, a műveleteket (komplementer, összeg, szorzat) "
             "és mondj példákat!",
             0, "Kedvező/összes eset; térj ki a független eseményekre.",
             "P(A) = kedvező/összes; P(A∪B) = P(A)+P(B)-P(A∩B).",
             "Szóbeli tétel-kifejtés", "Valószínűség"),
        Task("Tétel: Térfogat és felszín",
             "Ismertesd a hasáb, henger, gúla, kúp és gömb térfogat- és felszínképleteit, alkalmazással!",
             0, "Csoportosíts: egyenes testek vs. forgástestek.",
             "Pl. henger: V = r²πm, A = 2rπ(r+m); gömb: V = (4/3)r³π.",
             "Szóbeli tétel-kifejtés", "Térgeometria"),
        Task("Tétel: Halmazok és műveletek",
             "Definiáld a halmaz fogalmát, a halmazműveleteket (unió, metszet, különbség, komplementer) "
             "és a De Morgan-azonosságokat!",
             0, "Venn-diagram szemléltetés ajánlott.",
             "A∪B, A∩B, A\\B; De Morgan: (A∪B)' = A'∩B'.",
             "Szóbeli tétel-kifejtés", "Halmazok"),
        Task("Tétel: Logaritmus",
             "Definiáld a logaritmust, ismertesd az azonosságait és alkalmazásukat egyenletmegoldásban!",
             0, "logₐb azonosságok: szorzat, hányados, hatvány.",
             "logₐ(xy)=logₐx+logₐy; logₐ(xⁿ)=n·logₐx.",
             "Szóbeli tétel-kifejtés", "Logaritmus"),
        Task("Tétel: Vektorok",
             "Ismertesd a vektor fogalmát, a műveleteket és a skaláris szorzatot, geometriai alkalmazással!",
             0, "Térj ki a skaláris szorzat és a merőlegesség kapcsolatára.",
             "a·b = |a||b|cosφ; merőleges, ha a·b = 0.",
             "Szóbeli tétel-kifejtés", "Vektorok"),
    ]
    return _pick(pool, 3)


# ---------------------------------------------------------------------------
# IRODALOM (magyar nyelv és irodalom)
# ---------------------------------------------------------------------------

def _literature_written(level: str) -> list[Task]:
    pool = [
        Task("Szövegértés",
             "Olvass el egy kb. 600 szavas ismeretterjesztő szöveget, majd válaszolj a tartalmi, "
             "szerkezeti és nyelvi kérdésekre!",
             40, "Keresd a kulcsmondatokat, és idézz pontosan a szövegből.",
             "Pontos információ-visszakeresés, a szöveg logikájának megértése.",
             "Korábbi írásbeli szövegértés mintája", "Szövegértés"),
        Task("Műértelmező szövegalkotás",
             "Értelmezz egy 20. századi magyar verset (hangnem, motívumok, versbeszéd) kb. 400 szóban!",
             25, "Világos tételmondat, idézetekkel alátámasztott elemzés.",
             "A forma és tartalom kapcsolatának bemutatása, koherens szerkezet.",
             "Írásbeli elemzési szempontrendszer alapján", "Műértelmezés"),
        Task("Összehasonlító elemzés",
             "Hasonlíts össze két lírai alkotást egy közös motívum (pl. idő, haza, szerelem) mentén!",
             25, "Szempontok: téma, képek, hangnem, forma, üzenet.",
             "Párhuzamos szerkezet, idézetek, a különbségek kiemelése.",
             "Új, 2027-es összehasonlító feladat", "Összehasonlítás"),
        Task("Érvelő / gyakorlati szövegalkotás",
             "Írj érvelő esszét egy megadott idézet kapcsán (pl. az olvasás szerepe a 21. században)!",
             25, "Tézis – érvek (legalább 3) – ellenérv cáfolata – konklúzió.",
             "Logikus felépítés, példák, meggyőző nyelvhasználat.",
             "Írásbeli szövegalkotás mintája", "Érvelés"),
        Task("Nyelvi-stilisztikai elemzés",
             "Azonosíts és értelmezz legalább 5 stíluseszközt egy rövid prózarészletben!",
             15, "Megnevezés + idézet + funkció a szövegben.",
             "Pl. metafora, megszemélyesítés, alliteráció, ellentét, ismétlés.",
             "Középszintű feladattípus mintája", "Stilisztika"),
    ]
    if level == "emelt":
        pool.append(
            Task("Irodalomtörténeti érvelés (emelt)",
                 "Mutasd be a költőszerep változását a romantikától a modernségig, konkrét szerzőkkel!",
                 25, "Korszakonként 1-1 szerző és tételmondat.",
                 "Korszaklogika, művekre hivatkozás, fejlődési ív.",
                 "Emelt szintű esszéfeladat", "Irodalomtörténet"))
    return _pick(pool, 4 if level == "emelt" else 3)


_LIT_IRODALMI = [
    ("Petőfi Sándor tájköltészete", "Az alföld-motívum, a szabadság eszméje és a népiesség Petőfi lírájában."),
    ("Arany János balladái", "A ballada műfaji jegyei, lélektani ábrázolás (pl. Ágnes asszony, A walesi bárdok)."),
    ("Ady Endre létköltészete", "Az új versbeszéd, a szimbólumok és a magyarság-élmény."),
    ("József Attila kései költészete", "A létösszegző versek, a táj- és lélekrajz (pl. Téli éjszaka, Eszmélet)."),
    ("Kosztolányi Dezső prózája", "Az Esti Kornél novellák szerkezete és a homo aestheticus."),
    ("Mikszáth Kálmán novellisztikája", "Az anekdotikus elbeszélésmód és a társadalomkritika."),
    ("Madách Imre: Az ember tragédiája", "A drámai költemény szerkezete, az ember és az eszmék küzdelme."),
    ("Katona József: Bánk bán", "A dráma konfliktusrendszere és a tragikus hős."),
    ("Balassi Bálint költészete", "A vitézi, szerelmi és istenes versek; a Balassi-strófa."),
    ("Shakespeare drámaművészete", "A tragédia szerkezete és a jellemábrázolás (pl. Hamlet, Romeo és Júlia)."),
]

_LIT_NYELVI = [
    ("A kommunikáció tényezői és funkciói", "Jakobson modellje és a nyelvi funkciók."),
    ("A magyar nyelv szófaji rendszere", "Az alapszófajok, viszonyszók és mondatszók."),
    ("A mondat szerkezete", "Az egyszerű és összetett mondatok, a mellé- és alárendelés."),
    ("Stílusrétegek", "A társalgási, hivatalos, tudományos, publicisztikai és szépirodalmi stílus."),
    ("A szövegkohézió eszközei", "A grammatikai és jelentésbeli kapcsolóelemek."),
    ("A retorika és az érvelés", "A beszéd felépítése, az érvtípusok és a meggyőzés eszközei."),
    ("Nyelvváltozatok, nyelvjárások", "A nyelv vízszintes és függőleges tagolódása."),
    ("A helyesírás alapelvei", "A kiejtés, a szóelemzés, a hagyomány és az egyszerűsítés elve."),
]


def _literature_oral(level: str) -> list[Task]:
    irod = random.sample(_LIT_IRODALMI, 2)
    nyelv = random.sample(_LIT_NYELVI, 1)
    tasks: list[Task] = []
    for title, desc in irod:
        tasks.append(Task(
            f"Irodalmi tétel: {title}",
            f"Fejtsd ki önállóan a következő tételt: {title}. {desc}",
            0,
            "Tételmondat + művek/idézetek + a téma kifejtése logikus szerkezetben.",
            "Pontos művek, fogalmak és a szerző életművébe ágyazás.",
            "Szóbeli tétel (irodalom)", "Irodalmi tétel"))
    for title, desc in nyelv:
        tasks.append(Task(
            f"Magyar nyelvi tétel: {title}",
            f"Fejtsd ki a következő nyelvi tételt: {title}. {desc}",
            0,
            "Definíciók + példák + rendszerezés.",
            "Szabatos fogalomhasználat, saját példák.",
            "Szóbeli tétel (magyar nyelv)", "Nyelvi tétel"))
    return tasks


# ---------------------------------------------------------------------------
# TÖRTÉNELEM
# ---------------------------------------------------------------------------

def _history_written(level: str) -> list[Task]:
    year = random.choice([1848, 1867, 1918, 1920, 1945, 1956, 1989])
    pool = [
        Task("Forráselemzés",
             "Elemezz egy történelmi forrásrészletet: szerző nézőpontja, keletkezés körülményei, megbízhatóság.",
             14, "Különítsd el a tényt, a véleményt és a propagandát.",
             "Pontos korszakolás, kontextus, kritikus forráshasználat.",
             "Írásbeli forráselemzés mintája", "Forráselemzés"),
        Task("Rövid esszé – magyar történelem",
             f"Mutasd be a(z) {year}-hez kötődő események rövid és hosszú távú következményeit!",
             16, "Előzmény → esemény → következmény (politikai, társadalmi, gazdasági).",
             "Ok-okozati láncok, pontos adatok, fogalmak.",
             "Új, 2027-es témavariáció", "Magyar történelem"),
        Task("Hosszú esszé – egyetemes történelem",
             "Készíts elemzést a hidegháború kialakulásáról és jellemzőiről (1945–1962)!",
             18, "Szembenálló blokkok, kulcsesemények, fogalmak (pl. vasfüggöny).",
             "1947 Truman-doktrína, 1949 NATO, 1962 kubai rakétaválság.",
             "Adat- és időrend fókuszú feladat", "Egyetemes történelem"),
        Task("Topográfia és kronológia",
             "Helyezd el térben és időben a megadott 6 eseményt, és kösd őket a megfelelő helyszínhez!",
             10, "Használj évszám–helyszín párokat.",
             "Pontos évszámok és földrajzi helyek megfeleltetése.",
             "Középszintű feladattípus", "Topográfia"),
        Task("Fogalommeghatározás",
             "Határozz meg 6 történelmi fogalmat (pl. jobbágyfelszabadítás, dualizmus, reformáció)!",
             8, "Lényegre törő, pontos definíciók.",
             "Minden fogalomnál kulcselem + korszak.",
             "Korábbi feladattípus alapján", "Fogalmak"),
    ]
    if level == "emelt":
        pool.append(
            Task("Komplex összehasonlítás (emelt)",
                 "Hasonlíts össze két politikai rendszert (pl. dualizmus és Horthy-korszak) "
                 "államszervezet, társadalom és külpolitika szempontjából!",
                 22, "Összehasonlító szempontmátrix és példák.",
                 "Mindhárom szempont következetes végigvitele.",
                 "Emelt szintű kompetenciamérő feladat", "Összehasonlítás"))
    return _pick(pool, 4 if level == "emelt" else 3)


_HIST_TETELEK = [
    ("Az athéni demokrácia", "kép (vázakép)"),
    ("Szent István államszervezése", "szöveges forrás (törvények)"),
    ("Hunyadi Mátyás központosított állama", "szöveges forrás"),
    ("A reformáció és hatása", "térkép"),
    ("A Rákóczi-szabadságharc", "szöveges forrás"),
    ("A felvilágosodás és a francia forradalom", "szöveges forrás"),
    ("Az 1848–49-es forradalom és szabadságharc", "kép + szöveg"),
    ("A kiegyezés és a dualizmus kora", "statisztikai grafikon"),
    ("Az első világháború", "térkép"),
    ("Trianon és következményei", "térkép + statisztika"),
    ("A Horthy-korszak", "szöveges forrás"),
    ("A második világháború", "térkép"),
    ("A holokauszt", "szöveges forrás (visszaemlékezés)"),
    ("Az 1956-os forradalom", "kép + szöveg"),
    ("A Kádár-korszak mindennapjai", "statisztikai adatsor"),
    ("A rendszerváltás (1989–90)", "szöveges forrás"),
]


def _history_oral(level: str) -> list[Task]:
    chosen = random.sample(_HIST_TETELEK, 3)
    felkeszules = 30
    felelet = "10–15 perc" if level == "kozep" else "kb. 20 perc"
    tasks: list[Task] = []
    for title, src in chosen:
        tasks.append(Task(
            f"Történelmi tétel: {title}",
            f"Fejtsd ki a tételt a mellékelt forrás ({src}) felhasználásával: {title}. "
            f"Felkészülési idő: {felkeszules} perc, felelet: {felelet}. Atlasz használható.",
            0,
            "Szerkezet: feladatmegértés → tér-idő tájékozódás → forráselemzés → összefüggések.",
            "Pontos szaknyelv, forrásra hivatkozás, ok-okozati összefüggések, történelmi gondolkodás.",
            "Szóbeli tétel (történelem)", "Történelmi tétel"))
    return tasks


# ---------------------------------------------------------------------------
# NÉMET NYELV
# ---------------------------------------------------------------------------

def _german_written(level: str) -> list[Task]:
    city = random.choice(["Berlin", "Wien", "München", "Hamburg"])
    pool = [
        Task("Leseverstehen",
             "Olvass el egy kb. 250 szavas német szöveget, majd válaszolj 8 igaz-hamis és 4 kifejtős kérdésre!",
             16, "Keresd a kulcsszavak szinonimáit a szövegben.",
             "Helyes információ-visszakeresés és nyelvi pontosság.",
             "Német érettségi feladatszerkezete alapján", "Olvasott szöveg"),
        Task("Sprachbausteine / Nyelvhelyesség",
             "Egészítsd ki a hiányos német szöveget a megfelelő nyelvtani és lexikai elemekkel (15 hely)!",
             15, "Figyelj az esetekre, igeidőkre és elöljárószókra.",
             "Pontos nyelvtani szerkezetek és kollokációk.",
             "Korábbi nyelvhelyesség-feladat mintája", "Nyelvhelyesség"),
        Task("Hörverstehen",
             "Hallott szöveg: jegyzetelj egy rádióinterjút a környezetvédelemről, írj 10 kulcspontot németül!",
             12, "Rövid, információs mondatokban rögzíts.",
             "Témánkénti csoportosítás, tömör fogalmazás.",
             "Kompetenciaalapú hallásértés-feladat", "Hallott szöveg"),
        Task("Schreiben – E-Mail",
             f"Írj 140–170 szavas e-mailt egy {city}-i csereprogramról: érdeklődj szállásról, programokról, költségekről!",
             18, "Megszólítás, világos bekezdések, udvarias zárás.",
             "Einleitung → Fragen (Unterkunft/Programm/Kosten) → Schlussformel.",
             "Levélírás-feladat mintája", "Íráskészség"),
    ]
    if level == "emelt":
        pool.append(
            Task("Schreiben – Meinungsäußerung (emelt)",
                 "Írj 200–250 szavas véleménykifejtő szöveget a közösségi média hatásairól!",
                 20, "Tézis, érvek, példák, konklúzió – kohézív szerkezet.",
                 "Árnyalt érvelés, gazdag szókincs, helyes kötőszóhasználat.",
                 "Emelt szintű íráskészség-feladat", "Íráskészség"))
        pool.append(
            Task("Sprachmittlung / Mediation (emelt)",
                 "Foglalj össze németül egy magyar nyelvű, kb. 200 szavas cikket (90–120 szó)!",
                 18, "Ne szó szerint fordíts: információt közvetíts célzottan.",
                 "Tömör, pontos, koherens közvetítés.",
                 "Emelt szintű közvetítési feladat", "Sprachmittlung"))
    return _pick(pool, 5 if level == "emelt" else 4)


_GER_THEMEN = [
    ("Familie und Freundschaft", "Kapcsolatok, generációk, barátság szerepe."),
    ("Schule und Bildung", "Iskolarendszer, tanulás, jövőbeli tervek."),
    ("Freizeit und Hobbys", "Szabadidő, sport, közösségi élet."),
    ("Reisen und Tourismus", "Utazási szokások, célpontok, élmények."),
    ("Umwelt und Umweltschutz", "Környezetvédelem, fenntarthatóság, klímaváltozás."),
    ("Gesundheit und Lebensweise", "Egészséges életmód, táplálkozás, stressz."),
    ("Technik und Medien", "Digitális eszközök, közösségi média, internet."),
    ("Arbeit und Beruf", "Pályaválasztás, munka világa, diákmunka."),
    ("Wohnen", "Lakhatás, város vs. vidék, lakóhely."),
    ("Feste und Traditionen", "Ünnepek, szokások, kultúra."),
]


def _german_oral(level: str) -> list[Task]:
    thema1, desc1 = random.choice(_GER_THEMEN)
    thema2, desc2 = random.choice([t for t in _GER_THEMEN if t[0] != thema1])
    dauer = "15 perc" if level == "kozep" else "20 perc"

    tasks = [
        Task("1. Társalgás (Konversation)",
             f"Bemelegítő beszélgetés a(z) „{thema1}” témában. Válaszolj a vizsgáztató kérdéseire németül! "
             "(Ez a rész a vizsgán nem számít a pontozásba, de remek gyakorlás.)",
             0, "Beszélj természetesen, egész mondatokban; kérdezz vissza, ha kell.",
             "Folyékony, természetes válaszok, megfelelő szókincs.",
             f"Német szóbeli felépítése ({dauer})", "Konversation"),
    ]
    if level == "kozep":
        tasks.append(Task(
            "2. Szerepjáték (Rollenspiel)",
            "Játszd el a következő hétköznapi szituációt a vizsgáztatóval: információkérés egy "
            "nyelviskolai tanfolyamról (ár, időpont, szint). Térj ki MINDEN megadott szempontra! "
            "Fél perc felkészülési idő.",
            0, "Minden megadott pontra reagálj, különben pontlevonás jár.",
            "Megfelelő udvariassági formák, célorientált párbeszéd, minden szempont lefedve.",
            "Német középszintű szóbeli (2. feladat)", "Rollenspiel"))
    else:
        tasks.append(Task(
            "2. Vita (Diskussion)",
            "Fejtsd ki és védd meg a véleményed a következő állításról, reagálva a vizsgáztató érveire: "
            "„Az online oktatás hosszú távon kiválthatja a hagyományos iskolát.” Fél perc felkészülés.",
            0, "Érvelj és cáfolj; használj kötőszavakat (einerseits/andererseits, trotzdem).",
            "Árnyalt érvelés, reagálás az ellenérvekre, gazdag nyelvi eszköztár.",
            "Német emelt szintű szóbeli (2. feladat)", "Diskussion"))

    tasks.append(Task(
        "3. Önálló témakifejtés (Thema)",
        f"Fejtsd ki összefüggően a véleményed a(z) „{thema2}” témáról ({desc2}) 4 irányító szempont és egy "
        "kép alapján. FONTOS: ez NEM képleírás – a kép csak kiindulópont a véleményalkotáshoz! Fél perc felkészülés.",
        0, "Max. 1-2 mondat a képről, utána a téma problémái, a saját véleményed.",
        "Összefüggő, önálló kifejtés; ne betanult szöveg legyen; mind a 4 szempont jelenjen meg.",
        "Német szóbeli (3. feladat) – kutatott felépítés alapján", "Thema"))
    return tasks


# ---------------------------------------------------------------------------
# Összerakás
# ---------------------------------------------------------------------------

_BUILDERS: dict[str, dict[str, Callable[[str], list[Task]]]] = {
    "matek": {"irasbeli": _math_written, "szobeli": _math_oral},
    "irodalom": {"irasbeli": _literature_written, "szobeli": _literature_oral},
    "tortenelem": {"irasbeli": _history_written, "szobeli": _history_oral},
    "nemet": {"irasbeli": _german_written, "szobeli": _german_oral},
}

_ORAL_MINUTES = {"matek": 20, "irodalom": 20, "tortenelem": 30, "nemet": 15}


def generate_exam_set(subject: str, level: str, mode: str) -> dict[str, Any]:
    if subject not in _BUILDERS:
        subject = "matek"
    if mode not in MODES:
        mode = "irasbeli"
    builder = _BUILDERS[subject][mode]
    tasks = [asdict(task) for task in builder(level)]

    if mode == "szobeli":
        estimated = _ORAL_MINUTES.get(subject, 20)
    else:
        estimated = 90 if level == "kozep" else 120

    return {
        "title": f"{SUBJECTS[subject]} – 2027 {MODES[mode]} ({'középszint' if level == 'kozep' else 'emelt szint'})",
        "subject": subject,
        "subject_label": SUBJECTS[subject],
        "level": level,
        "mode": mode,
        "mode_label": MODES[mode],
        "estimated_minutes": estimated,
        "tasks": tasks,
    }
