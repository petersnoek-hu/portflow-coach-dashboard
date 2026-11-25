# 042 – Logboek van het AI-advies

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-25

## Doel

Als **coach** of **gildemeester** wil ik kunnen zien wat het dashboard heeft gedaan om met Ollama te praten, en waarom dat wel of niet lukte, zodat ik een probleem zelf kan begrijpen of het kan doorgeven aan de beheerder.

Aanleiding: op een Windows-laptop zei het dashboard dat Ollama niet gevonden werd, terwijl Ollama draaide. Na het herladen van de pagina lukte het wel. Achteraf was niet meer na te gaan wat er misging. Bouwt voort op [spec 040](../040-ai-advies-niveau/spec.md).

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- AI-advies, Ollama, model, wizard: [spec 040](../040-ai-advies-niveau/spec.md)

## Functionele eisen

- [x] **F1 – Wat er wordt vastgelegd.** Het dashboard schrijft een regel bij elke stap van het AI-advies:
  - elke controle op Ollama (bij het openen van Instellingen, de wizard, de evaluatiepagina en bij "Controleren"): het adres, wat er gevraagd werd (versie, modellen), het antwoord (versie, aantal modellen, of het gekozen model er staat) of de fout, en hoe lang het duurde;
  - downloaden van een model: start, klaar of de fout van Ollama;
  - de proefvraag: model, duur, gelukt of de fout;
  - een advies en een vervolgvraag: welke AI en welk model, de instellingen voor de laptop (kernen, materiaal, uit het geheugen halen), hoeveel materiaal er meeging, de duur, en gelukt, gestopt of de fout;
  - het opslaan van AI-instellingen (standaardmodel, adres, laptop).
  - *Acceptatie:* met Ollama uit staat er na het openen van Instellingen een regel met het adres en "niet bereikbaar"; na het starten van Ollama en "Controleren" een regel met de versie.
- [x] **F2 – De oorzaak, in gewone taal.** Bij een fout staat zowel een korte uitleg ("Ollama is niet bereikbaar op http://127.0.0.1:11434") als de technische melding van het systeem (bijvoorbeeld "Connection refused" of "timed out na 5 s"). Zo is te zien of Ollama niet draaide, te laat antwoordde, of iets anders.
- [x] **F3 – Tonen.** In Instellingen, sectie AI-advies, en onderaan de wizard staat een uitklapblok **"Wat de app deed"** met de laatste regels, nieuwste bovenaan: tijd, onderwerp (Ollama, Downloaden, Proefvraag, Advies, Instellingen), ✓ of ⚠, en de tekst. Standaard dicht; na een fout open.
- [x] **F4 – Kopiëren.** Een knop **"Kopiëren"** zet het hele logboek als platte tekst op het klembord, met bovenaan de versie van het dashboard, het besturingssysteem en de versie van Ollama, zodat de gebruiker het kan doorsturen.
- [x] **F5 – Bewaren.** De regels staan in de lokale database, ook na herstarten. Alleen de laatste **500** blijven; oudere vallen weg. **Alles verwijderen** ([spec 014](../014-alles-verwijderen/spec.md)) wist ze. Een knop **"Logboek leegmaken"** wist ze ook.
- [x] **F6 – Geen gevoelige gegevens.** In het logboek staan geen namen van studenten of collega's, geen inhoud van evaluaties of bewijsstukken, geen titels van verzoeken, geen Portflow-token en geen API-sleutel. Een advies wordt aangeduid met het nummer van het verzoek. Foutmeldingen van Ollama of Anthropic worden ingekort tot 300 tekens.
  - *Acceptatie:* na een advies over een verzoek van een verzonnen student komt de naam van die student nergens in het logboek voor.

### Buiten scope

- Logging van Portflow (inloggen, token, Verversen), updates en installatie.
- Het logboek automatisch versturen; de gebruiker kopieert het zelf.

## Schermen

Geen eigen ontwerp: een uitklapblok in de stijl van het dashboard, onder de sectie AI-advies in Instellingen en onderaan de wizard.

## Data

- **Bron:** het dashboard zelf; niets uit Portflow.
- **Bewaard:** nieuwe tabel `ai_log` (tijd, onderwerp, ok/fout, tekst, technische melding).
- **Privacy:** zie F6. [architectuur.md](../../docs/architectuur.md#privacy) wordt bijgewerkt.

## Technische eisen

- Eén functie om een regel te schrijven (`ai_log.add`), die zelf inkort en nooit een fout geeft (lukt schrijven niet, dan gaat het advies gewoon door).
- De controles van `ai_routes.readiness` en de functies in `ollama.py` schrijven hun uitkomst; de technische melding komt uit de oorspronkelijke fout (bijvoorbeeld `URLError.reason`).
- Tests: een regel per soort gebeurtenis, de grens van 500, geen namen of token, en het kopiëren.

## Open vragen

- [x] Omvang: alleen het AI-advies (gekozen door de gebruiker, 2026-11-25).
- [x] Plek: Instellingen › AI-advies en de wizard, met een kopieerknop (gekozen 2026-11-25).
- [x] Bewaren: de laatste 500 regels in de database (gekozen 2026-11-25).

## Logboek

- 2026-11-25 – spec aangemaakt op verzoek van de gebruiker, na het probleem met Ollama op een Windows-laptop; omvang, plek en bewaren gekozen door de gebruiker
- 2026-11-25 – gebouwd: `ai_log.py` (tabel `ai_log`, de laatste 500 regels, tekst ingekort tot 300 tekens, schrijven geeft nooit een fout), `OllamaError.detail` met de melding van het systeem (bijvoorbeeld `ConnectionRefusedError: Connection refused` of `timed out na 5 s`), regels bij de controle op Ollama, downloaden, de proefvraag, het advies, vervolgvragen en het opslaan van instellingen, en het blok "Wat de app deed" (`_ai_log.html`) in Instellingen › AI-advies en onderaan de wizard. Keuze bij het bouwen: dezelfde controle bij elke pagina (ook het verversen van de adviekaart) wordt niet steeds een nieuwe regel, maar telt op ("3×"), zolang er niets anders tussen zit; een ongeldig antwoord van het model wordt gelogd met de lengte, niet met de inhoud. Tests in `tests/test_ai_log.py`; in de ontwikkelversie nagekeken (controle, proefvraag, kopiëren)
- 2026-11-25 – hersteld: de logregel van een advies, vervolgvraag of download werd geschreven nadat de taak al als klaar of gestopt gemeld was; nu eerst de regel, dan de eindtoestand (anders faalde de stoptest af en toe bij het opruimen)
