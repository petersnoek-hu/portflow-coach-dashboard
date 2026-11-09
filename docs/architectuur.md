# Architectuur

Keuzes die voor álle functies gelden, met een korte reden.

## Doel van de applicatie

Een dashboard voor coaches en gildemeesters dat de Portflow-voortgang van groepen studenten toont. De evaluaties komen uit de (onofficiële) Portflow API; studenten en hun indeling beheert het dashboard zelf. Zie [gegevensmodel.md](gegevensmodel.md).

## Techstack

| Onderdeel | Keuze | Reden |
|---|---|---|
| Taal backend | Python | De bestaande console-app is in Python geschreven |
| Webframework / UI | *nog kiezen* | Webapp in de browser |
| Opslag / cache | *nog kiezen* (lokaal, bijvoorbeeld SQLite) | Gegevens blijven op de laptop van de gebruiker |
| Portflow-login | Playwright (Chrome) | Er is geen login-endpoint; het token wordt uit een browsersessie opgevangen, zoals in de console-app |
| Draaien | **Lokaal op de laptop** van de gebruiker, te openen via localhost | Elke coach heeft eigen gegevens; geen gedeelde server nodig |

## Mappenstructuur van de code

*(aanvullen zodra de eerste code er is)*

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

1. De gebruiker klikt op **Verbinden met Portflow**. De app opent een Chrome-venster (Playwright, met een eigen browserprofiel) op de Portflow-tool in Canvas.
2. De gebruiker logt in via Canvas/HU-SSO.
3. De app vangt het bearer-token op uit de uitgaande verzoeken van Portflow, en leest het eigen portfolio-id uit de pagina.
4. Het token (een JWT met vervaldatum) en het eigen portfolio-id worden **lokaal** bewaard, nooit in de repository.
5. Is het token verlopen (te zien aan de `exp`-claim, of aan een `401`), dan toont de bovenbalk "Niet verbonden" en kan de gebruiker opnieuw verbinden.

### Endpoints die het dashboard gebruikt

| Doel | Endpoint | Toelichting |
|---|---|---|
| Studenten kiezen en koppelen | `GET /shares/shared-with-me` | Portfolio's die met de gebruiker gedeeld zijn; alleen `inviter.current_role == "student"`. Effectief 20 per pagina |
| Eigen naam | `GET /portfolios/{eigen_portfolio_id}` | `user.name` |
| Vaardigheden van een student | `GET /portfolios/{portfolio_id}/goals` | Doelen; de tien vaardigheden herkennen op naam (zie hieronder) |
| Evaluaties per vaardigheid | `GET /portfolios/{portfolio_id}/goals/{goal_id}/feedback-items` | Niveau, datum, rol (`self` = zelfevaluatie), beoordelaar, `review_request_id` |
| Te beoordelen | `GET /portfolios/{eigen_portfolio_id}/progress-review/invitations/received?status=not_submitted` | Openstaande verzoeken aan de gebruiker: titel, toelichting, student, `created_at`, `suggested_due_date`, status |

- **Vaardigheidsnamen in Portflow** wijken soms in hoofdletters af van LEF ("Kwalitatief Product Maken", "Boodschap Delen"). Vergelijk zonder onderscheid tussen hoofd- en kleine letters.
- **Niveau:** `evaluation.level` verwijst naar `level_set[].id`; het label `"Startniveau"` wordt `0` ([voortgangsregels.md](voortgangsregels.md#startniveau)).
- **Onzeker** (zie §8 van het API-document): de naam van de beoordelaar en de datum van een evaluatie hebben geen vaste plek in de respons. De console-app probeert meerdere velden; de webapp neemt die aanpak over.
- **Paginering:** doorgaan tot een pagina korter is dan de vorige of leeg; niet uitgaan van een vaste paginagrootte.
- **Fouten:** `401` betekent opnieuw verbinden; `404` betekent geen toegang, dus `n/b` ([voortgangsregels.md](voortgangsregels.md#geen-toegang)); andere fouten worden maximaal 3 keer opnieuw geprobeerd.
- **Profielfoto's** (`profile_picture_url`) zijn tijdelijk geldige links; niet langdurig bewaren.

<a id="verversen"></a>
### Verversen

- De laatst opgehaalde Portflow-gegevens worden **lokaal bewaard**, zodat de app direct opent.
- Verversen gebeurt **bij het openen** van de app en met een **knop**. De kop toont "Bijgewerkt om …".
- Tijdens het ophalen is de voortgang zichtbaar. Feedback items worden parallel opgehaald (de console gebruikt 8 tegelijk).

## Privacy

Het dashboard toont gegevens van studenten. Uitgangspunten:

- Alleen tonen wat een coach nodig heeft.
- Geen echte studentgegevens in screenshots, testdata of de repository. Ontwerpscreenshots met echte namen staan in `.gitignore` tot ze geanonimiseerd zijn.
- Studentgegevens blijven lokaal op de laptop van de gebruiker; de lokale database, het Portflow-token en het browserprofiel staan niet in de repository.

## Beslissingen

| Datum | Beslissing | Reden |
|---|---|---|
| 2026-11-09 | Elke coach heeft eigen gegevens; het dashboard draait lokaal op de laptop | Geen gedeelde database of server nodig; gegevens blijven bij de gebruiker |
| 2026-11-09 | Portflow levert alleen evaluaties; studenten, squads, semesters, beroepsrollen en eigen kolommen beheert het dashboard zelf | Indeling staat niet (betrouwbaar) in Portflow; de coach wil die zelf kunnen aanpassen |
| 2026-11-09 | Studenten worden automatisch aan Portflow gekoppeld op naam, met controle door de gebruiker bij twijfel | Weinig handwerk, maar geen stille fouten |
| 2026-11-09 | Inloggen zoals de console-app: Chrome-venster, token opvangen, lokaal bewaren | Enige bekende manier; gebruiker logt in via HU-SSO |
| 2026-11-09 | Portflow-gegevens lokaal bewaren; verversen bij openen en met een knop | Ophalen duurt even; de app moet direct openen |
| 2026-11-09 | Alleen evaluaties van beoordelaars uit de eigen lijst tellen; de vaste uitzondering in de console-app vervalt | Evaluaties door bijvoorbeeld ouderejaars studenten onderscheiden van die door coaches en gildemeesters |
