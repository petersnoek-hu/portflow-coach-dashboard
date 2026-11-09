# portflow-coach-dashboard

Een dashboard voor coaches en gildemeesters van Open-ICT (Hogeschool Utrecht). Het toont per groep studenten de voortgang op de tien LEF-vaardigheden. De evaluaties komen uit de onofficiële Portflow API; studenten en hun indeling beheert de gebruiker in het dashboard zelf. Het draait lokaal op de laptop van de gebruiker.

*A custom-built Portflow dashboard that shows Portflow progress for different groups of students, using the unofficial Portflow API.*

## Installeren en starten

Nodig: Python 3.14 (bijvoorbeeld via pyenv). Eenmalig, in de projectmap:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Starten (de browser opent vanzelf op http://127.0.0.1:5050):

```bash
source .venv/bin/activate
python app.py
```

- Andere poort: `python app.py --port 8000`. Poort 5000 is op macOS bezet door de AirPlay-ontvanger.
- Zonder automatisch openen van de browser: `python app.py --no-browser`.
- Stoppen: Ctrl+C.
- Bij de eerste start opent een Chrome-venster om in te loggen bij Portflow (via Canvas/HU). Het venster sluit vanzelf. Het token staat daarna in `.env`, het browserprofiel in `data/`.
- Demodata laden of verwijderen: via **Instellingen**.
- Gegevens staan lokaal in `data/dashboard.sqlite3` (niet in git).

Tests:

```bash
python -m unittest
```

## Werkwijze

Elke functie wordt eerst beschreven en daarna gebouwd. Zie [`features/README.md`](features/README.md).

## Mappen

| Map | Inhoud |
|---|---|
| [`features/`](features/) | Eén map per functie met spec (eisen) en ontwerpen; sjabloon in `features/_sjabloon/` |
| [`docs/`](docs/) | Gedeelde documentatie: begrippen, vaardigheden, voortgangsregels, gegevensmodel, beroepsrollen, beroepstaken, design system, architectuur |
| [`screenshots/`](screenshots/) | Ontwerpen en referentiebeelden die meerdere functies betreffen |
| [`CLAUDE.md`](CLAUDE.md) | Werkafspraken voor Claude Code |

## Documentatie

- [Begrippen](docs/begrippen.md): domeintaal van Open-ICT
- [Vaardigheden (overzicht)](docs/vaardigheden-openict.md) en [vaardigheden per niveau (LEF)](docs/vaardigheden-niveaus-LEF.md)
- [Voortgangsregels](docs/voortgangsregels.md): evaluaties, semester behaald en weergave van niveaus
- [Beroepsrollen](docs/beroepsrollen.md) en [HBO-i-beroepstaken](docs/HBOi-beroepstaken.md)
- [Gegevensmodel](docs/gegevensmodel.md): welke gegevens uit Portflow komen en welke het dashboard zelf bijhoudt
- [Design system](docs/design-system.md): schermen uit de ontwerpen, kleuren en componenten
- [Architectuur](docs/architectuur.md): techstack, Portflow-gebruik, privacy, beslissingen
- [Portflow API](docs/portflow-API-reverse-engineer.md) (onofficieel) en de bestaande [console-app](docs/portflow-console-app.py)
