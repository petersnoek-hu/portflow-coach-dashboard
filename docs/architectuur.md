# Architectuur

Keuzes die voor álle functies gelden, met een korte reden.

## Doel van de applicatie

Een dashboard voor coaches en gildemeesters dat de Portflow-voortgang van groepen studenten toont. De evaluaties komen uit de (onofficiële) Portflow API; studenten en hun indeling beheert het dashboard zelf. Zie [gegevensmodel.md](gegevensmodel.md).

## Techstack

| Onderdeel | Keuze | Reden |
|---|---|---|
| Taal backend | Python 3.14 | De bestaande console-app is in Python geschreven |
| Webframework | **Flask** (enige dependency) | Eén dependency, leesbare code, templates met automatische escaping |
| Interface | Server-HTML (Jinja-templates) + **één eigen CSS-bestand en één eigen JS-bestand** | Geen npm en geen build-stap; filteren, sorteren en zoeken gebeuren in de browser |
| Opslag / cache | **SQLite** (`sqlite3`, standaardbibliotheek), bestand `dashboard.sqlite3` in de gegevensmap (zie *Mappen*) | Eén bestand, robuust, geen dependency; staat niet in git |
| Installatie | Gebruikers: **installatiescript met [uv](https://docs.astral.sh/uv/)** (`install/`, `pyproject.toml`, `uv.lock`); ontwikkelaars: **venv + requirements.txt** | Gebruikers hoeven geen Python of pakketten te installeren en krijgen geen waarschuwing van macOS of Windows; uv is alleen een installatiehulpmiddel, geen dependency van de app ([spec 020](../features/020-installatie/spec.md)) |
| Tests | **unittest** (standaardbibliotheek), `python -m unittest` | Geen extra dependency |
| HTTP naar Portflow | `urllib` (standaardbibliotheek) | Geen extra dependency nodig |
| Excel-import (later) | openpyxl | Excel lezen kan niet met de standaardbibliotheek |
| Portflow-login | **playwright** (circa 43 MB), met de geïnstalleerde Google Chrome | Er is geen login-endpoint; het token wordt uit een browsersessie opgevangen, zoals in de console-app |
| Tekst uit pdf's (AI-advies) | **pypdf** (zuiver Python, klein) | De standaardbibliotheek kan geen pdf lezen; zonder pypdf gaat van een pdf alleen de naam mee ([spec 040](../features/040-ai-advies-niveau/spec.md)) |
| AI-advies | **Ollama** op de laptop zelf (geen Python-pakket; `urllib` naar `127.0.0.1:11434`), voorgesteld model `gemma4:12b-it-qat` | Er gaan geen studentgegevens van de laptop af; de gebruiker installeert Ollama zelf met de wizard ([spec 040](../features/040-ai-advies-niveau/spec.md)) |
| AI-advies met Claude | **anthropic** (officiële SDK van Anthropic), model `claude-opus-5-5` | Gekozen door de gebruiker: foutafhandeling, stoppen en nieuwe API-versies zitten erin; alleen gebruikt als de gebruiker Claude instelt ([spec 040](../features/040-ai-advies-niveau/spec.md), F13–F17) |
| Draaien | **Lokaal op de laptop** van de gebruiker, te openen via localhost | Elke coach heeft eigen gegevens; geen gedeelde server nodig |

## Afspraken voor de code

- **Zo weinig mogelijk dependencies.** Een nieuwe dependency alleen als de standaardbibliotheek het redelijkerwijs niet kan; leg de reden vast in de tabel hierboven.
- **Code in het Engels, interface in het Nederlands.** De vertaling van domeinbegrippen naar namen in de code staat in [begrippen.md](begrippen.md#begrippen-in-de-code).
- **Geen externe bronnen in de browser:** geen CDN's, geen Google Fonts. Lettertype en iconen worden meegeleverd (zie [design-system.md](design-system.md#typografie)).
- **Database-wijzigingen:** `CREATE TABLE IF NOT EXISTS` past een bestaande database niet aan. Een nieuwe kolom of tabel komt er bij het starten bij via een kleine migratie in `db.py` (bijvoorbeeld `ALTER TABLE … ADD COLUMN` als de kolom nog ontbreekt), zonder gegevensverlies.
- **Starten:** `python app.py` start de server op `http://127.0.0.1:5050` en opent de browser; `--port` kiest een andere poort. Poort 5000 is op macOS bezet door de AirPlay-ontvanger. De app luistert alleen op de eigen laptop (`127.0.0.1`), nooit op het netwerk; de debugmodus staat standaard uit.

## Mappenstructuur van de code

```
app.py                 ← start de app en opent de browser (--port, --no-browser)
requirements.txt       ← Flask, playwright (later openpyxl)
dashboard/
  __init__.py          ← maakt de Flask-app
  routes.py            ← de pagina's
  db.py                ← SQLite: verbinding en tabellen
  demo.py              ← demodata laden en verwijderen
  templates/           ← base.html (schil) + één template per pagina
  static/
    app.css            ← design tokens uit design-system.md als CSS-variabelen
    app.js             ← paneel en live status (spec 003)
    favicon.svg
    fonts/             ← DM Sans + licentie (OFL.txt)
tests/                 ← unittest
data/                  ← database (met het Portflow-token), browserprofiel en bekeken bestanden in bestanden/ (niet in git)
install/               ← installatiescripts en iconen (spec 020)
releases/              ← releasenotes per versie (docs/releases.md)
.github/workflows/     ← release bij een tag (spec 020, R2)
.claude/launch.json    ← startconfiguratie voor de preview in Claude Code
.claude/skills/release ← /release voor Claude Code (spec 020, R4)
```

**Gegevensmap** (`dashboard/paths.py`, spec 020, I3): in een git-checkout `data/` naast de code. Een geïnstalleerd dashboard heeft programma, Python en gegevens apart, zodat bijwerken alleen `app/` vervangt:

| | macOS | Windows |
|---|---|---|
| Programma | `~/Library/Application Support/Portflow coach dashboard/app/` | `%LOCALAPPDATA%\Portflow coach dashboard\app\` |
| Python en pakketten | `…/venv/` | `…\venv\` |
| Gegevens | `…/data/` | `…\data\` |

De app herkent een installatie aan het bestand `app/.installed` (geschreven door het installatiescript). `PORTFLOW_DASHBOARD_DATA` zet de gegevensmap om, en `python app.py --database <bestand>` kiest een ander databestand; het Chrome-profiel, de reservekopieën en `dashboard.log` staan altijd in de map van de database. Instellingen › Data toont de paden en waar de keuze vandaan komt ([spec 031](../features/031-gegevensbestand/spec.md)).

**Versies en bijwerken** (spec 020): het versienummer staat in `dashboard/version.py`. `dashboard/updates.py` vraagt bij het starten en dagelijks `GET https://api.github.com/repos/petersnoek-hu/portflow-coach-dashboard/releases/latest` op (zonder gegevens, met de versie in de User-Agent). Bijwerken (alleen in een installatie): reservekopie zonder token (ook bij een beta-versie, spec 020 B8), zip downloaden en de SHA-256 controleren, uitpakken naast de oude code; daarna stopt de app en wisselt `dashboard/update_swap.py` de mappen, laat uv de pakketten bijwerken en start de app opnieuw (of de oude versie, als iets mislukt). Een **beta-versie** (spec 020, B1–B8) kiest de gebruiker in Instellingen › Versie: de app vraagt branches en commits op (`GET …/branches`, `GET …/commits?sha=<branch>`) en haalt na een waarschuwing de zip van die commit (`https://github.com/petersnoek-hu/portflow-coach-dashboard/archive/<commit>.zip`) op, met dezelfde reservekopie en dezelfde stappen; `app/.beta` onthoudt de commit. Releases maken: [releases.md](releases.md).

Portflow (spec 003): `portflow_api.py` (alle API-aanroepen), `portflow_token.py` (token: vervaltijd en opslag in de database), `portflow_login.py` (Chrome-venster, Playwright), `portflow_connection.py` (toestandsmachine), `portflow_routes.py`. Later komt er onder meer `progress.py` (voortgangsregels, op één plek en getest) bij. Houd de structuur zo plat mogelijk; splits pas als een bestand onoverzichtelijk wordt.

## Bestaande console-app

[`portflow-console-app.py`](portflow-console-app.py) is de bestaande console-app (in de terminal) die de basis vormt voor deze webapp. Het is **referentiecode**, niet de code van de webapp. Regels die eruit worden overgenomen, staan in de docs (vooral [voortgangsregels.md](voortgangsregels.md)); bij verschil gelden de docs. Screenshots: `screenshots/portflow-console-app-1.png` en `-2.png` (bevatten echte namen, staan in `.gitignore`).

<a id="portflow-api"></a>
## Portflow API

De volledige, gereverse-engineerde beschrijving staat in [portflow-API-reverse-engineer.md](portflow-API-reverse-engineer.md). Hieronder staat alleen wat het dashboard ervan gebruikt.

- **Onofficieel:** endpoints kunnen zonder aankondiging veranderen. Houd alle API-aanroepen op één plek in de code.
- **Alleen lezen:** de API wordt alleen met `GET` gebruikt. Beoordelen gebeurt in Portflow zelf.
- **Basis-URL:** `https://portfolio.drieam.app/api/v1`, met de header `Authorization: Bearer <token>`.

### Inloggen

Portflow heeft geen login-endpoint. Net als in de console-app:

1. De app opent een Chrome-venster (Playwright, met een blijvend browserprofiel in `data/browser-profile/`) op de Portflow-tool in Canvas.
2. De gebruiker logt zo nodig in via Canvas/HU-SSO; met een nog geldige HU-login in het profiel gaat dit vanzelf.
3. De app vangt het bearer-token op uit de uitgaande verzoeken van Portflow en leest het eigen portfolio-id uit de pagina.
4. Het token staat in de database (tabel `settings`, sleutel `portflow_token`), net als het eigen portfolio-id. Bij het opslaan krijgt het databasebestand de rechten `600` (alleen de gebruiker). Reservekopieën van de database bevatten geen token. Nooit in de repository, nooit in de browser-JavaScript of in logregels.
5. Een token is **8 uur** geldig en bevat geen naam. De app ververst het 1 uur voor het verlopen, standaard in een **zichtbaar** venster: onzichtbaar (headless) verversen blijft hangen op de accountkeuze van SURFconext, omdat de Canvas-sessiecookie het sluiten van de browser niet overleeft. Lukt verversen niet, dan vraagt de app de gebruiker opnieuw in te loggen.

De uitgewerkte eisen en de toestanden van de verbinding staan in [spec 003](../features/003-portflow-verbinden/spec.md).

### Endpoints die het dashboard gebruikt

| Doel | Endpoint | Toelichting |
|---|---|---|
| Studenten kiezen en koppelen | `GET /shares/shared-with-me` | Portfolio's die met de gebruiker gedeeld zijn; alleen `inviter.current_role == "student"`. Effectief 20 per pagina |
| Eigen naam | `GET /portfolios/{eigen_portfolio_id}` | `user.name` |
| Vaardigheden van een student | `GET /portfolios/{portfolio_id}/goals` | Doelen; de tien vaardigheden herkennen op naam (zie hieronder) |
| Evaluaties per vaardigheid | `GET /portfolios/{portfolio_id}/goals/{goal_id}/feedback-items` | Niveau, datum, rol (`self` = zelfevaluatie), beoordelaar, `review_request_id` en **de tekst** (`evaluation.comment`, HTML; bewaard in `evaluations.text`, gekozen door de gebruiker, [spec 037](../features/037-evaluaties-lezen/spec.md)) |
| Bewijsstukken van één student | `GET /portfolios/{portfolio_id}/collections`, daarna per collectie `GET /portfolios/{portfolio_id}/collections/{id}/evidence` | Bij het openen van de studentpagina, alleen voor die student. Bewaard in `evidence_items` (naam, soort, datums, collecties, vaardigheden; geen inhoud) ([spec 034](../features/034-bewijsstukken-tijdlijn/spec.md)) |
| Tekst van een bewijsstuk | `GET /portfolios/{portfolio_id}/evidence/{id}` | Bij het openen van het feedbackpaneel, alleen voor tekst-bewijsstukken, live en niet bewaard; de HTML wordt opgeschoond tot eenvoudige opmaak en staat bovenaan het gesprek ([spec 036](../features/036-bewijsstuk-lezen/spec.md)). Bestanden downloaden kan niet: het downloadadres is niet gevonden |
| Feedbackvragen en reacties | `GET /portfolios/{portfolio_id}/evidence/{id}/comments`, daarna `GET /portfolios/{portfolio_id}/comments/{id}/children` | Samen met de bewijsstukken, alleen voor bewijsstukken die in de semesterperiode zijn toegevoegd of bijgewerkt, zes tegelijk. Bewaard in `evidence_comments`, **met de tekst** (gekozen door de gebruiker), wie en de rol ([spec 035](../features/035-feedbackvragen/spec.md)). Het endpoint voor reacties pagineert niet |
| Te beoordelen | `GET /portfolios/{eigen_portfolio_id}/progress-review/invitations/received` (alle statussen) | Verzoeken aan de gebruiker. Bewaard in `received_requests` (titel, student, status, `created_at`), elke ophaalronde vervangen; de toelichting en de gewenste datum worden niet bewaard ([spec 030](../features/030-te-beoordelen/spec.md)) |

- **Vaardigheidsnamen in Portflow** wijken af van LEF: in hoofdletters ("Kwalitatief Product Maken", "Kritisch Oordelen") en soms in spelling ("Overzicht Creëeren", "Proactief Handelen"); een student kan per semester een eigen set doelen hebben. Vergelijk daarom ongevoelig voor hoofdletters, Unicode-vorm, accenten, streepjes, spaties en verdubbelde letters. Andere opleidingen (zoals HCAI) zetten er iets achter ("Boodschap delen (HCAI) - semester 1"): het begin van de naam is genoeg, als heel woord ([spec 005](../features/005-gegevens-ophalen/spec.md), F14).
- **Niveau:** `evaluation.level` verwijst naar `level_set[].id`; het label `"Startniveau"` wordt `0` ([voortgangsregels.md](voortgangsregels.md#startniveau)).
- **Onzeker** (zie §8 van het API-document): de naam van de beoordelaar en de datum van een evaluatie hebben geen vaste plek in de respons. De console-app probeert meerdere velden; de webapp neemt die aanpak over.
- **Paginering:** doorgaan tot een **lege** pagina. Niet stoppen bij een pagina die korter is dan `per_page`: `/shares/shared-with-me` geeft altijd hooguit 20 per pagina, ook bij `per_page=50`.
- **Fouten:** `401` betekent opnieuw verbinden; `404` betekent geen toegang, dus `n/b` ([voortgangsregels.md](voortgangsregels.md#geen-toegang)); andere fouten worden maximaal 3 keer opnieuw geprobeerd.
- **Profielfoto's** (`profile_picture_url`) zijn tijdelijk geldige links; niet langdurig bewaren.

<a id="verversen"></a>
### Verversen

- De laatst opgehaalde Portflow-gegevens worden **lokaal bewaard**, zodat de app direct opent.
- Verversen gebeurt **met de knop "Verversen"** in de bovenbalk, naast de Portflow-status; niet vanzelf bij het openen en niet na het toevoegen van studenten. Naast de knop staat "Bijgewerkt om …".
- **Uitzondering:** direct na het allereerste verbinden (nog nooit opgehaald) start de eerste ophaalronde vanzelf, voor alle studenten ([spec 019](../features/019-eenvoudige-start/spec.md), F2).
- Verversen haalt alleen de evaluaties op van de studenten **op het scherm**: de lijst op Overzicht en Beheer › Studenten (na filters en zoeken), de tabel op Evaluaties, de student op zijn eigen pagina of op de pagina van één evaluatie. Daarna komen studenten die in die ronde nieuw zijn toegevoegd. Op een pagina zonder studenten haalt Verversen iedereen op die niet verborgen is. De lijst met gedeelde portfolio's en de lijst Te beoordelen worden elke ronde volledig opgehaald ([spec 041](../features/041-verversen-contextueel/spec.md)).
- De pagina werkt **zonder herladen** bij, na elke opgehaalde student: app.js haalt de pagina op de achtergrond opnieuw op en vervangt alleen de veranderde onderdelen (gemarkeerd met `data-live`). De server maakt alle HTML; JavaScript rekent niets zelf uit ([spec 041](../features/041-verversen-contextueel/spec.md), F7).
- Tijdens het ophalen is de voortgang zichtbaar. Feedback items worden parallel opgehaald, hooguit 8 tegelijk.
- Verversen haalt een student alleen volledig op als zijn reviewlijst in Portflow sinds de vorige volledige ronde is veranderd; **Shift+klik** op Verversen haalt iedereen volledig op ([spec 042](../features/042-sneller-verversen/spec.md)).
- De uitgewerkte eisen staan in [spec 005](../features/005-gegevens-ophalen/spec.md).

## Privacy

Het dashboard toont gegevens van studenten. Uitgangspunten:

- Alleen tonen wat een coach nodig heeft.
- Geen echte studentgegevens in screenshots, testdata of de repository. Ontwerpscreenshots met echte namen staan in `.gitignore` tot ze geanonimiseerd zijn.
- Studentgegevens blijven lokaal op de laptop van de gebruiker; de lokale database, het Portflow-token en het browserprofiel staan niet in de repository.
- Het dashboard bewaart de evaluaties van **alle** studenten die hun portfolio met de gebruiker hebben gedeeld, ook als de gebruiker ze niet actief volgt. De student heeft het portfolio zelf gedeeld; een share eindigt in Portflow standaard aan het einde van het schooljaar ([spec 019](../features/019-eenvoudige-start/spec.md)).
- Sinds [spec 037](../features/037-evaluaties-lezen/spec.md) bewaart het dashboard ook de **teksten** van zelfevaluaties en beoordelingen, net als de teksten van feedbackvragen en reacties ([spec 035](../features/035-feedbackvragen/spec.md)). Ze blijven lokaal; "Alles verwijderen" wist ze.
- AI-advies met **Claude** (spec 040, F13–F17) is een keuze per advies. Dan gaat het materiaal (met vervangen namen, ook afbeeldingen) via internet naar Anthropic. Instellen kan alleen met een vinkje dat de HU dit toestaat. De API-sleutel staat alleen in de lokale database (`ai_claude_api_key`), niet in reservekopieën, logs of de browser.
- AI-advies ([spec 040](../features/040-ai-advies-niveau/spec.md)): het materiaal van een evaluatie gaat alleen naar een AI-model in Ollama op de laptop zelf (het adres moet `127.0.0.1`, `localhost` of `[::1]` zijn), met namen vervangen. Het laatste advies per verzoek staat in de tabel `ai_advice`, het eigen oordeel van de beoordelaar (dat ook naar de AI gaat, met vervangen namen) in `ai_judgment`; "Alles verwijderen" wist beide, de AI-instellingen blijven. Een model downloaden vanuit Instellingen laat Ollama het ophalen; het dashboard stuurt alleen de modelnaam naar Ollama op de laptop.
- Sinds [spec 039](../features/039-evaluatie-voorbereiden/spec.md) bewaart het dashboard ook de **toelichting** die een student bij een evaluatieverzoek aan de gebruiker schrijft (`received_requests.note`). Ze blijft lokaal; "Alles verwijderen" wist ze.
- Sinds [spec 038](../features/038-bestanden-bekijken/spec.md) bewaart het dashboard bestanden van bewijsstukken die de gebruiker **bekijkt** (het voorbeeld als pdf of afbeelding, of de video) in `bestanden/` naast de database; bestandsnamen bevatten alleen ids. Een bestand dat 30 dagen niet is geopend, verdwijnt bij het starten; "Alles verwijderen" wist de map; reservekopieën bevatten hem niet.
- Het Portflow-token gaat alleen naar `portfolio.drieam.app`. Verzoeken met het token volgen geen doorverwijzingen; de ondertekende S3-links van Portflow worden zonder token opgehaald en niet bewaard of gelogd.
- Ingelezen Excelbestanden worden niet bewaard. Notities bij een student kunnen contactgegevens bevatten als de gebruiker die bij het importeren meeneemt; ze blijven lokaal in de database ([spec 013](../features/013-excel-importeren/spec.md)).

## Beslissingen

| Datum | Beslissing | Reden |
|---|---|---|
| 2026-11-09 | Elke coach heeft eigen gegevens; het dashboard draait lokaal op de laptop | Geen gedeelde database of server nodig; gegevens blijven bij de gebruiker |
| 2026-11-09 | Portflow levert alleen evaluaties; studenten, squads, semesters, beroepsrollen en eigen kolommen beheert het dashboard zelf | Indeling staat niet (betrouwbaar) in Portflow; de coach wil die zelf kunnen aanpassen |
| 2026-11-09 | Studenten worden automatisch aan Portflow gekoppeld op naam, met controle door de gebruiker bij twijfel | Weinig handwerk, maar geen stille fouten |
| 2026-11-09 | Inloggen zoals de console-app: Chrome-venster, token opvangen, lokaal bewaren | Enige bekende manier; gebruiker logt in via HU-SSO |
| 2026-11-09 | Token verversen in een zichtbaar Chrome-venster met hetzelfde profiel (standaard); onzichtbaar verversen als instelling | Portflow heeft geen refresh-endpoint; headless blijft hangen op de accountkeuze van SURFconext |
| 2026-11-09 | Portflow-gegevens lokaal bewaren; verversen alleen met een knop in de bovenbalk | Ophalen duurt even; de app moet direct openen, en de gebruiker bepaalt zelf wanneer er Portflow-verkeer is |
| 2026-11-09 | Flask + server-HTML + eigen JS/CSS + SQLite; venv; code in het Engels | Eenvoudigste codebase met de minste dependencies; geen build-stap |
| 2026-11-09 | *(Vervangen op 2026-11-11.)* Alleen evaluaties van beoordelaars uit de eigen lijst tellen; de vaste uitzondering in de console-app vervalt | Evaluaties door bijvoorbeeld ouderejaars studenten onderscheiden van die door coaches en gildemeesters |
| 2026-11-09 | Coaches en gildemeesters in één tabel met personen en rollen, met twee eigen pagina's | Iemand kan beide zijn; één naam op één plek wijzigen |
| 2026-11-09 | Gildes als eigen lijst (code, naam, kleur), één per beroepsrol; start leeg | De gebruiker beheert de gildes; de Open-ICT-gildes zijn met één knop toe te voegen |
| 2026-11-09 | Beroepsrollen starten leeg en worden niet meer vanzelf aangemaakt; de negen Open-ICT-rollen met één knop | Net als bij gildes; een verwijderde rol komt niet terug |
| 2026-11-09 | Semesters als eigen lijst met de eisen als vrije tekst; start leeg, de 8 Open-ICT-semesters met één knop; het semester van een student blijft een nummer | Weergave van het toetsprogramma; de rekenregels blijven op één plek (voortgangsregels.md) |
| 2026-11-09 | Projecten met nummer, naam, opdrachtgever en kleur; start leeg, de Open-ICT-projecten met één knop | Net als bij de andere beheerlijsten |
| 2026-11-11 | Het Portflow-token in de database in plaats van in `.env`; reservekopieën zonder token | Alle gegevens van de app op één plek (eenvoudiger, ook voor de installatie van spec 020); het token is maar 8 uur geldig. Het blijft lokaal en buiten git |
| 2026-11-09 | Excelbestanden (.xlsx) inlezen zonder extra pakket (zip met XML); het bestand wordt niet bewaard | Geen nieuwe dependency; studentgegevens blijven zo kort mogelijk in de app |
| 2026-11-11 | Alle beoordelaars tellen mee, behalve uitgesloten beoordelaars; gevonden beoordelaars worden automatisch toegevoegd | Zonder instellen bruikbaar (spec 019); wie ouderejaars wil weglaten, sluit ze uit |
| 2026-11-11 | Alle gedeelde studenten komen automatisch in het dashboard; verbergen in plaats van aanvinken | Overzicht met zo weinig mogelijk handelingen (spec 019) |
| 2026-11-11 | De eerste ophaalronde start vanzelf na het allereerste verbinden; Verversen haalt daarna de zichtbare studenten op | De eenvoudige gebruiker ziet direct niveaus; minder Portflow-verkeer (spec 019) |
| 2026-11-23 | Verversen haalt alleen de studenten van het scherm op en werkt de pagina bij door onderdelen te vervangen die de server opnieuw maakt, niet door de gegevens in JavaScript te verwerken | Sneller klaar en het scherm toont meteen de nieuwe stand; de voortgangsregels blijven op één plek (spec 041) |
| 2026-11-11 | Invulling en Rol in de squad zijn keuzelijsten die de gebruiker beheert; eigen kolommen kunnen een keuzelijst zijn; studenten verwijzen naar een keuze ([spec 024](../features/024-keuzelijsten/spec.md)) | Eén beheeronderdeel voor alle eenvoudige lijsten; een gewijzigde code of omschrijving werkt overal door |
