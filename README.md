# ErettsegiMaster 2027

Látványos, modern webapp érettségi felkészüléshez 2027-re:
- Matematika
- Irodalom
- Történelem
- Német nyelv

Az alkalmazás minden generálásnál új, teljes gyakorlófeladatsort ad. A feladatok egy része újonnan készült, egy része pedig korábbi érettségik feladattípusai alapján készült.

## Indítás

1. (Opcionális) virtuális környezet:
   - Windows: `python -m venv .venv && .venv\Scripts\activate`
2. Függőségek:
   - `pip install -r requirements.txt`
3. Futtatás:
   - `python app.py`
4. Böngésző:
   - [http://127.0.0.1:5050](http://127.0.0.1:5050)

## Funkciók

- Tantárgy + szint (közép/emelt) kiválasztása
- Teljes feladatsor-generálás
- Pontszám- és időbecslés
- Tipp és forrás minden feladathoz
- Mintamegoldások ki/be kapcsolása
- Tanulási profil mentése (név, cél év, streak, statisztika)
- Időzített próbaérettségi mód visszaszámlálóval
- Automatikus pontozás válaszmezők alapján
- Feladatsor export PDF-be
- Korábbi érettségi feladatsor-linkek importja az Oktatási Hivatal oldaláról