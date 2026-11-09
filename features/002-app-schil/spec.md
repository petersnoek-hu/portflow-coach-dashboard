# 002 – Basisapplicatie en schil

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-09

## Doel

Als **coach** of **gildemeester** wil ik de app met één opdracht kunnen starten en een herkenbare schil zien (zijbalk, bovenbalk, pagina's), zodat er een basis staat waarop de andere functies gebouwd worden. Met demodata kan ik de app bekijken zonder echte gegevens.

Dit is de eerste code van het project. De technische keuzes staan in [architectuur.md](../../docs/architectuur.md).

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil in deze functie.

## Betrokken begrippen

- Menu-items en schermen uit [design-system.md](../../docs/design-system.md#schil-alle-schermen)
- Demodata: verzonnen studenten, squads, beroepsrollen en evaluaties ([gegevensmodel.md](../../docs/gegevensmodel.md))
- Namen in de code: [begrippen.md](../../docs/begrippen.md#begrippen-in-de-code)

## Functionele eisen

### Starten

- [x] **F1 – Eén opdracht.** Na de installatie (venv + `pip install -r requirements.txt`) start `python app.py` de app op `http://127.0.0.1:5050` en opent de browser vanzelf. Met `python app.py --port 8000` kies je een andere poort; `--no-browser` start zonder de browser te openen. (Niet 5000: die poort is op macOS bezet door de AirPlay-ontvanger.)
  - *Acceptatie:* op een schone checkout, na de installatiestappen uit de README, toont de browser binnen enkele seconden de pagina Overzicht.
- [x] **F2 – Alleen lokaal.** De app luistert alleen op `127.0.0.1`; de debugmodus staat uit.
  - *Acceptatie:* vanaf een ander apparaat in hetzelfde netwerk is de app niet bereikbaar.
- [x] **F3 – Database.** Bij de eerste start maakt de app `data/dashboard.sqlite3` aan, met tabellen volgens [gegevensmodel.md](../../docs/gegevensmodel.md) voor zover nodig voor de demodata. De map `data/` staat in `.gitignore`.
  - *Acceptatie:* na de eerste start bestaat het bestand; een tweede start gebruikt het opnieuw zonder fout of verlies van gegevens.
- [x] **F4 – Poort bezet.** Is de gekozen poort bezet, dan meldt de app dat duidelijk in de terminal.
  - *Acceptatie:* een tweede `python app.py` terwijl de eerste draait, geeft een begrijpelijke melding (met de tip `--port`) en geen lange foutmelding.

### Schil

- [x] **F5 – Zijbalk.** Donkergroen. Bovenaan het **terminal-woordmerk**: `>_ portflow` in een monospace letter, met daaronder "coach dashboard" (een knipoog naar de console-app). Daaronder het kopje "Werkruimte" en de menu-items Overzicht, Studenten, Evaluaties, Projecten, Kolommen, Beroepsrollen, Semesters en Instellingen, elk met een icoon. De browsertab heeft een `>_`-icoon. Het actieve item is gemarkeerd.
  - *Acceptatie:* een klik op Projecten opent de pagina Projecten, en dan is Projecten in de zijbalk gemarkeerd. De browsertab heet "Portflow coach dashboard".
- [x] **F6 – Gebruiker onderin de zijbalk.** Zolang de eerste start (naam invullen) niet gebouwd is: een neutrale avatar met de tekst **"Gebruiker"**, zonder rollen. Geen hulpkaart ("Hulp nodig?"); die komt pas als er een handleiding is.
  - *Acceptatie:* onderin de zijbalk staat "Gebruiker"; er is geen hulpkaart.
- [x] **F7 – Bovenbalk.** De Portflow-status "Niet verbonden" (deze functie verbindt nog niet) en de avatar van de gebruiker. Geen belletje; dat komt pas als er meldingen zijn.
  - *Acceptatie:* de bovenbalk staat op elke pagina, met de status "Niet verbonden" en zonder belletje.
- [x] **F8 – Paginakop.** Elke pagina heeft een klein kopje in hoofdletters, een titel en één zin uitleg (teksten: zie de tabel hieronder).
  - *Acceptatie:* elke pagina toont de kop uit de tabel.
- [x] **F9 – Lege pagina's.** Onder de kop staat een korte, vriendelijke tekst over wat daar komt, bijvoorbeeld "Hier komt het studentenoverzicht."
  - *Acceptatie:* elke pagina behalve Instellingen toont zo'n tekst, en geen foutmelding.

| Pagina | Kopje | Titel | Uitleg | Bron |
|---|---|---|---|---|
| Overzicht | datum, bijvoorbeeld "MAANDAG 9 NOVEMBER" | "Goedemorgen, …" (naar tijdstip: morgen, middag, avond) | Dit vraagt vandaag je aandacht. | ontwerp |
| Studenten | Studievoortgang | Studenten | Alle studenten die je volgt, met hun voortgang per vaardigheid. | afgesproken |
| Evaluaties | Studievoortgang | Evaluaties | Evaluatieverzoeken die op jouw beoordeling wachten. | afgesproken |
| Projecten | Beheer | Projecten | Beheer de projectgroepen waarin je studenten zijn ingedeeld. | ontwerp |
| Kolommen | Curriculum | Kolommen | De bouwstenen van je studentenoverzicht, op één plek beheerd. | ontwerp |
| Beroepsrollen | Opleidingsprofiel | Beroepsrollen | Beheer rollen en zie direct welke studenten primair of secundair gekoppeld zijn. | ontwerp |
| Semesters | Studievoortgang | Semesters | Bekijk de bezetting van semester 1 tot en met 8 en verplaats studenten. | ontwerp |
| Instellingen | Beheer | Instellingen | Je gegevens, de semesterperiode en de koppeling met Portflow. | afgesproken |

### Demodata

- [x] **F10 – Demodata laden.** In Instellingen staat de knop **"Demodata laden"**. Die vult de database met een vaste, verzonnen set: studenten, squads, beroepsrollen, coaches, gildemeesters en evaluaties. Alle demorecords zijn gemarkeerd (`is_demo`). Is er al demodata, dan is de knop uitgeschakeld.
  - *Acceptatie:* na een klik toont Instellingen hoeveel demorecords er per soort zijn; een tweede klik is niet mogelijk.
- [x] **F11 – Demodata verwijderen.** De knop **"Demodata verwijderen"** vraagt eerst om bevestiging ("Alle demodata verwijderen? Echte gegevens blijven staan.", met Annuleren en Verwijderen) en verwijdert daarna alle demorecords en niets anders.
  - *Acceptatie:* met één echte student en de demodata blijft na verwijderen alleen de echte student over.
- [x] **F12 – Demobanner.** Zolang er demodata is, staat op elke pagina een banner "Je bekijkt demodata", met een link naar Instellingen.
  - *Acceptatie:* na laden verschijnt de banner, na verwijderen is hij weg.
- [x] **F13 – Inhoud van de demodata.** Alle namen zijn verzonnen. De set dekt de gevallen uit spec 001, zodat die later te testen zijn:
  - studenten in semester 2 en in semester 3 tot en met 5;
  - meerdere squads, een student zonder squad en een student zonder semester;
  - evaluaties met startniveau (`0`), met meerdere niveaus (`1/2`) en zonder evaluatie;
  - openstaande verzoeken (`?`), een geweigerd verzoek en een eindassessment;
  - een evaluatie van een beoordelaar die niet in de lijst staat;
  - studenten met signalen;
  - een student zonder toegang.
  - *Acceptatie:* een test controleert dat elk genoemd geval in de demoset voorkomt.

### Uiterlijk

- [x] **F14 – Stijl volgens het design system.** Kleuren, lettertype (DM Sans, meegeleverd) en iconen (SVG) volgens [design-system.md](../../docs/design-system.md). Geen externe bronnen: geen CDN, geen Google Fonts.
  - *Acceptatie:* de schil lijkt op de zijbalk en bovenbalk in de ontwerpen; in de netwerkverzoeken van de browser staan alleen verzoeken naar `127.0.0.1`.
- [x] **F15 – Schermbreedte.** Gebouwd voor laptop en groter (vanaf ongeveer 1280 pixels). Op smallere schermen blijft de zijbalk staan en scrolt de inhoud horizontaal.
  - *Acceptatie:* bij 1280 pixels breed past de schil zonder horizontale scrollbalk.
- [x] **F16 – Logo in de terminal.** Bij het starten toont de terminal het ASCII-logo uit de console-app, met "coach dashboard" en het adres van de app.
  - *Acceptatie:* `python app.py` toont het logo en `http://127.0.0.1:5050`.

### Buiten scope

- Inhoud van de pagina's (eigen specs, zoals 001 Studentenoverzicht)
- Eerste start (naam en gildes invullen), Portflow verbinden, studenten toevoegen
- Meldingen (belletje) en de hulpkaart met handleiding
- Een installeerbaar programma (PyInstaller of iets vergelijkbaars)

## Schermen

| Scherm | Bestand | Opmerking |
|---|---|---|
| Schil (zijbalk, bovenbalk, kop) | [`screenshots/kompas-dashboard-ontwerp.png`](../../screenshots/kompas-dashboard-ontwerp.png) en de vier `*-CRUD-*.png` | Bevatten echte namen (in `.gitignore`). "Kompas" is een werktitel; de app heet Portflow coach dashboard. Afwijkingen: terminal-woordmerk, geen hulpkaart, geen belletje |

## Data

- **Bron:** alleen de lokale SQLite-database; deze functie gebruikt Portflow nog niet.
- **Privacy:** alleen verzonnen demodata; er staan geen echte gegevens in de code of de tests.

## Technische eisen

- Opzet volgens [architectuur.md](../../docs/architectuur.md): Flask als enige dependency, server-HTML met één CSS- en één JS-bestand, SQLite, venv, code in het Engels.
- Een README-sectie "Installeren en starten" met de exacte stappen.
- Tests (unittest): elke pagina geeft status 200; demodata laden en verwijderen raakt geen echte records; F13.
- De demoset staat in de code als leesbare data (bijvoorbeeld een Python- of JSON-bestand), niet willekeurig gegenereerd.

## Open vragen

- [x] Naam en logo: "Portflow coach dashboard", met het terminal-woordmerk in de zijbalk en het ASCII-logo in de terminal.
- [x] Gebruiker: neutraal "Gebruiker" tot de eerste start gebouwd is.
- [x] Hulpkaart en belletje: weglaten tot er een handleiding en meldingen zijn.
- [x] Schermbreedte: laptop en groter.
- [x] Demodata verwijderen: eerst bevestigen.
- [x] Paginateksten: akkoord.

## Logboek

- 2026-11-09 – spec aangemaakt
- 2026-11-09 – open vragen beantwoord; status uitgewerkt
- 2026-11-09 – poort gewijzigd van 5000 naar 5050, instelbaar met `--port` (5000 is op macOS bezet door AirPlay); status in bouw
- 2026-11-09 – gebouwd en gecontroleerd: 17 tests slagen (`python -m unittest`); in de browser gecontroleerd op 1440 px breed: alle pagina's, demodata laden, bevestigen, verwijderen, alleen verzoeken naar 127.0.0.1. Extra: `--no-browser` en een favicon. Status klaar.
- Niet automatisch getest: het vanzelf openen van de browser (F1) en de onbereikbaarheid vanaf een ander apparaat (F2; volgt uit het luisteren op 127.0.0.1).
