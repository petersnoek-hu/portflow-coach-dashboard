# 003 – Portflow verbinden

**Status:** uitgewerkt <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-09

## Doel

Als **coach** of **gildemeester** wil ik één keer inloggen bij Portflow en daarna verbonden blijven zolang de app draait, zodat het dashboard gegevens kan ophalen zonder dat ik steeds een token hoef te regelen. Lukt automatisch verversen niet, dan wil ik dat duidelijk zien en met één klik opnieuw kunnen inloggen.

Inspiratie: de console-app ([`docs/portflow-console-app.py`](../../docs/portflow-console-app.py), functies `get_bearer_token`, `_capture_token_via_browser`, `ensure_own_portfolio_id`). Achtergrond: [architectuur.md](../../docs/architectuur.md#inloggen).

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Hoe het werkt (achtergrond)

- Portflow heeft **geen login- of refresh-endpoint**. Een token ontstaat als de Portflow-tool in Canvas geladen wordt; dan doet Portflow verzoeken met `Authorization: Bearer <token>`.
- De app opent daarom een eigen **Chrome-venster** (via Playwright, met een **blijvend browserprofiel**), laat de gebruiker zo nodig inloggen via HU-SSO en **vangt het token op**. Omdat het profiel bewaard blijft, is de HU-login bij een volgende keer vaak nog geldig. Inloggen gaat dan zonder dat de gebruiker iets hoeft te doen.
- Het token is een JWT dat **8 uur** geldig is (gemeten op 2026-11-09: `exp − iat` = 8 uur). Het bevat geen naam; de naam komt uit `GET /portfolios/{eigen portfolio-id}`.
- **Verversen** = hetzelfde opvangen, maar onzichtbaar (headless) met hetzelfde profiel. Dat werkt zolang de HU-login in het profiel nog geldig is.

## Functionele eisen

### Verbinden

- [ ] **F1 – Verbinden met Portflow.** Een knop **"Verbinden met Portflow"** (in het verbindingspaneel en in Instellingen) opent een Chrome-venster op de Portflow-tool in Canvas. De gebruiker logt zo nodig in. Zodra een token is opgevangen en gecontroleerd (`GET /dashboard` geeft 200), sluit het venster vanzelf en is de app verbonden.
  - *Acceptatie:* bij een geldige HU-login in het profiel opent het venster, sluit het binnen enkele seconden en toont de bovenbalk "Verbonden".
- [ ] **F2 – Eigen portfolio en naam.** Tijdens het verbinden leest de app het eigen portfolio-id uit de Portflow-pagina en haalt de naam op met `GET /portfolios/{id}`. De naam vervangt "Gebruiker" in de zijbalk (met initialen) en komt in de lijst met coaches en gildemeesters ([gegevensmodel.md](../../docs/gegevensmodel.md#gebruiker)).
  - *Acceptatie:* na het verbinden staat onderin de zijbalk de Portflow-naam van de gebruiker.
- [ ] **F3 – De app blijft bruikbaar.** Tijdens het inloggen kun je in het dashboard verder werken; de bovenbalk toont "Inloggen…" en het paneel zegt "Log in in het Chrome-venster". Er loopt hooguit één inlogpoging tegelijk.
  - *Acceptatie:* tijdens het inloggen laden andere pagina's gewoon; een tweede klik op Verbinden start geen tweede venster.
- [ ] **F4 – Afbreken en time-out.** Sluit de gebruiker het venster, of is er na 5 minuten geen token, dan stopt de poging. De app meldt dat ontwikkelingsgericht ("Inloggen is niet afgerond. Probeer het opnieuw.") en keert terug naar de vorige toestand.
  - *Acceptatie:* venster dichtklikken → melding en status "Niet verbonden" (of de vorige status).
- [ ] **F5 – Token plakken (reserve).** In het paneel staat onder "Lukt het niet?" de mogelijkheid om een token te plakken. Bij plakken controleert de app de vorm (JWT), de vervaltijd en de toegang (`GET /dashboard`). Is het eigen portfolio-id onbekend, dan vraagt de app erom, met uitleg waar je het vindt (in de URL van je eigen portfolio), en controleert het (`access_type == "owner"`).
  - *Acceptatie:* een verlopen of ongeldig token wordt geweigerd met een begrijpelijke uitleg; een geldig token geeft "Verbonden".

### Verbonden blijven

- [ ] **F6 – Bij het starten.** Bij het starten leest de app het bewaarde token:
  - nog geldig → meteen verbonden;
  - verlopen → eerst stil verversen (F7);
  - geen token, of verversen mislukt → het inlogvenster (F1) opent **meteen**.
  - *Acceptatie:* starten met een geldig token → "Verbonden" zonder venster; starten zonder token → het Chrome-venster opent en de status is "Inloggen…".
- [ ] **F7 – Stil verversen.** Zolang de app draait, ververst hij het token **1 uur voor het verlopen** onzichtbaar (headless Chrome met hetzelfde profiel, time-out 60 seconden). Lukt dat, dan wisselt het token zonder dat de gebruiker iets merkt, behalve "Laatst ververst" in het paneel.
  - *Acceptatie:* met een token dat over 59 minuten verloopt, start de app binnen een minuut een verversing; na succes ligt de nieuwe vervaltijd ongeveer 8 uur verder.
- [ ] **F8 – Terugval op een zichtbaar venster.** Lukt onzichtbaar verversen niet (bijvoorbeeld omdat de HU-inlogpagina headless browsers weigert), dan opent de app kort een **zichtbaar** Chrome-venster met hetzelfde profiel, dat vanzelf sluit zodra het token gevonden is. In Instellingen kan de gebruiker kiezen voor **"Altijd zichtbaar verversen"**; dan slaat de app de onzichtbare poging over.
  - *Acceptatie:* gesimuleerde mislukte headless-poging → er opent een zichtbaar venster; met de instelling aan wordt headless niet geprobeerd.
- [ ] **F9 – Opnieuw inloggen nodig.** Lukt ook het zichtbare venster niet (de HU-login is verlopen en de gebruiker logt niet in, of het venster wordt gesloten), dan wordt de status oranje **"Opnieuw inloggen nodig"** met de vervaltijd. Er verschijnt een knop **"Opnieuw inloggen"** die F1 start. De app probeert automatisch verversen hooguit **één keer per 15 minuten** opnieuw.
  - *Acceptatie:* gesimuleerde mislukte verversing → oranje status met de knop; de huidige (nog geldige) gegevens blijven bruikbaar; binnen 15 minuten geen nieuwe automatische poging.
- [ ] **F10 – Verlopen.** Is het token verlopen, of geeft Portflow `401`, dan wordt de status rood **"Verlopen"** en verschijnt op elke pagina een banner: "Je Portflow-verbinding is verlopen. Je ziet gegevens van {tijd}. [Opnieuw inloggen]". Bewaarde gegevens blijven zichtbaar ([architectuur.md](../../docs/architectuur.md#verversen)).
  - *Acceptatie:* token met verlopen `exp` → rode status en banner; de banner verdwijnt na opnieuw inloggen.
- [ ] **F11 – Verbinding verbreken.** In het paneel en in Instellingen: **"Verbinding verbreken"** verwijdert het token (na bevestiging). Het browserprofiel blijft staan.
  - *Acceptatie:* na verbreken is de status "Niet verbonden" en staat er geen token meer in `.env`.

### Weergave

- [ ] **F12 – Status in de bovenbalk.** De statusknop rechtsboven toont altijd de toestand:

  | Toestand | Stip | Tekst | Subtekst |
  |---|---|---|---|
  | Niet verbonden | grijs | Niet verbonden | — |
  | Inloggen | blauw, pulserend | Inloggen… | Log in in het Chrome-venster |
  | Verbonden | groen | Verbonden | tot 16:59 |
  | Verversen | groen, pulserend | Verversen… | — |
  | Opnieuw inloggen nodig | oranje | Opnieuw inloggen nodig | verloopt om 16:59 |
  | Verlopen | rood (`#C17661`) | Verlopen | sinds 16:59 |

  - *Acceptatie:* elke toestand is met een test op te roepen en toont de stip, de tekst en de subtekst uit de tabel.
- [ ] **F13 – Verbindingspaneel.** Een klik op de statusknop opent een paneel met:
  - ingelogd als {naam};
  - eigen portfolio-id;
  - token geldig tot {tijd} (nog {x} uur {y} min);
  - laatst ververst {tijd} (automatisch of handmatig);
  - de knoppen die bij de toestand horen (Verbinden / Opnieuw inloggen / Annuleren / Verbinding verbreken);
  - "Lukt het niet? Token plakken".

  Escape of een klik ernaast sluit het paneel.
  - *Acceptatie:* bij "Verbonden" toont het paneel naam, vervaltijd en "Verbinding verbreken".
- [ ] **F14 – Live bijwerken.** De status werkt zichzelf bij zonder de pagina te verversen: elke 2 seconden tijdens inloggen of verversen, anders elke minuut (via `app.js` en een status-endpoint).
  - *Acceptatie:* na het sluiten van het inlogvenster wordt de bovenbalk binnen 2 seconden groen, zonder herladen.
- [ ] **F15 – Instellingen.** Een sectie **"Portflow-koppeling"** in Instellingen toont dezelfde gegevens en knoppen als het paneel, plus het veld **Canvas-adres van de Portflow-tool** (standaard `https://canvas.hu.nl/courses/51659/external_tools/1134`) en het vinkje **"Altijd zichtbaar verversen"** (F8).
  - *Acceptatie:* het Canvas-adres aanpassen en opslaan → de volgende inlogpoging opent dat adres.

### Installatie en fouten

- [ ] **F16 – Playwright of Chrome ontbreekt.** Ontbreekt het Python-pakket `playwright`, of Google Chrome, dan legt het paneel uit wat er nodig is, met de exacte opdracht (bijvoorbeeld `pip install playwright` of `python -m playwright install chromium`). De app installeert niets zelf. Token plakken blijft mogelijk.
  - *Acceptatie:* zonder Playwright toont "Verbinden" de uitleg in plaats van een fout.
- [ ] **F17 – Browserprofiel in gebruik.** Staat er nog een app-browservenster open (het profiel is vergrendeld), dan meldt de app: "Er staat nog een inlogvenster open. Sluit dat en probeer opnieuw."
  - *Acceptatie:* een tweede poging terwijl het profiel vergrendeld is, geeft deze melding.

### Buiten scope

- Gegevens ophalen en verversen (studenten, evaluaties): eigen spec
- Studenten kiezen uit "gedeeld met mij": spec *Studenten toevoegen*
- Een browserextensie voor je eigen browser

## Schermen

| Scherm | Bestand | Opmerking |
|---|---|---|
| Statusknop rechtsboven | [`screenshots/kompas-dashboard-ontwerp.png`](../../screenshots/kompas-dashboard-ontwerp.png), "Portflow · Verbonden" | In het ontwerp alleen "Verbonden"; de overige toestanden staan in F12 |
| Paneel, banner, Instellingen | — | Nog geen ontwerp; volg [design-system.md](../../docs/design-system.md) |

Schets van het paneel (bij "Verbonden"):

```
┌──────────────────────────────────────┐
│ ● Verbonden met Portflow             │
│   Ingelogd als  A. Coach             │
│   Eigen portfolio  23588             │
│   Geldig tot  16:59 (nog 3 u 12 min) │
│   Laatst ververst  08:59 · automatisch│
│                                      │
│   [Opnieuw verbinden] [Verbreken]    │
│   Lukt het niet? Token plakken       │
└──────────────────────────────────────┘
```

## Data

- **Bron:** Portflow via de browsersessie; API: `GET /dashboard` (controle), `GET /portfolios/{eigen id}` (naam). Zie [architectuur.md](../../docs/architectuur.md#portflow-api).
- **Bewaren:**
  - **Token** in `.env` als `PORTFLOW_BEARER_TOKEN` (regel uit CLAUDE.md: geheimen alleen in `.env`).
  - **Eigen portfolio-id, naam, vervaltijd en "laatst ververst"** in de database (geen geheimen).
  - **Browserprofiel** in `data/browser-profile/`. Daarin staan HU- en Canvas-cookies; de map staat niet in git.
- **Privacy:** het token komt **nooit** in de browser-JavaScript, in logregels of in foutmeldingen. Het status-endpoint geeft alleen de toestand, naam en tijden terug.

## Technische eisen

- Nieuwe dependency: **playwright** (Python-pakket, circa 43 MB). Gebruikt de geïnstalleerde Google Chrome (`channel="chrome"`), anders Playwright-Chromium. Leg dit vast in de techstacktabel van architectuur.md.
- Alle Portflow-aanroepen in `dashboard/portflow_api.py`; het opvangen van het token in een eigen module (bijvoorbeeld `dashboard/portflow_login.py`) die in een **achtergrondthread** draait, met een lock zodat er maar één browser tegelijk loopt.
- De toestanden uit F12 zijn één toestandsmachine op één plek, met tests voor elke overgang. De browser wordt in tests vervangen door een nepfunctie: geen echte Portflow-aanroepen in tests. Gebruik nep-JWT's met een zelfgekozen `exp`.
- `app.js` (het eerste JavaScript) doet alleen het paneel en het live bijwerken; zonder JavaScript blijft de status zichtbaar (na herladen).
- Het status-endpoint en de POST-acties vallen onder de bestaande controle op host en herkomst ([`dashboard/__init__.py`](../../dashboard/__init__.py)).

## Open vragen

- [x] Verversmarge: 1 uur voor het verlopen; opnieuw proberen hooguit eens per 15 minuten.
- [x] Headless mislukt: terugvallen op een zichtbaar venster dat vanzelf sluit, met de instelling "Altijd zichtbaar verversen".
- [x] Starten zonder token: het inlogvenster opent meteen.
- [x] Verbinding verbreken: alleen het token; het browserprofiel blijft.
- [x] Rollen bij de naam ("Coach · Gildemeester") horen bij de spec *Eerste start*, niet hier.

## Logboek

- 2026-11-09 – spec aangemaakt
- 2026-11-09 – open vragen beantwoord; status uitgewerkt
