# 042 – Sneller verversen (caching)

**Status:** in bouw <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-23

## Doel

Als **coach** of **gildemeester** wil ik met Verversen snel de nieuwste evaluaties zien, zonder dat het dashboard elke keer het hele portfolio van iedere student opnieuw ophaalt.

Nu haalt elke ronde van [spec 005](../005-gegevens-ophalen/spec.md) per student en per portfolio alle doelen op, plus de feedback items van de tien vaardigheden (minstens 11 aanroepen per portfolio, en meer bij paginering). Bij 13 studenten zijn dat er al meer dan 140, ook als er niets is veranderd.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- Evaluatie, zelfevaluatie, evaluatieverzoek, beoordelaar ([begrippen.md](../../docs/begrippen.md))
- Ophaalronde, Verversen ([spec 005](../005-gegevens-ophalen/spec.md), [architectuur.md](../../docs/architectuur.md#verversen))

## Referentie: P2M

Het zijproject P2M (Tauri + Svelte) cachet op twee manieren:

1. **Met een houdbaarheid:** de statistieken staan 30 minuten in `localStorage`, met "Cache: 14:32" erbij. Binnen die tijd wordt niets opgehaald.
2. **Gegevens die niet meer veranderen:** de criteria van een beoordelingsverzoek worden per `review_request_id` voor altijd bewaard; alleen ontbrekende worden opgehaald.

Dit dashboard bewaart al alles lokaal (SQLite, spec 005, F5). De winst zit dus niet in het bewaren, maar in **minder aanroepen per ronde**.

## Gekozen aanpak

Gekozen door de gebruiker (2026-11-23): **alleen ophalen wat er tussen `fetched_at` en nu is veranderd**, met een tweede knop om alles op te halen. Evaluaties houden hun id, dus `students.fetched_at` (al bewaard door spec 005) is het ijkpunt. Geen vaste houdbaarheid zoals de 30 minuten van P2M.

De feedback items kunnen in Portflow alleen per doel worden opgehaald. Een datumfilter op dat endpoint zou dus nog steeds 11 aanroepen per portfolio kosten. De winst zit in **eerst goedkoop controleren of er iets veranderd is**. P2M gebruikt daarvoor `GET /portfolios/{id}/progress-review/reviews`: één aanroep per portfolio, met per review `updated_at` en `invitation.review_request_id`. Live gecontroleerd op 2026-11-23 en beschreven in het [API-document §4.12](../../docs/portflow-API-reverse-engineer.md#412-get-portfoliosportfolio_idprogress-reviewreviews--alle-ingediende-reviews-op-een-portfolio-gevonden-2026-11-23).

**Uitwerking van "sinds `fetched_at`":** in plaats van de klok van de computer te vergelijken met `updated_at` van Portflow, bewaart het dashboard na elke volledige ophaalronde per portfolio een **vingerafdruk** van de reviewlijst (de id's met hun `updated_at`). Komt die bij de volgende ronde overeen, dan is er sinds `fetched_at` niets toegevoegd, aangepast of verwijderd. Zo maken tijdzones en een afwijkende klok niet uit, en vallen verwijderde reviews vanzelf op.

## Functionele eisen

- [x] **F1 – Alleen veranderde studenten.** Bij Verversen vraagt het dashboard per portfolio eerst de lijst met reviews op. Is de vingerafdruk van elk portfolio van de student gelijk aan die van de vorige volledige ronde, dan worden de doelen en feedback items van die student **niet** opgehaald en blijven zijn gegevens staan. Anders wordt de student volledig opgehaald zoals in spec 005 (F4: vervangen, niet aanvullen).
  - *Acceptatie:* 13 studenten, bij 1 is een review gewijzigd na zijn `fetched_at` → voor 12 studenten alleen de reviewlijst (1 aanroep per portfolio), voor 1 student de volledige ronde.
  - *Acceptatie:* een student zonder `fetched_at` (nog nooit opgehaald, of net opnieuw gekoppeld) wordt altijd volledig opgehaald.
  - *Acceptatie:* een review is verwijderd (aantal lager) → de student wordt volledig opgehaald en de evaluatie verdwijnt.
- [x] **F2 – Bij twijfel volledig.** Geeft de reviewlijst een fout of een onverwachte vorm, dan wordt de student volledig opgehaald (nooit een student overslaan op basis van onvolledige informatie). Een `401` stopt de ronde zoals in spec 005, F11.
  - *Acceptatie:* reviewlijst geeft `500` → de student wordt toch volledig opgehaald.
- [x] **F3 – Alles verversen met Shift+klik.** **Shift+klik** op Verversen haalt dezelfde studenten als een gewone ronde volledig op, ook als er niets veranderd is (op een pagina met studenten dus de studenten van het scherm, [spec 041](../041-verversen-contextueel/spec.md); elders iedereen). De hover-tekst van de knop vermeldt dit: "Evaluaties ophalen uit Portflow · Shift+klik: alles opnieuw ophalen".
  - *Acceptatie:* na Shift+klik zijn voor elke student de doelen en feedback items opgehaald, ook als er niets veranderd is.
- [x] **F5 – Status van verzoeken.** Ook bij een overgeslagen student wordt de status van verzoeken aan de gebruiker bijgewerkt (spec 005, F3), want een geweigerd verzoek verandert de reviewlijst niet.
  - *Acceptatie:* een verzoek dat sinds de vorige ronde is geweigerd → na Verversen geen `?` meer, ook als de student is overgeslagen.
- [x] **F4 – Voortgang en tijdstip.** *Gewijzigd 2026-11-23 (keuze van de gebruiker):* zonder Shift+klik staat er tijdens de ronde **"Controleren… 12 van 30"** (een overgeslagen student telt mee als gedaan), en na afloop **"Bijgewerkt om 10:47 · 3 nieuw"**: het aantal studenten dat volledig is opgehaald omdat er iets veranderd was. Was er niets veranderd: **"Bijgewerkt om 10:47 · niets nieuw"**. Na Shift+klik blijft het zoals in spec 005, F8–F9 ("Ophalen… 4 van 30 studenten", daarna "Bijgewerkt om …" zonder aantal). Deze informatie staat niet in de hover-tekst.
  - *Acceptatie:* een ronde met 30 studenten waarvan 3 veranderd → tijdens de ronde "Controleren… n van 30", daarna "Bijgewerkt om … · 3 nieuw".
- [x] **F6 – Draaiend icoon.** Tijdens een ronde draait het icoon van Verversen met een CSS-animatie die aan staat zolang de knop `aria-busy="true"` heeft. De statusupdates passen alleen dit attribuut en de tekst van de knop aan, zodat het icoon blijft draaien in plaats van bij elke update opnieuw te beginnen.
  - *Acceptatie:* tijdens een ronde met 30 studenten draait het icoon zonder te haperen als de teller oploopt.

### Buiten scope

- Een vaste houdbaarheid (TTL) per student
- Automatisch verversen terwijl de app openstaat (blijft buiten scope, zoals in spec 005)
- Caching van bewijsstukken en bestanden (spec 034, 038; bestanden worden al bewaard)

## Schermen

Geen nieuw scherm en geen nieuwe knop; alleen Shift+klik op Verversen en een langere hover-tekst.

## Data

- **Bron:** `GET /portfolios/{id}/progress-review/reviews`, daarnaast dezelfde endpoints als spec 005.
- **Benodigde velden:** per review `id` en `updated_at`. Bewaard wordt alleen een vingerafdruk (hash) per portfolio, geen namen of teksten uit deze lijst.
- **Privacy:** geen nieuwe gegevens die getoond worden; alles blijft lokaal.

## Technische eisen

- Alle Portflow-aanroepen blijven in `portflow_api.py`; het nieuwe endpoint komt in het API-document.
- Het besluit "overslaan of volledig ophalen" staat op één plek en heeft tests.
- De reviewlijsten van alle studenten worden aan het begin van de ronde tegelijk gecontroleerd (hooguit 8 tegelijk); daarna worden ongewijzigde studenten direct overgeslagen. Het bladeren stopt bij een pagina korter dan 50 (dit endpoint houdt zich aan `per_page`), zodat er geen extra aanroep voor een lege pagina nodig is.
- Tests met een nagebootste Portflow die het aantal aanroepen tellen.
- Nieuwe kolom (vingerafdruk per portfolio, in `student_portfolios`) wordt bij het starten toegevoegd aan een bestaande database.

## Open vragen

- [x] **Aanpak:** verschil sinds `fetched_at` (gekozen), geen vaste houdbaarheid.
- [x] **Volledig verversen:** Shift+klik op Verversen (gekozen door de gebruiker, in plaats van een tweede knop).
- [x] **Onderzoek:** live gecontroleerd (alleen lezen) bij 3 studenten: de lijst bevat zelfevaluaties én reviews van andere beoordelaars (coach, teacher, assessor, supervisor); elk verzoek uit de lokale database stond erin. Gepagineerd, `order_by` wordt genegeerd, dus alle pagina's ophalen. `updated_at` verandert bij aanpassen.
- [x] **Knop:** geen; Shift+klik.

## Logboek

- 2026-11-23 – spec aangemaakt, met P2M als referentie
- 2026-11-23 – aanpak gekozen: alleen ophalen wat sinds `fetched_at` veranderd is, plus een knop "Alles verversen"; controle via de reviewlijst uit P2M, nog live te onderzoeken
- 2026-11-23 – reviewlijst live gecontroleerd (zie Open vragen); gekozen: Shift+klik voor alles; "sinds `fetched_at`" uitgewerkt als vingerafdruk per portfolio; F5 toegevoegd; status in bouw
- 2026-11-23 – gebouwd: `portflow_api.reviews`, vingerafdruk in `student_portfolios.reviews_signature`, besluit in `portflow_fetch.is_unchanged`; Shift+klik in `app.js`. Tests in `tests/test_fetch.py` (nagebootste Portflow, telt aanroepen); hele suite groen. Nog niet in de app zelf geprobeerd; de eerste ronde na de update haalt iedereen volledig op (er is nog geen vingerafdruk)
- 2026-11-23 – bij het proberen bleek de caching te werken (vingerafdruk bij alle 30 portfolio's), maar niet zichtbaar. F4 gewijzigd op verzoek van de gebruiker: "Controleren… n van m" en "· 3 nieuw", niet in de hover. F6 toegevoegd: het icoon begon bij elke statusupdate opnieuw te draaien omdat de knop werd vervangen; nu `aria-busy` en alleen tekst bijwerken
- 2026-11-23 – F4 (teksten) en F6 (aria-busy, knop bijwerken in plaats van vervangen) gebouwd; tests in `tests/test_fetch.py`, hele suite groen. Nog niet in de app zelf bekeken
- 2026-11-23 – na een melding van de gebruiker (30 studenten duurden 30 seconden): de controles liepen een voor een en kostten elk een extra aanroep voor een lege pagina. Nu eerst alle reviewlijsten parallel (8 tegelijk) en stoppen bij een korte pagina. Live gemeten (alleen lezen): 30 portfolio's in 3,1 s, alle 30 ongewijzigd
- 2026-11-23 – gebruiker meldde 34 s voor een ronde zonder wijzigingen. Gemeten: de controles kosten 2,5 s, maar het bijwerken van verzoekstatussen (F5) deed per overgeslagen student één UPDATE per verzoek (30 × 367, zonder index): 24,5 s. Nu één UPDATE voor alle overgeslagen studenten samen, alleen voor rijen waarvan de status verandert: 0,02 s. Sorteren op datum om bij `fetched_at` te stoppen kan niet: dit endpoint negeert `order_by`
- 2026-11-23 – N+1-analyse (op verzoek van de gebruiker): `get_all_pages` stopt nu bij een pagina korter dan 50 in plaats van bij een lege pagina (live gecontroleerd dat goals, feedback-items, invitations, collections en reviews zich aan `per_page` houden); volledig ophalen van een student kost daardoor ongeveer 11 in plaats van 22 aanroepen. Indexen op `evaluations(student_id)` en `evaluations(review_request_id)`. De N+1-queries van de beheerpagina's (coaches, gildemeesters, projecten, keuzelijsten; < 50 ms) bewust gelaten: die lijsten groeien niet veel
- 2026-11-24 – samengevoegd met main, waar tegelijk een andere spec 041 (Verversen contextueel) was gebouwd: deze spec hernummerd van 041 naar 042. De twee vullen elkaar aan: 041 bepaalt *welke* studenten een ronde ophaalt (die van het scherm), 042 *of* een student volledig wordt opgehaald (alleen bij een gewijzigde reviewlijst). F3 aangepast: Shift+klik haalt dezelfde studenten als een gewone ronde volledig op, niet meer altijd iedereen. Het knopje "Bijgewerkt om … · N nieuw" blijft, naast de wijziging van spec 015, F4 (geen aantal niet-gekoppelde studenten meer)
