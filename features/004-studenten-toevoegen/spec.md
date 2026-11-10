# 004 – Studenten toevoegen

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-09

> **Omvang van deze spec:** de lege-staat-trigger op Overzicht, het keuzescherm tussen de vier manieren uit [gegevensmodel.md](../../docs/gegevensmodel.md#studenten-toevoegen), en één manier volledig uitgewerkt: **uit Portflow kiezen**. De andere drie manieren (Excelbestand uploaden, namen typen of plakken, CSV/cellen plakken) en het automatisch koppelen van niet-Portflow-studenten aan een portfolio op naam volgen in latere specs (zie *Buiten scope*). Zodra die specs er zijn, krijgen ze hun eigen nummer en wordt het keuzescherm hieronder (F3) uitgebreid.
>
> **Bouwvolgorde:** deze functie wordt gebouwd **na** [spec 003 – Portflow verbinden](../003-portflow-verbinden/spec.md) (klaar) en maakt [spec 001 – Studentenoverzicht](../001-studentenoverzicht/spec.md) bouwbaar (die heeft gevolgde studenten nodig).

## Doel

Als **coach** of **gildemeester** wil ik snel beginnen met het dashboard door de portfolio's die studenten al met mij gedeeld hebben in Portflow te kiezen en te gaan volgen, zodat ik niet eerst handmatig gegevens hoef in te voeren.

Bij de eerste start zijn er 0 studenten ([gegevensmodel.md](../../docs/gegevensmodel.md#studenten-toevoegen)). Zonder gevolgde studenten kan het dashboard zijn kernfunctie (voortgang tonen) niet laten zien; deze functie is daarom de noodzakelijke eerste stap.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil: beide gebruikers zien en doorlopen dezelfde toevoegpagina.

## Betrokken begrippen

- Student en zijn velden, groep **Nog in te delen** bij een ontbrekend semester of primaire beroepsrol ([gegevensmodel.md](../../docs/gegevensmodel.md#student))
- Portfolio, delen (sharing) ([begrippen.md](../../docs/begrippen.md#portflow))
- De vier manieren van toevoegen en de automatische koppeling op naam ([gegevensmodel.md](../../docs/gegevensmodel.md#studenten-toevoegen))
- Verbindingstoestanden van Portflow ([spec 003](../003-portflow-verbinden/spec.md))

## Functionele eisen

### Lege staat en instappen (Overzicht)

- [x] **F1 – Signaleren van 0 studenten.** Zodra de gebruiker Overzicht opent en er 0 gevolgde studenten zijn, toont de pagina in plaats van het (nog lege) studentenoverzicht een duidelijke lege staat met uitleg en de knop **"Studenten toevoegen"**. Dit geldt ongeacht de Portflow-verbindingstoestand.
  - *Acceptatie:* 0 studenten in de database → Overzicht toont de lege staat en de knop; geen lege tabel.
- [x] **F2 – Permanente knop.** Zodra er 1 of meer studenten gevolgd worden, verdwijnt de lege staat van F1, maar blijft er op Overzicht én op de pagina Studenten (zodra die gebouwd is, [spec 001](../001-studentenoverzicht/spec.md)) een zichtbare knop **"+ Student toevoegen"** staan, die naar dezelfde toevoegpagina leidt. Zo blijft tussentijds nog een student toevoegen altijd mogelijk, niet alleen bij de allereerste keer.
  - *Acceptatie:* na het toevoegen van 1 student toont Overzicht geen lege staat meer, maar wel de knop "+ Student toevoegen".

### Keuzescherm

- [x] **F3 – Vier manieren.** De knop opent een eigen pagina met de vier manieren uit [gegevensmodel.md](../../docs/gegevensmodel.md#studenten-toevoegen) als keuzeopties: "Uit Portflow kiezen", "Excelbestand uploaden", "Namen typen of plakken", "CSV of Excelcellen plakken". Alleen **"Uit Portflow kiezen"** is in deze spec werkend; de andere drie tonen een uitgeschakelde kaart met het label **"Binnenkort beschikbaar"** en een korte uitleg wat de manier gaat doen.
  - Dit is een **bewuste uitzondering** op de keuze bij de schil ("geen knoppen die niets doen"): de kaarten laten zien wat er komt.
  - *Acceptatie:* de pagina toont 4 kaarten; een klik op een uitgeschakelde kaart doet niets (of toont alleen de uitleg); een klik op "Uit Portflow kiezen" opent die manier.
- [x] **F4 – Terugnavigatie.** Vanaf het keuzescherm en vanaf de lijst van "Uit Portflow kiezen" kan de gebruiker terug naar Overzicht zonder iets toe te voegen. Niets wordt opgeslagen tenzij de gebruiker expliciet bevestigt (F11).
  - *Acceptatie:* teruggaan zonder te bevestigen laat het aantal studenten ongewijzigd.

### Uit Portflow kiezen — gegevens ophalen

- [x] **F5 – Verbinden indien nodig.** Is er geen geldig token (toestand "Niet verbonden" of "Verlopen", zie [spec 003, F12](../003-portflow-verbinden/spec.md)) wanneer de gebruiker "Uit Portflow kiezen" kiest, dan start dezelfde verbindstap als in spec 003 (F1). Na een geslaagde verbinding gaat de gebruiker automatisch verder naar de lijst (F6); bij afbreken (spec 003, F4) blijft hij op het keuzescherm.
  Bij "Opnieuw inloggen nodig" is het token nog geldig; dan gaat de app gewoon door naar de lijst. Tijdens "Inloggen…" of "Verversen…" wacht de pagina tot de verbinding klaar is.
  - *Acceptatie:* niet verbonden + "Uit Portflow kiezen" → het Chrome-inlogvenster opent; na succesvol inloggen verschijnt de lijst zonder extra klik. Bij "Opnieuw inloggen nodig" verschijnt de lijst direct, zonder inlogvenster.
- [x] **F6 – Ophalen en groeperen van gedeelde portfolio's.** De app haalt `GET /shares/shared-with-me` op en pagineert door **tot een lege pagina**. Let op: dit endpoint geeft altijd hooguit 20 items per pagina, ook bij `per_page=50`; "stoppen bij een pagina korter dan gevraagd" zou dus na de eerste 20 studenten stoppen (zie [architectuur.md](../../docs/architectuur.md#portflow-api) en §3 van het API-document). en houdt alleen items over met `inviter.current_role == "student"`. Items met hetzelfde `inviter.id` (dezelfde Portflow-student, meerdere gedeelde portfolio's) worden samengevoegd tot één regel met alle bijbehorende `portfolio_id`'s.
  - *Acceptatie:* twee gedeelde items met hetzelfde `inviter.id` maar verschillende `portfolio_id` leveren één regel op in de lijst van F9; 45 gedeelde portfolio's verdeeld over pagina's van 20, 20 en 5 leveren alle 45 op.
- [x] **F7 – Foutafhandeling.** Een `401` tijdens het ophalen wordt behandeld als "niet meer verbonden": de gebruiker krijgt de melding en de keuze om opnieuw in te loggen (zoals [spec 003, F10](../003-portflow-verbinden/spec.md)). Andere fouten (time-out, serverfout) worden maximaal 3 keer opnieuw geprobeerd; lukt het dan nog niet, dan toont de pagina "Portflow is niet bereikbaar. Probeer het later opnieuw." met een knop om het opnieuw te proberen.
  - *Acceptatie:* een gesimuleerde `401` toont de herverbind-melding; een gesimuleerde aanhoudende serverfout toont de "niet bereikbaar"-melding na 3 pogingen.
- [x] **F8 – Geen gedeelde portfolio's.** Is de (gegroepeerde) lijst leeg, dan toont de pagina uitleg in plaats van een lege lijst: "Je hebt nog geen gedeelde portfolio's. Vraag je studenten om hun portfolio in Portflow met je te delen." plus een knop om het opnieuw op te halen.
  - *Acceptatie:* een lege respons van `/shares/shared-with-me` toont deze uitleg, geen lege lijst of tabel.

### Uit Portflow kiezen — selecteren en toevoegen

- [x] **F9 – Lijst met selectie.** Elke (gegroepeerde) student uit F6 staat als rij met een aankruisvakje, naam en initialenavatar (Portflow levert op dit endpoint geen profielfoto, zie [portflow-API-reverse-engineer.md](../../docs/portflow-API-reverse-engineer.md)). Een zoekveld filtert de lijst op naam terwijl je typt; **"Selecteer alles"** en **"Selecteer niets"** werken op de (eventueel gefilterde) zichtbare rijen.
  - *Acceptatie:* zoeken op een voornaam toont alleen bijpassende rijen; "Selecteer alles" na zoeken vinkt alleen de zichtbare rijen aan.
- [x] **F10 – Al gevolgde studenten.**
  - Een Portflow-gebruiker (`inviter.id`) die al aan een gevolgde student gekoppeld is, staat uitgeschakeld in de lijst met het label **"Al gevolgd"**.
  - Is er een gevolgde student **zonder** Portflow-koppeling met **dezelfde naam** (ongevoelig voor hoofdletters en extra spaties), bijvoorbeeld eerder toegevoegd via Excel of plakken, dan blijft de rij kiesbaar met het label **"Mogelijk al gevolgd (zelfde naam)"**. Kiest de gebruiker die rij, dan **koppelt** de app de bestaande student aan dit portfolio in plaats van een nieuwe student aan te maken.
  - Demostudenten tellen hierbij niet mee.
  - *Acceptatie:* een student die al eerder via deze manier is toegevoegd, verschijnt bij een volgend bezoek uitgeschakeld; een ongekoppelde student "Lisa Jansen" plus een gedeeld portfolio van "Lisa  jansen" geeft het label, en na toevoegen is er één Lisa Jansen, nu met Portflow-koppeling.
- [x] **F11 – Bevestigen en opslaan.** Een knop **"X studenten toevoegen"** (X = aantal aangevinkt, uitgeschakeld bij 0) maakt voor elke geselecteerde rij een nieuwe student aan met de naam en de Portflow-koppeling (`inviter.id`, `inviter.name`, alle samengevoegde `portfolio_id`'s uit F6). Boven de knop staat het vinkje **"Ik ben hun coach"**, standaard **aan**: dan wordt de gebruiker (de naam uit Portflow, spec 003 F2) als **coach** ingevuld, zodat de studenten meteen in "Mijn coachstudenten" staan. De **gildemeester** blijft leeg. Overige velden (semester, squad, invulling, rol in de squad, primaire en secundaire beroepsrol) blijven leeg; de student valt daarmee in de groep **Nog in te delen** totdat semester en primaire beroepsrol zijn ingevuld ([gegevensmodel.md](../../docs/gegevensmodel.md#student)).
  - *Acceptatie:* 3 aangevinkte studenten bevestigen met het vinkje aan → 3 nieuwe studenten, elk met de gebruiker als coach, zonder gildemeester, semester en primaire beroepsrol, en met de juiste Portflow-koppeling. Met het vinkje uit blijft ook de coach leeg.
- [x] **F12 – Terugkoppeling.** Na het bevestigen keert de gebruiker terug naar Overzicht met een bevestiging ("3 studenten toegevoegd. Ze staan bij Nog in te delen."; bij koppelen volgens F10 ook "1 bestaande student gekoppeld"). Zijn alle gedeelde portfolio's nu toegevoegd (de lijst van F9 is na het bevestigen leeg), dan toont een volgend bezoek aan deze manier de lege staat van F8.
  - *Acceptatie:* direct na het bevestigen toont Overzicht geen lege staat meer (F2); de bevestigingstekst noemt het juiste aantal.

### Buiten scope

- **Excelbestand uploaden, namen typen of plakken, CSV/Excelcellen plakken:** eigen specs, inclusief het automatisch koppelen op naam aan een gedeeld portfolio en het voorleggen van twijfelgevallen ([gegevensmodel.md](../../docs/gegevensmodel.md#koppelen-aan-portflow)).
- **Extra portfolio's later koppelen aan een al gevolgde student,** of een koppeling corrigeren: hoort bij een spec *Student bewerken*.
- **Studenten bewerken** (semester, squad, beroepsrol etc. invullen) na het toevoegen: eigen spec; deze functie levert alleen de naam en de Portflow-koppeling op.
- **Studenten verwijderen** of een toevoeging ongedaan maken: eigen spec.
- Een student die zijn portfolio niet meer deelt nadat hij is toegevoegd (`n/b`): hoort bij het Studentenoverzicht ([spec 001, F11](../001-studentenoverzicht/spec.md)).

## Schermen

Er is nog geen eigen ontwerp voor het keuzescherm of de portfoliolijst. **Het ontwerp voor nu is [design-system.md](../../docs/design-system.md)**: dezelfde paginakop als de andere beheerschermen (kopje, titel, uitleg, rechts de primaire knop), en de beheerkaarten zoals bij Projecten en Beroepsrollen voor de vier manieren. Een eigen schets in `design/` naast dit bestand mag later volgen en gaat dan voor. "+ Student toevoegen" (F2) is op Overzicht de primaire knop rechts in de paginakop.

| Scherm | Bestand | Opmerking |
|---|---|---|
| Lege staat Overzicht | design-system.md (kaart met uitleg en knop) | Eigen schets optioneel: `design/lege-staat.png` |
| Keuzescherm (4 manieren) | design-system.md (beheerkaarten, zoals [`screenshots/projecten-CRUD-met-studenten.png`](../../screenshots/projecten-CRUD-met-studenten.png)) | Eigen schets optioneel: `design/keuzescherm.png` |
| Lijst "Uit Portflow kiezen" | design-system.md (zoekveld, rijen met avatar) | Eigen schets optioneel: `design/portflow-lijst.png` |

Gedrag dat niet uit een afbeelding blijkt:

- Tijdens het ophalen van de gedeelde portfolio's (F6) toont de pagina een laadindicator; de lijst verschijnt pas als alle pagina's zijn opgehaald.
- De knop "X studenten toevoegen" (F11) is uitgeschakeld zolang er niets is aangevinkt en toont het actuele aantal terwijl de gebruiker vinkt.
- Een uitgeschakelde kaart (F3) en een uitgeschakelde rij (F10) zijn duidelijk grijzer dan een werkende kaart/rij, met de uitleg zichtbaar zonder hover (toegankelijkheid).

## Data

- **Bron:** Portflow, endpoint `GET /shares/shared-with-me` ([architectuur.md](../../docs/architectuur.md#portflow-api), [portflow-API-reverse-engineer.md](../../docs/portflow-API-reverse-engineer.md#42-get-sharesshared-with-me--met-mij-gedeelde-portfolios)).
- **Benodigde velden:** `portfolio_id`, `inviter.id`, `inviter.name`, `inviter.current_role` (filter op `"student"`).
- **Verversen:** alleen opgehaald op het moment dat de gebruiker deze pagina opent; geen achtergrondverversing.
- **Bewaren:** naam, Portflow-gebruikers-id en portfolio-id('s) van de nieuwe student in de eigen database ([gegevensmodel.md](../../docs/gegevensmodel.md#student)); verder niets van Portflow.
- **Privacy:** alleen namen van studenten die al met de gebruiker gedeeld zijn; geen profielfoto (niet beschikbaar op dit endpoint) en geen studentnummer (Portflow levert dat niet).

## Technische eisen

- **Database** ([`dashboard/db.py`](../../dashboard/db.py)): `students` krijgt een kolom `portflow_user_id` (nullable, voor de Portflow-koppeling); een nieuwe tabel `student_portfolios` (`student_id`, `portfolio_id`, `PRIMARY KEY (student_id, portfolio_id)`, `ON DELETE CASCADE`) legt vast dat een student meer dan één portfolio kan hebben.
- **Migratie:** `CREATE TABLE IF NOT EXISTS` past een bestaande database niet aan. Bij het starten voegt de app de ontbrekende kolom toe (`ALTER TABLE students ADD COLUMN portflow_user_id …` als die nog niet bestaat), zodat een bestaande `data/dashboard.sqlite3` blijft werken zonder gegevensverlies. Leg die aanpak vast in architectuur.md, want latere specs hebben hem ook nodig.
- **Portflow-aanroepen** blijven in [`dashboard/portflow_api.py`](../../dashboard/portflow_api.py): een functie die `/shares/shared-with-me` doorpagineert **tot een lege pagina** (zie F6) en de gefilterde, gegroepeerde lijst teruggeeft. Bij een `401` roept de app `mark_unauthorized()` van de verbinding aan (spec 003, F10).
- **Laden:** de pagina "Uit Portflow kiezen" toont eerst de laadindicator; `app.js` haalt de lijst daarna op als HTML-fragment en zet die op de plek van de indicator. Zonder JavaScript haalt de server de lijst direct op bij het laden van de pagina (trager, zonder indicator). Zoeken en "Selecteer alles/niets" (F9) werken met `app.js`; zonder JavaScript blijven de vinkjes bruikbaar.
- **Bevestiging (F12):** de app heeft geen sessies; de bevestiging gaat mee als parameter in de terugverwijzing naar Overzicht (bijvoorbeeld `?toegevoegd=3&gekoppeld=1`) en wordt alleen als getal gelezen.
- **Routes:** volg de bestaande indeling (uitbreiden van `routes.py`, of een nieuwe module als het te groot wordt, zie [architectuur.md](../../docs/architectuur.md#mappenstructuur-van-de-code)). De POST die studenten opslaat valt onder de bestaande controle op host en herkomst ([`dashboard/__init__.py`](../../dashboard/__init__.py)).
- **Tests:** de Portflow-aanroep wordt in tests vervangen door een nepfunctie (geen echte API-aanroepen), net als bij spec 003. Dek in elk geval: doorpagineren tot een lege pagina met pagina's van 20 (F6), groeperen op `inviter.id` (F6), "Al gevolgd" en "Mogelijk al gevolgd" met koppelen (F10), het aanmaken van studenten zonder semester/beroepsrol en met of zonder de gebruiker als coach (F11), en de migratie van een bestaande database zonder `portflow_user_id`.
- Testdata alleen met verzonnen namen.

## Open vragen

- [x] Ontwerp: design-system.md is voor nu het ontwerp; een eigen schets mag later volgen.
- [x] Keuzescherm: de drie uitgeschakelde kaarten blijven, als bewuste uitzondering.
- [x] Coach: standaard de gebruiker (vinkje "Ik ben hun coach", aan); gildemeester leeg.
- [x] Dubbelen: ook op naam waarschuwen, en dan koppelen in plaats van een nieuwe student.
- [x] Na toevoegen: terug naar Overzicht.
- [ ] Exacte plek van "+ Student toevoegen" op de pagina Studenten (F2) wordt definitief bepaald bij het bouwen van [spec 001](../001-studentenoverzicht/spec.md), die nu nog placeholder is.

## Logboek

- 2026-11-09 – spec aangemaakt, op basis van de keuzes met de gebruiker: omvang beperkt tot de lege-staat-trigger, het keuzescherm en de manier "Uit Portflow kiezen"; eigen pagina (geen paneel); bij 0 studenten én niet verbonden worden alle 4 manieren getoond; de permanente "+ Student toevoegen"-knop hoort ook bij deze spec.
- 2026-11-09 – review: paginering tot een lege pagina (de 20-per-pagina-quirk), migratie van de database, "Opnieuw inloggen nodig" telt als verbonden, laden en bevestiging technisch beschreven, design-system als ontwerp; keuzes: coach standaard de gebruiker, waarschuwen bij dezelfde naam en dan koppelen.
- 2026-11-09 – gebouwd: `dashboard/student_intake.py` (groeperen, koppelen op naam, toevoegen), `portflow_api.shared_with_me` (paginering tot een lege pagina, met retry), de migratie in `db.py` (kolom `portflow_user_id`, tabel `student_portfolios`), de routes en templates (keuzescherm, laadindicator met HTML-fragment via `app.js`, de lijst met zoeken/selecteren/koppelen/coach-vinkje). 85 tests slagen (`python -m unittest discover -s tests`), inclusief de migratie op een bestaande database zonder gegevensverlies. Handmatig gecontroleerd in de browser: lege staat, keuzescherm, verbinden-en-afbreken (F4, met een geannuleerde echte inlogpoging), en de volledige flow met een nep-API (laden → lijst met "Mogelijk al gevolgd" → selecteren → bevestigen → koppelen en toevoegen → bevestiging op Overzicht). Niet echt getest met een actieve Portflow-verbinding (geen testaccount beschikbaar in deze sessie); de Portflow-aanroep is overal vervangen door een nepfunctie, zoals bij spec 003.
- 2026-11-09 – de kaart "Excelbestand uploaden" (F3) is werkend geworden met [spec 013](../013-excel-importeren/spec.md); nog twee kaarten tonen "Binnenkort beschikbaar"
- 2026-11-10 – een vijfde kaart "Handmatig invoeren" is toegevoegd met [spec 017](../017-student-handmatig-toevoegen/spec.md)
