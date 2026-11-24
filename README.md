# portflow-coach-dashboard

Een dashboard voor coaches en gildemeesters van Open-ICT (Hogeschool Utrecht). Het toont per groep studenten de voortgang op de tien LEF-vaardigheden. De evaluaties komen uit de onofficiële Portflow API; studenten en hun indeling beheert de gebruiker in het dashboard zelf. Het draait lokaal op de laptop van de gebruiker.

*A custom-built Portflow dashboard that shows Portflow progress for different groups of students, using the unofficial Portflow API.*

## Installeren

Je hebt **Google Chrome** nodig; Python of andere programma's hoef je niet zelf te installeren.

**macOS:** open *Terminal* (via Spotlight: ⌘-spatie, typ "Terminal"), plak deze regel en druk op Enter:

```bash
curl -fsSL https://github.com/petersnoek-hu/portflow-coach-dashboard/releases/latest/download/install-macos.sh | sh
```

**Windows:** open *PowerShell* (Startmenu, typ "PowerShell"), plak deze regel en druk op Enter:

```powershell
irm https://github.com/petersnoek-hu/portflow-coach-dashboard/releases/latest/download/install-windows.ps1 | iex
```

Het script zet het dashboard in je eigen gebruikersmap (je hebt geen beheerdersrechten nodig), maakt een snelkoppeling en opent het dashboard. De eerste keer downloadt het ongeveer 100 MB. Daarna open je het dashboard met de snelkoppeling: op macOS **Portflow coach dashboard** in de map Apps in je thuismap (sleep het naar het Dock), op Windows in het Startmenu en op het bureaublad. Stoppen doe je via je naam onderin de zijbalk: **Dashboard afsluiten**.

- **Nieuwe versie:** het dashboard meldt het zelf; klik op **Nu bijwerken**. Je gegevens blijven staan.
- **Opnieuw installeren of herstellen:** voer dezelfde regel nog een keer uit.
- **Verwijderen:** op macOS `curl -fsSL https://github.com/petersnoek-hu/portflow-coach-dashboard/releases/latest/download/install-macos.sh | sh -s -- --verwijderen`; op Windows `& ([scriptblock]::Create((irm https://github.com/petersnoek-hu/portflow-coach-dashboard/releases/latest/download/install-windows.ps1))) --verwijderen`. Het script vraagt of je ook je gegevens wilt verwijderen.
- **Je gegevens** (database, Portflow-verbinding) staan in `~/Library/Application Support/Portflow coach dashboard/data/` (macOS) of `%LOCALAPPDATA%\Portflow coach dashboard\data\` (Windows). Gebruikte je het dashboard al vanuit een gekloonde map, dan biedt het script aan die gegevens over te nemen.

## Ontwikkelen

Nodig: Python 3.14 (bijvoorbeeld via pyenv). Eenmalig, in de projectmap:

macOS en Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Met [uv](https://docs.astral.sh/uv/) kan het op beide zonder deze stappen: `uv run python app.py` maakt de `.venv` zelf aan.

Starten (de browser opent vanzelf op http://127.0.0.1:5050):

```bash
source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
python app.py
```

**Let op: draait het geïnstalleerde dashboard ook?** Dat gebruikt zijn eigen kopie van de code (in `%LOCALAPPDATA%\Portflow coach dashboard\app\` of `~/Library/Application Support/Portflow coach dashboard/app/`) en poort 5050. Wijzigingen in deze map zie je daar dus **niet**. Sluit het geïnstalleerde dashboard af (je naam onderin de zijbalk › **Dashboard afsluiten**) of start de ontwikkelversie op een andere poort, bijvoorbeeld `python app.py --port 5051`, en open die poort in de browser. Wil je daarbij je echte gegevens gebruiken, start dan met `--database` en het pad naar `dashboard.sqlite3` in de datamap hieronder bij *Je gegevens*.

- Andere poort: `python app.py --port 8000`. Poort 5000 is op macOS bezet door de AirPlay-ontvanger. Een geïnstalleerd dashboard gebruikt 5050; de preview in Claude Code draait op 5051.
- Ander databestand: `python app.py --database ~/test/dashboard.sqlite3`. Het Chrome-profiel en de reservekopieën komen dan in dezelfde map. Welk bestand in gebruik is, staat in **Instellingen › Data**.
- Zonder automatisch openen van de browser: `python app.py --no-browser`.
- Stoppen: Ctrl+C.
- Op Windows staat Python in de venv in `.venv\Scripts\python.exe` (niet in `.venv/bin/python`).
- Bij de eerste start opent een Chrome-venster om in te loggen bij Portflow (via Canvas/HU). Het venster sluit vanzelf. Het token staat daarna in de database, het browserprofiel in `data/`; beide staan niet in git.
- Demodata laden of verwijderen: via **Instellingen**.
- Gegevens staan lokaal in `data/dashboard.sqlite3` (niet in git).

Tests:

```bash
python -m unittest
```

Een nieuwe versie publiceren: zie [`docs/releases.md`](docs/releases.md), of gebruik `/release` in Claude Code.

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
