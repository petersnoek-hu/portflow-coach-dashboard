# 005 – Gegevens ophalen en verversen

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-09

> **Bouwvolgorde:** na [spec 003 – Portflow verbinden](../003-portflow-verbinden/spec.md) en [spec 004 – Studenten toevoegen](../004-studenten-toevoegen/spec.md). Deze spec maakt [spec 001 – Studentenoverzicht](../001-studentenoverzicht/spec.md) zinvol met echte gegevens, en levert de beoordelaars voor de keuzelijsten van [spec 006 – Gildemeesters](../006-gildemeesters/spec.md) en [spec 007 – Coaches](../007-coaches/spec.md).

## Doel

Als **coach** of **gildemeester** wil ik met één knop de evaluaties van mijn gevolgde studenten uit Portflow ophalen en lokaal bewaren, zodat de voortgangstabel direct opent, actueel is als ik dat wil, en ook zonder verbinding de laatst bekende stand toont.

Het studentenoverzicht (spec 001) haalt zelf niets op; deze spec doet dat. Hoe de app ophaalt en ververst, staat in grote lijnen in [architectuur.md](../../docs/architectuur.md#verversen); deze spec werkt dat uit.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil: het ophalen geldt voor alle gevolgde studenten, los van filters.

## Betrokken begrippen

- Portfolio, doel, feedback item, evaluatie, zelfevaluatie, evaluatieverzoek, beoordelaar ([begrippen.md](../../docs/begrippen.md))
- De tien vaardigheden en hun namen in Portflow ([vaardigheden-openict.md](../../docs/vaardigheden-openict.md), [API-document §9.1](../../docs/portflow-API-reverse-engineer.md))
- Startniveau als `0` ([voortgangsregels.md](../../docs/voortgangsregels.md#startniveau))
- Geen toegang, `n/b` ([voortgangsregels.md](../../docs/voortgangsregels.md#geen-toegang))
- Verbindingstoestanden ([spec 003](../003-portflow-verbinden/spec.md))

## Functionele eisen

### Wat wordt opgehaald

- [x] **F1 – Per gevolgde student.** Voor elke gevolgde student met een Portflow-koppeling haalt de app, voor elk gekoppeld portfolio, de doelen op (`GET /portfolios/{id}/goals`) en voor de **tien vaardigheden** de feedback items (`GET /portfolios/{id}/goals/{goal_id}/feedback-items`). Doelen worden op naam herkend, zonder onderscheid tussen hoofd- en kleine letters ([architectuur.md](../../docs/architectuur.md#portflow-api)). Beroepstaken en andere doelen worden niet opgehaald. Demostudenten en studenten zonder koppeling worden overgeslagen.
  - *Acceptatie:* een student met één portfolio met 12 doelen, waarvan 10 vaardigheden → 10 aanroepen voor feedback items; een demostudent → geen aanroepen.
- [x] **F2 – Wat bewaard wordt.** Per feedback item bewaart de app: vaardigheid, soort (zelfevaluatie of beoordeling), niveau (`Startniveau` → `0`), datum, naam van de beoordelaar, `review_request_id`, titel van het verzoek en of het verzoek beoordeeld is. **Alle** beoordelaars worden bewaard, ook die niet in de lijsten van spec 006 en 007 staan: of een evaluatie meetelt, bepalen de [voortgangsregels](../../docs/voortgangsregels.md#welke-evaluaties-tellen) bij het tonen, niet bij het ophalen. Toelichtingsteksten en bewijsstukken worden **niet** bewaard.
  - *Acceptatie:* een beoordeling door een onbekende beoordelaar staat na het ophalen in de database, maar verschijnt niet in de tabel van spec 001.
- [x] **F3 – Geweigerde verzoeken.** Daarnaast haalt de app de verzoeken op die aan de gebruiker zelf gericht zijn (`GET /portfolios/{eigen_id}/progress-review/invitations/received`) en bewaart van elk verzoek de status. Zo weet het overzicht welke `?` niet moeten verschijnen, omdat het verzoek is geweigerd ([voortgangsregels.md](../../docs/voortgangsregels.md#openstaand)). Van verzoeken aan andere beoordelaars is de status niet op te halen (zie *Open vragen*).
  - *Acceptatie:* een verzoek met status `denied` in de ontvangen verzoeken → de bijbehorende zelfevaluatie levert geen `?` op.
- [x] **F4 – Vervangen, niet aanvullen.** Na een geslaagde ophaalronde voor een student vervangen de nieuwe gegevens de oude van die student volledig. Lukt het voor een student niet, dan blijven de oude gegevens van die student staan.
  - *Acceptatie:* een evaluatie die in Portflow is verwijderd, is na verversen ook uit het dashboard verdwenen; een student waarvoor het ophalen mislukt, houdt zijn vorige cellen.

### Wanneer

- [x] **F5 – Alleen handmatig.** De app haalt **niet** vanzelf op: niet bij het starten en niet na het toevoegen van studenten. De pagina's tonen altijd de laatst bewaarde gegevens.
  - *Acceptatie:* de app start met een geldig token → er worden geen evaluaties opgehaald; na het toevoegen van 3 studenten ook niet.
- [x] **F6 – Knop "Verversen".** In de bovenbalk staat naast de Portflow-status ([spec 003](../003-portflow-verbinden/spec.md), F12) een knop **"Verversen"**. Een klik start een ophaalronde voor alle gevolgde studenten. Tijdens een ronde is de knop uitgeschakeld; een tweede ronde start niet zolang de eerste loopt.
  - *Acceptatie:* twee keer snel klikken start één ronde.
- [x] **F7 – Hint na toevoegen.** De bevestiging na het toevoegen van studenten ([spec 004](../004-studenten-toevoegen/spec.md), F12) krijgt de zin **"Klik op Verversen om hun evaluaties op te halen."**
  - *Acceptatie:* na het toevoegen van 3 studenten staat deze zin in de bevestiging op Overzicht.

### Weergave

- [x] **F8 – "Bijgewerkt om …".** In de knop "Verversen", onder het woord Verversen, staat **"Bijgewerkt om 14:32"** (vandaag) of **"Bijgewerkt op 8 november, 14:32"** (eerder): het tijdstip van de laatste geslaagde ronde. Is er nog nooit opgehaald: **"Nog niet opgehaald"**. Deze tekst staat in de bovenbalk, dus op elke pagina; de regel "Bijgewerkt om …" uit het ontwerp van Overzicht komt daarmee te vervallen ([design-system.md](../../docs/design-system.md#overzicht)).
  - *Acceptatie:* na een ronde om 14:32 vandaag toont de bovenbalk "Bijgewerkt om 14:32".
- [x] **F9 – Voortgang.** Tijdens een ronde toont dezelfde plek de voortgang: **"Ophalen… 4 van 13 studenten"**. Na afloop verversen de tabel en de tekst zich vanzelf, zonder dat de gebruiker de pagina herlaadt.
  - *Acceptatie:* tijdens een ronde loopt de teller op; na afloop toont de tabel de nieuwe gegevens zonder herladen.

### Fouten

- [x] **F10 – Geen toegang.** Geeft Portflow `404` voor (alle portfolio's van) een student, dan markeert de app die student als **geen toegang**; het overzicht toont dan `n/b` ([spec 001, F11](../001-studentenoverzicht/spec.md)). Krijgt de app later weer toegang, dan vervalt de markering.
  - *Acceptatie:* `404` op de doelen van het enige portfolio → de student staat op "geen toegang"; bij een volgende ronde met `200` niet meer.
- [x] **F11 – Verbinding verlopen.** Bij een `401` stopt de ronde, wordt de verbinding als verlopen gemarkeerd (spec 003) en blijven alle bewaarde gegevens staan.
  - *Acceptatie:* een `401` halverwege → de ronde stopt, de bovenbalk toont de verlopen verbinding en de tabel blijft gevuld.
- [x] **F12 – Andere fouten.** Andere fouten worden maximaal 3 keer opnieuw geprobeerd. Mislukt het daarna nog voor een of meer studenten, dan meldt de kop na afloop **"Bijgewerkt om 14:32 · 2 studenten niet gelukt"**, met bij hover hun namen. Die studenten houden hun oude gegevens (F4).
  - *Acceptatie:* een aanhoudende serverfout voor 2 van de 13 studenten → 11 studenten bijgewerkt en de melding "2 studenten niet gelukt".
- [x] **F13 – Niet verbonden.** Zonder geldige verbinding start er geen ronde en is de knop "Verversen" uitgeschakeld, met bij hover "Verbind eerst met Portflow". De bewaarde gegevens blijven zichtbaar.
  - *Acceptatie:* bij een verlopen token is de knop uitgeschakeld en blijft de tabel gevuld.

### Buiten scope

- Het tonen van de gegevens (cellen, `?`, signalen): [spec 001](../001-studentenoverzicht/spec.md)
- Te beoordelen (verzoeken die op de gebruiker wachten): eigen spec
- Automatisch verversen terwijl de app openstaat (bijvoorbeeld elk kwartier)
- Beroepstaken, toelichtingsteksten, bewijsstukken, profielfoto's

## Schermen

Er is geen eigen ontwerp. De knop "Verversen" en "Bijgewerkt om …" staan in de bovenbalk, rechts naast de Portflow-status, in dezelfde stijl als die statusknop ([design-system.md](../../docs/design-system.md#schil-alle-schermen)). In [`screenshots/kompas-dashboard-ontwerp.png`](../../screenshots/kompas-dashboard-ontwerp.png) (bevat echte namen, in `.gitignore`) staat "Bijgewerkt om …" nog in de kop van Overzicht; dat is een afwijking.

## Data

- **Bron:** Portflow API: `/portfolios/{id}/goals`, `/portfolios/{id}/goals/{goal_id}/feedback-items`, `/portfolios/{eigen_id}/progress-review/invitations/received` ([architectuur.md](../../docs/architectuur.md#portflow-api), [API-document §4.4–4.6](../../docs/portflow-API-reverse-engineer.md)).
- **Benodigde velden:** zie F2. De datum en de naam van de beoordelaar hebben geen vaste plek in de respons; de app probeert dezelfde velden als de console-app (API-document §4.5 en §8).
- **Verversen:** alleen met de knop "Verversen" (F5, F6).
- **Privacy:** alleen evaluatiegegevens die de coach nodig heeft; geen toelichtingen, bewijsstukken of foto's. Alles blijft lokaal in de database ([architectuur.md](../../docs/architectuur.md#privacy)).

## Technische eisen

- Alle Portflow-aanroepen blijven in `portflow_api.py` ([architectuur.md](../../docs/architectuur.md#portflow-api)). Paginering tot een lege pagina.
- Feedback items worden parallel opgehaald, hooguit 8 tegelijk.
- Het ophalen draait in een achtergrondthread, net als de verbinding van spec 003; het token komt nooit in de browser, logregels of foutmeldingen.
- Het herkennen van datum, beoordelaar en niveau uit een feedback item staat op één plek en heeft tests met verzonnen voorbeeldresponsen.
- Nieuwe kolommen en tabellen worden bij het starten toegevoegd aan een bestaande database ([architectuur.md](../../docs/architectuur.md), regel voor databasemigratie).
- Tests met een nagebootste Portflow (geen echte aanroepen) voor F1–F4 en F10–F12.

## Open vragen

- [x] **Bij het openen:** niet automatisch ophalen; alleen met de knop "Verversen" in de bovenbalk, naast de Portflow-status.
- [x] **Na toevoegen:** niet automatisch ophalen.
- [x] **Geweigerd bij anderen (F3):** akkoord. Een verzoek dat een andere beoordelaar heeft geweigerd, blijft als `?` staan; vastgelegd in [voortgangsregels.md](../../docs/voortgangsregels.md#openstaand).

## Logboek

- 2026-11-09 – spec aangemaakt
- 2026-11-09 – antwoorden verwerkt: alleen handmatig verversen met een knop in de bovenbalk; status uitgewerkt
- 2026-11-09 – gebouwd en getest, ook met echte Portflow-gegevens (13 studenten); status klaar. De beoordelaar staat in `evaluation.reviewer.name` en de datum in `date`
- 2026-11-09 – F8 aangepast op verzoek van de gebruiker: "Bijgewerkt om …" staat in de knop, en de knop is even hoog als de Portflow-statusknop
- 2026-11-09 – de knop Verversen en de Portflow-statusknop zijn nu ook even breed (op verzoek van de gebruiker)
