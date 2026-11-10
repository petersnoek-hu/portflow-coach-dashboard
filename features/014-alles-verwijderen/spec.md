# 014 – Alles verwijderen (terug naar de begintoestand)

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-09

## Doel

Als **coach** of **gildemeester** wil ik met één functie alle gegevens uit het dashboard verwijderen en de app terugzetten in de begintoestand (zoals bij de eerste start), bijvoorbeeld aan het eind van een semester of om opnieuw te beginnen. Omdat dit niet terug te draaien is, vraagt de app twee keer om bevestiging en maakt hij eerst een reservekopie.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- De gegevens van het dashboard ([gegevensmodel.md](../../docs/gegevensmodel.md)), de Portflow-koppeling ([spec 003](../003-portflow-verbinden/spec.md)), demodata ([spec 002](../002-app-schil/spec.md))

## Functionele eisen

- [x] **F1 – Plek.** Onderaan **Instellingen**, onder Demodata, staat een blok **"Alles verwijderen"** met de uitleg "Zet het dashboard terug in de begintoestand: alle gegevens en de Portflow-koppeling worden verwijderd. Er wordt eerst een reservekopie gemaakt." en een rode knop **"Alles verwijderen…"**.
  - *Acceptatie:* Instellingen toont het blok onderaan met de knop.
- [x] **F2 – Eerste bevestiging.** De knop toont eerst de vraag **"Alle gegevens verwijderen?"** met een opsomming van wat verdwijnt (met aantallen: studenten, evaluaties, projecten, semesters, beroepsrollen, gildes, coaches en gildemeesters, eigen kolommen, instellingen, de Portflow-koppeling en de HU-login in het browserprofiel), en de knoppen **Annuleren** en **Doorgaan**.
  - *Acceptatie:* na "Alles verwijderen…" staat de vraag met de aantallen; Annuleren laat alles staan.
- [x] **F3 – Tweede bevestiging.** "Doorgaan" toont een tweede stap: **"Weet je het zeker? Dit kun je in de app niet ongedaan maken."** met een veld waarin de gebruiker **VERWIJDEREN** typt. Pas dan werkt de knop **"Definitief verwijderen"** (ook de server controleert het woord; hoofd- of kleine letters maken niet uit).
  - *Acceptatie:* zonder het woord, of met een ander woord, wordt niets verwijderd en blijft de tweede stap staan met de uitleg "Typ VERWIJDEREN om te bevestigen."
- [x] **F4 – Reservekopie.** Vóór het verwijderen maakt de app een kopie van de database in `data/reservekopieen/` met datum en tijd in de naam (bijvoorbeeld `dashboard-2026-11-09-2215.sqlite3`). Mislukt de kopie, dan wordt er niets verwijderd en meldt de app dat. Het token en het browserprofiel komen niet in de kopie.
  - *Acceptatie:* na het verwijderen staat er een kopie met de oude gegevens in de map; terugzetten gaat door de app te stoppen en het bestand over `data/dashboard.sqlite3` te zetten.
- [x] **F5 – Wat er verdwijnt.** Alle gegevens in de database (ook demodata en alle instellingen, zoals de semesterperiode, de kolomkeuze, de naam van de gebruiker en het tijdstip van ophalen), het Portflow-token in `.env` en het browserprofiel (`data/browser-profile`, met de HU-login). Ook een lopende, niet afgeronde Excel-import wordt vergeten. De structuur van de database blijft, zodat de app meteen verder kan.
  - *Acceptatie:* na het verwijderen zijn alle tabellen leeg, staat er geen token meer in `.env` en is het browserprofiel weg.
- [x] **F6 – Begintoestand.** Na het verwijderen gaat de gebruiker naar **Overzicht** met de melding "Alle gegevens zijn verwijderd. De reservekopie staat in data/reservekopieen/…". Het dashboard is zoals bij de eerste start: 0 studenten (de lege staat van [spec 004](../004-studenten-toevoegen/spec.md)), Portflow "Niet verbonden", geen beroepsrollen, semesters, projecten, gildes, coaches of gildemeesters. Er opent geen inlogvenster vanzelf.
  - *Acceptatie:* Overzicht toont "Nog geen studenten" en de bovenbalk "Niet verbonden".
- [x] **F7 – Niet tijdens inloggen of ophalen.** Loopt er een inlogpoging of een ophaalronde, dan is de knop uitgeschakeld met de uitleg "Wacht tot het inloggen of ophalen klaar is."
  - *Acceptatie:* tijdens een ophaalronde wordt er niets verwijderd.

### Buiten scope

- Een reservekopie terugzetten vanuit de app (kan handmatig, zie F4)
- Alleen een deel verwijderen (bijvoorbeeld alleen studenten); demodata verwijderen heeft al een eigen knop

## Schermen

Geen eigen ontwerp. Volgt de bevestigingen in Instellingen (Demodata verwijderen, Verbinding verbreken); de rode knop is de knop "gevaar" uit het design system.

## Data

- **Bron:** eigen opslag, `.env` en `data/browser-profile`.
- **Privacy:** de reservekopie bevat studentgegevens; hij staat in `data/` (niet in de repository) en blijft lokaal.

## Technische eisen

- Eén functie die alles verwijdert, los van de pagina's; de tabellen worden in één transactie leeggemaakt.
- De kopie via de backup-functie van SQLite (een consistente kopie, ook als de app draait).
- Tests: de twee bevestigingen (zonder en met het woord), de kopie, lege tabellen, token weg, browserprofiel weg, de begintoestand van Overzicht, en geblokkeerd tijdens ophalen.

## Open vragen

- [x] **Omvang:** alles, ook de Portflow-verbinding (token en browserprofiel).
- [x] **Reservekopie:** ja, automatisch, in `data/reservekopieen/`.
- [x] **Tweede bevestiging:** het woord VERWIJDEREN intypen.
- [x] **Plek:** onderaan Instellingen.

## Logboek

- 2026-11-09 – spec aangemaakt op verzoek van de gebruiker; antwoorden verwerkt; status in bouw
- 2026-11-09 – gebouwd en getest met unit tests (tijdelijke database, .env en browserprofiel); status klaar. Nog niet in de browser bekeken: de server was door de gebruiker gestopt
