# Portflow API — overzicht voor hergebruik in een ander project

Dit document beschrijft **alle Portflow/Drieam API-functionaliteit die daadwerkelijk wordt
aangeroepen** door de Python-scripts in deze repository (`portflow.py`,
`portflow_export_full.py`, `export_single_student.py`, `evaluaties.py`, `graph.py`,
`retrieve_token.py`). Het is geschreven zodat een AI/LLM het kan gebruiken als
referentiemateriaal om dezelfde API vanuit een ander project aan te spreken.

> **Bron en status van deze informatie:** dit is een **niet-officiële, reverse-engineerde
> API-documentatie**. Er bestaat (voor zover bekend) geen publieke API-documentatie van
> Drieam/Portflow. Alle endpoints, parameters en velden hieronder zijn afgeleid uit de
> broncode van deze scripts en uit één bewaarde raw-response dump
> (`evaluaties_debug.json`). Velden die niet met zekerheid zijn vastgesteld, zijn expliciet
> als zodanig gemarkeerd (zie [§8 Onzekerheden](#8-onzekerheden--aandachtspunten)).
> Alle voorbeeldnamen, ID's en tokens in dit document zijn **gefingeerd/geanonimiseerd**.

---

## 1. Quick reference

| Aspect | Waarde |
|---|---|
| Platform | Drieam Portflow (portfolio-/e-portfoliotool), hier ingezet door Hogeschool Utrecht via Canvas LTI |
| Base URL | `https://portfolio.drieam.app/api/v1` |
| Auth scheme | `Authorization: Bearer <JWT>` (HTTP header) |
| Content-type responses | JSON (behalve het evidence-downloadendpoint, dat een binaire bestandsstream teruggeeft) |
| HTTP-methodes gebruikt door deze scripts | uitsluitend `GET` (read-only gebruik; er is geen `POST`/`PUT`/`PATCH`/`DELETE` reverse-engineerd) |
| Paginering | query-params `page` (1-based) en `per_page`; response is een platte JSON-array (behalve `/dashboard`, die een object teruggeeft) |
| Max `per_page` | 50 voor de meeste endpoints; `/shares/shared-with-me` lijkt hard op 20 per pagina te zitten ongeacht de gevraagde waarde (zie [§3](#3-algemene-conventies)) |
| Token-type | JWT met `exp`-claim; lokaal te valideren zonder API-call |
| Tokenbron | Geen inlog-/token-endpoint gevonden. Het token komt uit de browsersessie die ontstaat na SSO-login via Canvas (HU) → Portflow-iframe; scripts onderscheppen de `Authorization`-header van uitgaande requests in die browsersessie (zie [§2](#2-authenticatie)) |
| Foutafhandeling | `401` → token verlopen/ongeldig; `404` → resource niet gevonden/niet gekoppeld (niet retryen); overige fouten → max. 3 pogingen met 5s wachttijd |

---

## 2. Authenticatie

Portflow/Drieam kent (voor zover gereverse-engineerd) **geen eigen login- of
token-endpoint** dat vanuit een los script/backend kan worden aangeroepen. De
scripts in deze repo verkrijgen het bearer-token daarom door een echte browsersessie
te starten en het token te onderscheppen:

1. Open een (Chrome-)browser met een persistent profiel naar de LTI-tool in Canvas:
   `https://canvas.hu.nl/courses/51659/external_tools/1134`
2. De gebruiker logt in via de instellings-SSO (HU) als dat nog nodig is.
3. Canvas laadt de Portflow-tool in een iframe (`*.drieam.app`). Die iframe-app doet
   zelf XHR/fetch-requests naar `https://portfolio.drieam.app/api/v1/...` met een
   `Authorization: Bearer <token>`-header.
4. Het script luistert op alle uitgaande netwerk-requests (ook in iframes) naar hosts
   die eindigen op `portflow.io`, `hu.nl` of `drieam.app`, en pakt de eerste geldige
   `Bearer`-token uit de `authorization`-header.
5. De token wordt gevalideerd door 'm te gebruiken in een live call naar
   `GET /api/v1/dashboard`; status `200` = geldig.
6. De token (een JWT) wordt opgeslagen in `.env` als `PORTFLOW_BEARER_TOKEN` en bij elk
   volgend scriptgebruik lokaal gevalideerd (zie hieronder) — pas als hij verlopen is,
   wordt opnieuw een browservenster geopend.

### Header die bij **elke** API-aanroep wordt meegestuurd

```
Authorization: Bearer <jwt-token>
Accept: */*
User-Agent: Mozilla/5.0
```

`Accept` en `User-Agent` lijken niet strikt verplicht (puur defensief door de scripts
meegestuurd), maar `Authorization` is op elk endpoint verplicht; zonder geldige token
komt er een `401` terug.

### Token-geldigheid lokaal controleren (zonder API-call)

Het token is een standaard JWT (`header.payload.signature`, base64url). De scripts
decoderen alleen het payload-deel (geen signature-verificatie, dat kan ook niet zonder
het secret van Drieam) en lezen de `exp`-claim (unix timestamp, seconden):

```python
import base64, json, time

def jwt_is_valid(token: str) -> bool:
    payload_b64 = token.split(".")[1]
    padding = (4 - len(payload_b64) % 4) % 4
    payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=" * padding))
    exp = payload.get("exp")
    if exp is None:
        return True
    return time.time() < exp
```

Uit dezelfde payload is (best-effort) ook een gebruikersnaam te halen via claims als
`name`, `full_name`, `fullname`, `display_name` of `email` (direct, of genest in een
sub-object van de payload).

### "Wie ben ik" / eigen portfolio-ID

Er is **geen bevestigd "whoami"-endpoint** dat betrouwbaar het eigen portfolio-ID
teruggeeft op basis van alleen het token. In plaats daarvan:

- Bij het laden van de Portflow-pagina in de browser staat het eigen portfolio-object
  in een `data-react-props`-attribuut van een `<div data-react-class>`-element:
  ```js
  JSON.parse(el.dataset.reactProps).portfolio.id
  ```
  Dit wordt uit de DOM gelezen tijdens de browser-tokencapture (niet via de API).
- Handmatig is het eigen portfolio-ID ook af te lezen uit de URL van je eigen portfolio
  in de webapp, bijv. `https://portfolio.drieam.app/portfolio/23588/...` → `23588`.
- Zodra het portfolio-ID bekend is, kan de eigen naam alsnog via de API worden
  opgehaald met `GET /portfolios/{eigen_portfolio_id}` (zie [§4.3](#43-get-portfoliosportfolio_id--portfoliodetail)).
- Daarnaast is er (alleen waargenomen in een los browserextensie-bestand in deze repo,
  niet gebruikt door de Python-scripts) een endpoint `GET /api/v1/me` dat vermoedelijk
  eveneens de ingelogde gebruiker + status teruggeeft; dit is in deze repo niet verder
  uitgewerkt of met een voorbeeldrespons bevestigd.

---

## 3. Algemene conventies

- **Base path:** alle endpoints hangen onder `https://portfolio.drieam.app/api/v1`.
- **IDs** zijn integers (portfolio-ID, goal-ID, evidence-ID, review_request_id, user-ID, ...).
- **Timestamps** zijn ISO 8601 UTC-strings met `Z`-suffix, bijv. `"2026-06-03T09:14:38.478Z"`.
- **Lijst-responses** zijn een kale JSON-array (`[ {...}, {...} ]`), **niet** gewrapt in
  `{ "data": [...], "meta": {...} }`. Uitzondering: `GET /dashboard` geeft een object
  terug met een `students`-sleutel.
- **Paginering:** query-params `page` (begint bij `1`) en `per_page`. Stop-conditie die
  de scripts gebruiken: net zo lang doorpagineren tot de teruggekregen pagina **korter**
  is dan de verwachte paginagrootte (of leeg is).
- **Bekende/aannemelijke per-page caps:**

  | Endpoint | Gevraagde `per_page` in scripts | Waargenomen stop-conditie | Conclusie |
  |---|---|---|---|
  | `/portfolios/{id}/goals` | 50 | `len(data) < 50` | server levert max. 50/pagina |
  | `/portfolios/{id}/goals/{goal_id}/feedback-items` | 50 | `len(data) < 50` | server levert max. 50/pagina |
  | `/portfolios/{id}/progress-review/invitations/received` | 50 | `len(data) < 50` | server levert max. 50/pagina |
  | `/dashboard` | 50 | `len(page_students) < 50` | server levert max. 50/pagina |
  | `/shares/shared-with-me` | 50 (of zelfs 200 in `graph.py`) | **`len(data) < 20`** (hardcoded, ongeacht de gevraagde waarde) | dit endpoint lijkt intern een vaste paginagrootte van **20** te hanteren, los van de `per_page`-parameter — behandel dit als een quirk, niet als bug in je eigen implementatie |

  Advies voor een nieuwe implementatie: gebruik per endpoint de **daadwerkelijke
  lengte van de ontvangen pagina** als stop-conditie in plaats van een aangenomen
  constante, om deze quirk niet te hoeven kennen.

- **Foutafhandeling (zoals toegepast in deze scripts):**
  - `401 Unauthorized` → token is verlopen/ongeldig. Geen retry; gebruiker moet een
    nieuw token ophalen (opnieuw inloggen via browser).
  - `404 Not Found` → resource bestaat niet of is niet aan je gekoppeld (bijv. een
    student zonder gekoppeld portfolio, of een goal zonder feedback-items-eindpunt).
    Wordt **niet** geretryed; de aanroepende code slaat deze entiteit over.
  - Overige fouten (timeouts, 5xx, connectiefouten) → retry met max. 3 pogingen en 5
    seconden wachttijd ertussen; daarna opgeven en doorgaan met de rest van de run.
  - Er is **geen rate-limit-afhandeling** (geen `429`/`Retry-After`-logica) in deze
    scripts aangetroffen; dat wil niet zeggen dat de API geen limieten kent.
- **Concurrency:** feedback-items per `goal_id` binnen één portfolio worden parallel
  opgehaald met een `ThreadPoolExecutor` van 8 workers, bovenop één gedeelde
  `requests.Session` met een connection-pool van dezelfde grootte (keep-alive
  hergebruik van TCP/TLS-verbindingen).
- **Timeouts:** 15–30 seconden per request, afhankelijk van het script/endpoint.

---

## 4. Endpoints

### 4.1 `GET /dashboard` — studenten in een sectie (docent-/coachweergave)

Haalt de studenten op die horen bij een Canvas-`section_id` (zoals gezien vanuit het
docenten-/coachaccount waarmee je bent ingelogd).

**Query parameters**

| Param | Verplicht | Voorbeeld | Omschrijving |
|---|---|---|---|
| `section_id` | ja | `72086` | Canvas-section-ID |
| `page` | ja (paginering) | `1` | paginanummer, 1-based |
| `per_page` | ja | `50` | items per pagina (server cap ≈ 50) |

**Voorbeeldaanroep**

```bash
curl -s "https://portfolio.drieam.app/api/v1/dashboard?section_id=72086&page=1&per_page=50" \
  -H "Authorization: Bearer <token>" \
  -H "Accept: */*"
```

**Voorbeeldrespons (geanonimiseerd)**

```json
{
  "students": [
    {
      "id": 10234,
      "name": "Voornaam Achternaam",
      "portfolio_id": 20456
    },
    {
      "id": 10235,
      "name": "Andere Student",
      "portfolio_id": 20457
    }
  ]
}
```

**Gebruikte velden:** `students[].id`, `students[].name`, `students[].portfolio_id`.
Eén student kan meerdere `portfolio_id`'s hebben over verschillende paginas/aanroepen
heen (de scripts verzamelen ze in een `set`).

---

### 4.2 `GET /shares/shared-with-me` — met mij gedeelde portfolio's

Lijst van portfolio's/uitnodigingen die aan de ingelogde gebruiker zijn gedeeld —
typisch door studenten die jou als beoordelaar/coach hebben toegevoegd. Dit is het
**primaire endpoint** om erachter te komen welke studentportfolio's je mag inzien,
zonder dat je een `section_id` hoeft te kennen.

**Query parameters**

| Param | Verplicht | Voorbeeld | Omschrijving |
|---|---|---|---|
| `order_by` | nee | `created_at` | sorteerveld |
| `order_direction` | nee | `desc` | `asc`/`desc` |
| `page` | ja | `1` | paginanummer |
| `per_page` | ja | `50` | zie paginering-quirk hierboven (effectief ~20/pagina) |

**Voorbeeldaanroep**

```bash
curl -s "https://portfolio.drieam.app/api/v1/shares/shared-with-me?order_by=created_at&order_direction=desc&page=1&per_page=50" \
  -H "Authorization: Bearer <token>" \
  -H "Accept: */*"
```

**Voorbeeldrespons (geanonimiseerd)**

```json
[
  {
    "portfolio_id": 20456,
    "inviter": {
      "id": 10234,
      "name": "Voornaam Achternaam",
      "current_role": "student"
    }
  }
]
```

**Gebruikte velden:** `portfolio_id`, `inviter.id`, `inviter.name`,
`inviter.current_role` (gefilterd op `"student"` om alleen studentportfolio's over te
houden; andere rollen, bijv. medebeoordelaars, worden genegeerd).

---

### 4.3 `GET /portfolios/{portfolio_id}` — portfoliodetail

Detail van één portfolio, inclusief de eigenaar (`user`). Wordt in deze scripts alleen
gebruikt om de **naam van de ingelogde gebruiker zelf** op te halen (dus aangeroepen
met het *eigen* portfolio-ID, niet dat van een student).

**Voorbeeldaanroep**

```bash
curl -s "https://portfolio.drieam.app/api/v1/portfolios/23588" \
  -H "Authorization: Bearer <token>" \
  -H "Accept: */*"
```

**Voorbeeldrespons (geanonimiseerd, alleen bevestigde velden)**

```json
{
  "id": 23588,
  "user": {
    "name": "Eigen Naam",
    "full_name": "Eigen Naam",
    "email": "eigen.naam@voorbeeld.nl"
  }
}
```

**Gebruikte velden:** `user.name` (fallback `user.full_name`, dan `user.email`). Er
zijn vermoedelijk meer velden in de echte respons (bv. goal-samenvattingen), maar die
worden door deze scripts niet gelezen.

---

### 4.4 `GET /portfolios/{portfolio_id}/goals` — doelen/vaardigheden/beroepstaken

Lijst van "goals" binnen een portfolio: dit zijn zowel de 10 generieke HBO-i
vaardigheden (zie [§9](#9-bijlage-vaste-referentiedata-niet-via-api-opgehaald-maar-hardcoded-in-deze-scripts)) als beroepsproduct-/
beroepstaak-achtige doelen, afhankelijk van hoe de opleiding het portfolio heeft
ingericht.

**Query parameters:** `page`, `per_page` (max. 50).

**Voorbeeldaanroep**

```bash
curl -s "https://portfolio.drieam.app/api/v1/portfolios/20456/goals?page=1&per_page=50" \
  -H "Authorization: Bearer <token>" \
  -H "Accept: */*"
```

**Voorbeeldrespons (geanonimiseerd, alleen bevestigde velden)**

```json
[
  { "id": 126908, "name": "Overzicht creëren" },
  { "id": 126909, "name": "Kritisch oordelen" },
  { "id": 126910, "name": "Boodschap Delen" }
]
```

**Gebruikte velden:** `id`, `name`. `name` komt (vrijwel) exact overeen met een van de
10 vaardigheidsnamen of een beroepsproduct-/beroepstaaknaam (zie bijlage). Er zijn
waarschijnlijk meer velden in de echte respons (bv. voortgang, status, gekoppeld
beroepsproduct) die hier niet gebruikt/gedocumenteerd worden.

**Foutgedrag:** `404` op dit endpoint betekent "deze student/dit portfolio heeft geen
(toegankelijk) portfolio voor jou" en wordt door de scripts als "geen gekoppeld
portfolio" behandeld (niet als harde fout).

---

### 4.5 `GET /portfolios/{portfolio_id}/goals/{goal_id}/feedback-items` — evaluaties/feedback op één doel

Het belangrijkste endpoint: geeft alle "feedback items" (zelfevaluaties,
beoordelingen, opmerkingen) voor één `goal_id` binnen een portfolio.

**Query parameters:** `page`, `per_page` (max. 50).

**Voorbeeldaanroep**

```bash
curl -s "https://portfolio.drieam.app/api/v1/portfolios/20456/goals/126908/feedback-items?page=1&per_page=50" \
  -H "Authorization: Bearer <token>" \
  -H "Accept: */*"
```

**Voorbeeldrespons (geanonimiseerd, gereconstrueerd uit veldgebruik in de code — zie
toelichting hieronder)**

```json
[
  {
    "type": "criterion_evaluation",
    "role": "self",
    "status": "submitted",
    "created_at": "2026-04-18T10:03:00.000Z",
    "updated_at": "2026-04-20T08:15:00.000Z",
    "evaluation": {
      "level": 502,
      "level_set": [
        { "id": 501, "label": "Startniveau" },
        { "id": 502, "label": "1" },
        { "id": 503, "label": "2" }
      ],
      "review_request_id": 81600,
      "review_request_title": "OC & KO 1ste evaluatie",
      "review_request_scored": true,
      "sub_criterion_name": null,
      "comment": "Toelichting/zelfevaluatietekst van de student...",
      "submitted_at": "2026-04-18T10:03:00.000Z"
    }
  },
  {
    "type": "sub_criterion_evaluation",
    "role": "assessor",
    "status": "scored",
    "created_at": "2026-04-20T08:15:00.000Z",
    "evaluation": {
      "level": 503,
      "level_set": [
        { "id": 501, "label": "Startniveau" },
        { "id": 502, "label": "1" },
        { "id": 503, "label": "2" }
      ],
      "review_request_id": 81600,
      "review_request_scored": true,
      "sub_criterion_name": "Vereisten analyseren",
      "comment": "Feedback van de beoordelaar...",
      "reviewer": { "name": "Naam Beoordelaar" },
      "evaluated_at": "2026-04-20T08:15:00.000Z"
    }
  }
]
```

**Bevestigd gebruikte velden (vaste key, rechtstreeks gelezen):**

| Veld | Type | Omschrijving |
|---|---|---|
| `type` | string | `"criterion_evaluation"` (evaluatie op het doel zelf) of `"sub_criterion_evaluation"` (evaluatie op een subcriterium/beroepstaak binnen het doel). Andere waarden worden door de scripts genegeerd. |
| `role` | string | `"self"` = zelfevaluatie door de student. Elke andere waarde wordt behandeld als "niet self" (vermoedelijk iets als `"assessor"` of `"coach"`, maar dat is **niet met zekerheid vastgesteld** — zie [§8](#8-onzekerheden--aandachtspunten)). |
| `evaluation` | object \| null | Null/ontbrekend = er is nog geen daadwerkelijke evaluatie ingevuld (pending). |
| `evaluation.level` | int \| null | Verwijst naar een `id` in `evaluation.level_set`. |
| `evaluation.level_set` | array van `{id, label}` | Niveauschaal; `label == "Startniveau"` wordt in de UI als niveau `"0"` getoond, overige labels (bv. `"1"`, `"2"`) 1-op-1. |
| `evaluation.review_request_id` | int | ID van het onderliggende beoordelingsverzoek; koppelt meerdere feedback-items (over meerdere goals/subcriteria) die bij **dezelfde** beoordelingsronde horen. |
| `evaluation.review_request_scored` | bool \| null | `true` zodra het hele verzoek door de beoordelaar is afgerond/gescoord. |
| `evaluation.review_request_title` | string | Titel die de student aan het verzoek gaf. |
| `evaluation.sub_criterion_name` | string \| null | Naam van het subcriterium (alleen bij `type == "sub_criterion_evaluation"`); hierin staan vaak beroepstaak-/beroepsproductnamen. |

**Datumveld (niet één vaste key — eerste match wint):** de scripts proberen op zowel
`item` als `item.evaluation` achtereenvolgens: `submitted_at`, `evaluated_at`,
`evaluation_date`, `graded_at`, `reviewed_at`, `assessed_at`, `created_at`,
`updated_at`, `date`. Gebruik voor een nieuwe implementatie bij voorkeur de meest
specifieke die aanwezig is.

**Tekstinhoud (niet één vaste key — eerste match wint, zie [§8](#8-onzekerheden--aandachtspunten)):**
geprobeerde keys op zowel `item` als `item.evaluation`: `comment`, `comments`, `body`,
`content`, `text`, `message`, `description`, `toelichting`, `feedback`, `reflection`,
`self_evaluation`, `self_evaluation_text`. Deze tekst kan **HTML bevatten**, inclusief
ingebedde "mentions" naar bewijsstukken (zie [§6](#6-bewijsstukkenevidence-ophalen-inline-mentions--download)).

**Beoordelaarsnaam (niet één vaste key):** geprobeerd worden achtereenvolgens
`item.user.name`, `item.author.name`, `item.creator.name`, `item.reviewer.name`,
`item.evaluator.name`, `item.created_by.name`, en vlakke varianten als
`item.user_name`, `item.reviewer_name`, enz. Pas als geen van die aanwezig is, valt de
code terug op een generieke, diepe zoektocht door het hele object naar een sleutel die
op "naam" lijkt in een context die op "beoordelaar" lijkt (hint-tokens: `review`,
`evaluator`, `assessor`, `author`, `coach`, `teacher`, `created_by`, `creator`, `user`,
`inviter`, `sender`, `owner`, `by`).

**Foutgedrag:** `404` → dit goal/portfolio heeft geen feedback-items-endpoint
beschikbaar voor jou (overslaan).

---

### 4.6 `GET /portfolios/{portfolio_id}/progress-review/invitations/received` — ontvangen beoordelingsverzoeken

Geeft beoordelingsverzoeken die **naar** de eigenaar van `portfolio_id` zijn gestuurd.
Wordt in de praktijk aangeroepen met het **eigen** portfolio-ID (`OWN_PORTFOLIO_ID`) om
te zien welke evaluatieverzoeken van studenten nog door jou (als beoordelaar) moeten
worden opgepakt.

**Query parameters**

| Param | Verplicht | Voorbeeld | Omschrijving |
|---|---|---|---|
| `order_by` | nee | `created_at` | sorteerveld |
| `order_direction` | nee | `desc` | `asc`/`desc` |
| `page` | ja | `1` | paginanummer |
| `per_page` | ja | `50` | server cap = 50 |
| `status` | nee | `not_submitted` | serverside filter; weggelaten → alle statussen |

**Voorbeeldaanroep**

```bash
curl -s "https://portfolio.drieam.app/api/v1/portfolios/23588/progress-review/invitations/received?order_by=created_at&order_direction=desc&page=1&per_page=50&status=not_submitted" \
  -H "Authorization: Bearer <token>" \
  -H "Accept: */*"
```

**Voorbeeldrespons (geanonimiseerde versie van een echte, bewaarde voorbeeldrespons)**

```json
[
  {
    "id": 165479,
    "reviewer_id": 17708,
    "review_request_id": 81600,
    "review_request_note": "<p><span data-type=\"mention\" data-id=\"704899\" data-label=\"Onderzoek Front.docx\" data-mention-type=\"evidence\" data-portfolio-id=\"20456\">@Onderzoek Front.docx</span> Toelichting van de student bij dit verzoek...</p>",
    "portfolio_id": 20456,
    "status": "not_started",
    "submitted_at": null,
    "denied_at": null,
    "created_at": "2026-06-03T09:14:38.478Z",
    "updated_at": "2026-06-03T09:14:38.478Z",
    "review_request_title": "OC & KO 1ste evaluatie",
    "suggested_due_date": null,
    "requester": {
      "id": 20161,
      "user_type": "lti",
      "pronouns": null,
      "custom_pronouns": null,
      "lms_id": "278567",
      "current_role": "student",
      "name": "Voornaam Achternaam",
      "profile_picture_url": "https://portfolio-lti-production.s3.eu-west-1.amazonaws.com/.../avatar-50.png?X-Amz-Signature=..."
    }
  },
  {
    "id": 165472,
    "reviewer_id": 17708,
    "review_request_id": 81596,
    "review_request_note": "<p></p>",
    "portfolio_id": 20457,
    "status": "not_started",
    "submitted_at": null,
    "denied_at": null,
    "created_at": "2026-06-03T09:10:05.862Z",
    "updated_at": "2026-06-03T09:10:05.862Z",
    "review_request_title": "Flexibel opstellen niv 2",
    "suggested_due_date": "2026-06-25T22:00:00.000Z",
    "requester": {
      "id": 19499,
      "user_type": "lti",
      "current_role": "student",
      "name": "Andere Student",
      "profile_picture_url": "https://portfolio-lti-production.s3.eu-west-1.amazonaws.com/.../avatar-50.png?X-Amz-Signature=..."
    }
  }
]
```

**Velden:**

| Veld | Type | Omschrijving |
|---|---|---|
| `id` | int | ID van deze uitnodiging/invitation-record |
| `reviewer_id` | int | user-ID van de beoordelaar (= jij, de ingelogde gebruiker) |
| `review_request_id` | int | koppelt aan dezelfde `evaluation.review_request_id` op de feedback-items van het goal-endpoint |
| `review_request_title` | string | titel die de student aan het verzoek gaf |
| `review_request_note` | string (HTML) | toelichting van de student; kan evidence-mentions bevatten (zie §6) |
| `portfolio_id` | int | portfolio van de student die het verzoek stuurde |
| `status` | string | waargenomen/besproken waarden: `not_started`, `in_progress`, `submitted`, `scored`, `denied` |
| `submitted_at` / `denied_at` | string\|null | ISO-timestamp of `null` |
| `created_at` / `updated_at` | string | ISO-timestamp |
| `suggested_due_date` | string\|null | door de student voorgestelde uiterste datum |
| `requester` | object | zie hieronder |
| `requester.id` | int | user-ID van de student |
| `requester.name` | string | naam van de student |
| `requester.current_role` | string | `"student"` in alle waargenomen gevallen |
| `requester.user_type` | string | `"lti"` (via Canvas LTI) |
| `requester.lms_id` | string | Canvas-user-ID |
| `requester.profile_picture_url` | string | **pre-signed S3 URL, tijdelijk geldig** (bevat `X-Amz-*`-query-parameters met vervaltijd — cache deze URL niet lang) |
| `requester.pronouns` / `requester.custom_pronouns` | string\|null | optioneel |

**Query-param `status=not_submitted`** is een serverside filterwaarde die **niet**
letterlijk overeenkomt met een van de teruggegeven `status`-waarden; vermoedelijk
matcht dit op `not_started` + `in_progress` samen (niet 100% bevestigd, enkel afgeleid
uit het gebruik in de scripts voor "openstaande evaluaties").

---

### 4.7 `GET /portfolios/{portfolio_id}/evidence/{evidence_id}` — bewijsstuk downloaden

Download van één bewijsstuk/bestand ("evidence") als binaire stream. `portfolio_id` en
`evidence_id` komen **niet** uit een apart "lijst evidence op"-endpoint, maar worden
geparsed uit HTML-tekstvelden (zie [§6](#6-bewijsstukkenevidence-ophalen-inline-mentions--download)).

**Voorbeeldaanroep**

```bash
curl -s "https://portfolio.drieam.app/api/v1/portfolios/20456/evidence/704899" \
  -H "Authorization: Bearer <token>" \
  -H "Accept: */*" \
  -o "bewijsstuk.bin"
```

**Respons:** geen JSON, maar de ruwe bestandsinhoud (stream). Bruikbare response-headers:
- `Content-Type` → gebruikt om een bestandsextensie te bepalen (`mimetypes.guess_extension`)
- `Content-Disposition` → kan een `filename=` of `filename*=UTF-8''...` bevatten, waaruit
  de oorspronkelijke bestandsnaam wordt gehaald

**Statuscodes:** `>= 400` → bewijsstuk niet beschikbaar/geen toegang; scripts schrijven
dan een `.txt`-bestand met metadata in plaats van het bestand zelf, in plaats van hard
te falen.

---

## 5. Datamodellen — samengevatte veldreferentie

### Student / gebruiker (zoals voorkomend in meerdere responses)

```json
{
  "id": 10234,
  "name": "Voornaam Achternaam",
  "current_role": "student",
  "user_type": "lti",
  "lms_id": "278567",
  "profile_picture_url": "https://...s3.../avatar-50.png?X-Amz-Signature=...",
  "pronouns": null,
  "custom_pronouns": null
}
```

Niet elk endpoint geeft alle velden tegelijk terug — zie per-endpoint voorbeeld hierboven.

### Goal

```json
{ "id": 126908, "name": "Overzicht creëren" }
```

### Feedback item (`criterion_evaluation` / `sub_criterion_evaluation`)

```json
{
  "type": "criterion_evaluation | sub_criterion_evaluation",
  "role": "self | <overige rolwaarde, vermoedelijk assessor/coach>",
  "status": "string",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "evaluation": {
    "level": "int | null (verwijst naar level_set[].id)",
    "level_set": [ { "id": "int", "label": "string (bv. 'Startniveau', '1', '2', ...)" } ],
    "review_request_id": "int",
    "review_request_title": "string",
    "review_request_scored": "bool | null",
    "sub_criterion_name": "string | null",
    "<tekstveld, naam varieert>": "string (HTML, kan evidence-mentions bevatten)",
    "<datumveld, naam varieert>": "ISO-8601"
  }
}
```

### Invitation / review request (received)

Zie volledige tabel in [§4.6](#46-get-portfoliosportfolio_idprogress-reviewinvitationsreceived--ontvangen-beoordelingsverzoeken).

---

## 6. Bewijsstukken/evidence ophalen: inline mentions + download

Bewijsstukken ("evidence") worden **niet** via een los lijst-endpoint opgehaald. Ze
zitten verwerkt als *inline mentions* in HTML-tekstvelden (bijvoorbeeld
`review_request_note` op het invitations-endpoint, of het tekstveld binnen
`evaluation` op het feedback-items-endpoint). Een mention ziet er zo uit:

```html
<span data-type="mention"
      data-id="704899"
      data-label="Onderzoek Front.docx"
      data-mention-type="evidence"
      data-portfolio-id="20456">@Onderzoek Front.docx</span>
```

**Stappen om een bewijsstuk te downloaden:**

1. Parse alle `<span ... data-mention-type="evidence" ...>`-tags uit elk tekstveld met
   een regex (of HTML-parser) en lees `data-id`, `data-label`, `data-portfolio-id`.
   Regex zoals gebruikt in deze repo:
   ```python
   import re
   pattern = re.compile(
       r'data-id="(?P<id>\d+)"[^>]*data-label="(?P<label>[^"]+)"'
       r'[^>]*data-mention-type="evidence"[^>]*data-portfolio-id="(?P<portfolio_id>\d+)"'
   )
   ```
2. Roep per gevonden mention `GET /portfolios/{data-portfolio-id}/evidence/{data-id}`
   aan (zie [§4.7](#47-get-portfoliosportfolio_idevidenceevidence_id--bewijsstuk-downloaden)).
3. Gebruik `data-label` als voorgestelde bestandsnaam; val terug op
   `Content-Disposition`/`Content-Type` uit de downloadrespons als er geen label is.

Daarnaast bevat een generieke attachment-scanner in deze scripts (`gather_attachments`)
logica om in **willekeurige** JSON-structuren te zoeken naar objecten met een sleutel
`download_url`, `file_url`, `url`, `href` of `link` waarvan de waarde met `http` begint
— dit suggereert dat sommige responses (niet 100% geïdentificeerd welke) directe,
voorgetekende (S3) download-URLs kunnen bevatten naast/in plaats van het
`/evidence/{id}`-endpoint. Zulke URLs worden dan direct gedownload (met dezelfde
`Authorization`-header, al is die voor een pre-signed S3-URL normaliter niet nodig).

---

## 7. Praktische implementatiepatronen (herbruikbare Python-snippets)

### 7.1 Generieke headers

```python
def headers_for_token(token: str) -> dict:
    return {
        "accept": "*/*",
        "authorization": f"Bearer {token}",
        "user-agent": "Mozilla/5.0",
    }
```

### 7.2 Generieke, gepagineerde GET met retry

```python
import time
import requests

def request_with_retries(session, url, headers, params=None, max_attempts=3):
    for attempt in range(1, max_attempts + 1):
        try:
            response = session.get(url, headers=headers, params=params, timeout=15)
            if response.status_code == 401:
                return "TOKEN_EXPIRED"
            if response.status_code == 404:
                return response  # niet retryen; laat aanroeper beslissen
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException:
            if attempt < max_attempts:
                time.sleep(5)
            else:
                return None


def get_all_pages(session, url, headers, extra_params=None, per_page=50):
    items = []
    page = 1
    while True:
        params = {"page": page, "per_page": per_page, **(extra_params or {})}
        response = request_with_retries(session, url, headers, params)
        if response in (None, "TOKEN_EXPIRED"):
            break
        if isinstance(response, requests.Response) and response.status_code == 404:
            break
        data = response.json()
        if not data:
            break
        items.extend(data)
        if len(data) < per_page:      # pas aan naar daadwerkelijke paginalengte i.p.v. aangenomen constante
            break
        page += 1
    return items
```

### 7.3 Niveau van een evaluatie bepalen

```python
def resolve_level(evaluation: dict) -> str | None:
    level_id = evaluation.get("level")
    if not level_id:
        return None
    for lvl in evaluation.get("level_set", []):
        if lvl["id"] == level_id:
            return "0" if lvl["label"] == "Startniveau" else lvl["label"]
    return None
```

### 7.4 Parallel ophalen van feedback-items per goal

```python
from concurrent.futures import ThreadPoolExecutor

def get_feedback_for_goals(session, token, portfolio_id, goal_ids, max_workers=8):
    headers = headers_for_token(token)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        def fetch(goal_id):
            return get_all_pages(
                session,
                f"https://portfolio.drieam.app/api/v1/portfolios/{portfolio_id}/goals/{goal_id}/feedback-items",
                headers,
            )
        results = pool.map(fetch, goal_ids)
        return dict(zip(goal_ids, results))
```

---

## 8. Onzekerheden / aandachtspunten

Belangrijk voor een nieuwe implementatie om niet blind op te vertrouwen:

1. **Geen officiële documentatie.** Alles hierboven is afgeleid uit cliëntcode en één
   voorbeelddump; velden die niet door deze scripts gebruikt worden, zijn onbekend.
2. **Tekstveld van een evaluatie heeft geen vaste naam.** De code probeert ~10
   kandidaat-sleutelnamen (`comment`, `body`, `content`, `text`, `message`,
   `description`, `toelichting`, `feedback`, `reflection`, `self_evaluation`,
   `self_evaluation_text`) en neemt de eerste niet-lege string. Controleer dit zelf
   tegen een live response voor je eigen implementatie.
3. **Naam van de beoordelaar heeft geen vaste locatie.** Idem: meerdere kandidaatpaden
   worden geprobeerd, met als laatste redmiddel een diepe, heuristische zoektocht door
   het hele object. Alleen `role == "self"` (zelfevaluatie door de student) is een
   **bevestigde**, letterlijk gecontroleerde waarde; de waarde voor "beoordeeld door
   een ander" is in de code nooit letterlijk gematcht en dus niet zeker vastgesteld.
4. **`/shares/shared-with-me` paginering** lijkt in de praktijk op 20 items/pagina
   gelimiteerd, onafhankelijk van de gevraagde `per_page` — gebruik de daadwerkelijke
   paginalengte als stop-conditie, niet een aangenomen constante.
5. **`profile_picture_url` is een pre-signed S3-URL** met een vervaltijd in de
   query-string (`X-Amz-Expires`/`X-Amz-Date`); niet geschikt om langdurig te cachen.
6. **Alleen GET-gebruik gereverse-engineerd.** Er is geen inzicht in hoe je via de API
   zelf een evaluatie zou **indienen/schrijven** (self-evaluatie aanmaken, beoordeling
   geven, bewijsstuk uploaden) — deze scripts zijn puur lezend.
7. **Rate limiting** is niet waargenomen/behandeld; ga hier voorzichtig mee om bij hoog
   verkeer (bv. expliciete backoff en niet onnodig veel parallelle requests).
8. **Authenticatie vereist een echte browsersessie** (SSO/LTI-login); er is geen
   service-account- of API-key-achtige manier bekend om los van een ingelogde
   eindgebruiker een token te verkrijgen.

---

## 9. Bijlage: vaste referentiedata (niet via API opgehaald, maar hardcoded in deze scripts)

### 9.1 De 10 HBO-i vaardigheden (`goal.name` ↔ code)

| `goal.name` (zoals in de API) | Code |
|---|---|
| Overzicht creëren | OC |
| Kritisch oordelen | KO |
| Juiste kennis ontwikkelen | JKO |
| Kwalitatief Product Maken | KPM |
| Plannen | PL |
| Boodschap Delen | BD |
| Samenwerken | SW |
| Flexibel opstellen | FO |
| Pro-actief handelen | PH |
| Reflecteren | RE |

### 9.2 Waargenomen `status`-waarden op invitations/received

| Waarde | Betekenis (NL) |
|---|---|
| `not_started` | Niet begonnen |
| `in_progress` | In uitvoering |
| `submitted` | Ingediend |
| `scored` | Beoordeeld |
| `denied` | Geweigerd |
