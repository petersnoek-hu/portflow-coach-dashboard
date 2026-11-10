# 001 – Studentenoverzicht

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-09

> **Bouwvolgorde:** deze functie wordt gebouwd **na** [spec 003 – Portflow verbinden](../003-portflow-verbinden/spec.md) en [spec 004 – Studenten toevoegen](../004-studenten-toevoegen/spec.md), en samen met of na [spec 005 – Gegevens ophalen](../005-gegevens-ophalen/spec.md), die de evaluaties ophaalt. Zonder [spec 006 – Gildemeesters](../006-gildemeesters/spec.md) en [spec 007 – Coaches](../007-coaches/spec.md) tellen alleen de evaluaties van de gebruiker zelf mee.

## Doel

Als **coach** of **gildemeester** wil ik in één tabel zien welke niveaus mijn studenten per vaardigheid hebben laten evalueren, wat nog openstaat en wie aangespoord moet worden, zodat ik snel weet wie aandacht nodig heeft en waarop.

Dit is de kern van het dashboard en de opvolger van de tabel in de console-app (zie [`docs/portflow-console-app.py`](../../docs/portflow-console-app.py), functie `print_coach_table`).

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Iedereen ziet dezelfde tabel; het verschil zit in het filter (Mijn coachstudenten, Mijn gildestudenten). Zie [gegevensmodel.md](../../docs/gegevensmodel.md#gebruiker).

## Betrokken begrippen

- Vaardigheden OC … RE in vaste volgorde ([vaardigheden-openict.md](../../docs/vaardigheden-openict.md))
- Niveaus en celweergave, `?`, `n/b`, eindassessment en signalen ([voortgangsregels.md](../../docs/voortgangsregels.md))
- Squad (project), semester, invulling, profiel, rol in de squad, coach, gildemeester, eigen kolommen ([gegevensmodel.md](../../docs/gegevensmodel.md))

## Functionele eisen

### Plek

- [x] **F1 – Plek: Overzicht.** De voortgangstabel staat op **Overzicht**, volledig (niet ingekort), met onderaan "X van Y studenten". De pagina **Studenten** toont geen voortgang, maar de basisgegevens van de studenten ([spec 010](../010-studentenlijst/spec.md)). *(Gewijzigd 2026-11-09; eerder stond de volledige tabel op Studenten en een verkorte op Overzicht.)*
  - *Acceptatie:* Overzicht toont alle gevolgde studenten met hun voortgang; er staat geen link "Alle studenten bekijken →" meer.

### Tabel

- [x] **F2 – Rijen en kolommen.** Eén rij per gevolgde student. Kolommen in deze volgorde: Student (avatar met initialen, naam, subregel "Sem N"; het project staat al in de groepskop), Profiel (primaire beroepsrol), de tien vaardigheden OC … RE, de eigen kolommen (F8), en daarna de extra kolommen (F3). Zonder pijl naar een detailpagina; die komt met de spec *Detailpagina*.
  - *Acceptatie:* gegeven 7 gevolgde studenten en het filter "Alle gevolgde studenten", dan toont de tabel 7 rijen met de kolommen in deze volgorde.
- [x] **F3 – Extra kolommen, aan en uit te zetten.** Extra kolommen zijn Coach, Gildemeester en Invulling. Standaard staat alleen **Gildemeester** aan. De gebruiker zet kolommen aan of uit, en die keuze blijft bewaard. Eigen kolommen zijn op dezelfde manier te verbergen.
  - *Acceptatie:* bij de eerste keer zijn Coach en Invulling verborgen; na het aanzetten van Coach en het herstarten van de app is Coach nog steeds zichtbaar.
- [x] **F4 – Kolomkoppen per categorie.** De koppen OC … KPM, PL … SW en FO … RE krijgen de LEF-categoriekleur ([design-system.md](../../docs/design-system.md#vaardigheidscategorieën-uit-lef)).
  - *Acceptatie:* de kop van KPM heeft de productkleur, die van SW de sociale kleur en die van RE de persoonsvormende kleur.
- [x] **F5 – Rol in de squad.** Heeft een student een rol (PO, SM, 2ePO, 2eSM), dan staat die als klein label bij de naam.
  - *Acceptatie:* een student met rol SM toont het label "SM"; een student zonder rol toont geen label.

### Cellen

- [x] **F6 – Celinhoud.** Elke vaardigheidscel toont de behaalde niveaus volgens [voortgangsregels.md](../../docs/voortgangsregels.md#weergave-per-vaardigheid). Alleen evaluaties die [meetellen](../../docs/voortgangsregels.md#welke-evaluaties-tellen) verschijnen. Openstaande evaluaties staan erachter als `?` ([openstaand](../../docs/voortgangsregels.md#openstaand)). Lange waarden worden niet afgekapt.
  - *Acceptatie (voorbeelden):*
    - evaluaties 1 en daarna 2 → `1/2`
    - startniveau en daarna 2 → `0/2`
    - 1 behaald en een nieuw verzoek ingediend → `1/?`
    - een geweigerd verzoek → geen `?`
    - semester 3, geen evaluatie → `-/-`
    - semester 2, geen evaluatie → een grijze cel zonder tekst
    - semester onbekend (Nog in te delen), geen evaluatie → een grijze cel zonder tekst
    - een evaluatie van een beoordelaar die niet in de lijst staat → verschijnt niet
    - een evaluatie van vóór de semesterperiode → verschijnt niet
- [x] **F7 – Celkleur.** De kleur hangt af van het aantal behaalde evaluaties: 0, 1, of 2 en meer ([design-system.md](../../docs/design-system.md#niveaulabels)). **Staat er een `?` in de cel, dan krijgt de cel een blauwe achtergrond**, ongeacht het aantal evaluaties, zodat openstaande verzoeken opvallen. Voor "semester behaald" telt een `?` niet mee.
  - *Acceptatie:* `1/?` en `?` hebben de blauwe achtergrond; `1/1/2` heeft de kleur van "2 evaluaties".
- [x] **F8 – Eigen kolommen.** Eigen kolommen ([gegevensmodel.md](../../docs/gegevensmodel.md#kolommen)) staan na RE. De gebruiker klikt op een cel en vult de waarde in. Percentage: een geheel getal van 0 tot en met 100, getoond als `75%`. Tekst: vrije tekst; lange tekst wordt in de cel ingekort en bij hover volledig getoond. De waarde wordt lokaal bewaard. Het aanmaken en beheren van eigen kolommen hoort bij de spec *Kolommen*.
  - *Acceptatie:* invullen van `75` in een percentagekolom toont `75%` en blijft na herstart bewaard; `120` wordt geweigerd met een uitleg.
- [x] **F9 – Details bij hover.** Hover (of klik) op een vaardigheidscel toont per evaluatie het niveau, de datum en de beoordelaar; bij een `?` de titel van het verzoek en de datum van indienen.
  - *Acceptatie:* een cel `1/2` toont twee regels, elk met niveau, datum en beoordelaar, in chronologische volgorde.
- [x] **F10 – Eindassessment.** Dient een student alle tien vaardigheden in één verzoek in, dan staan er geen tien `?`, maar bij de naam de markering "Assessment ingeleverd".
  - *Acceptatie:* een verzoek met alle tien vaardigheden levert nul `?` en één markering op.
- [x] **F11 – Geen toegang.** Is het portfolio niet met de gebruiker gedeeld, dan is de rij grijs, tonen de cellen `n/b` en staat er de uitleg "portfolio niet gedeeld".
  - *Acceptatie:* als Portflow voor die student `404` geeft, toont de rij tien keer `n/b`.

### Signalen

- [x] **F12 – Signalen (geen labels).** Voor studenten in semester 3 en hoger bepaalt de app signalen volgens [voortgangsregels.md](../../docs/voortgangsregels.md#signalen) ("Product nog leeg", "Coach nog leeg"). Ze staan **niet** als label bij de naam (verwijderd op verzoek van de gebruiker, 2026-11-10); ze bepalen alleen het filter "Aan te sporen" (F13).
  - *Acceptatie:* semester 4 met OC, KO, JKO en KPM leeg → de student valt onder "Aan te sporen", zonder label bij de naam; semester 2 → nooit onder "Aan te sporen".
- [x] **F13 – Filter "Aan te sporen".** Toont alleen studenten met minstens één signaal; te combineren met de andere filters.
  - *Acceptatie:* 18 studenten, waarvan 4 met een signaal → het filter toont 4 rijen.

### Filteren, groeperen, zoeken en sorteren

- [x] **F14 – Filter op wie.** Keuze uit Mijn coachstudenten, Mijn gildestudenten en Alle gevolgde studenten ([gegevensmodel.md](../../docs/gegevensmodel.md#gebruiker)).
  - *Acceptatie:* de gebruiker "A. Coach" heeft 3 studenten bij wie coach = "A. Coach"; "Mijn coachstudenten" toont die 3.
- [x] **F15 – Extra filters.** Op semester, invulling, squad en beroepsrol, te combineren met F13 en F14.
  - *Acceptatie:* "Mijn coachstudenten" + semester 3 toont alleen coachstudenten in semester 3.
- [x] **F16 – Groeperen.** Standaard per squad; ook per invulling, semester, gilde of beroepsrol. De groepskop toont een gekleurde streep, de naam, de volledige naam en het aantal studenten. "Nog in te delen" en "Zonder project" komen als laatste. De keuze **"Niet groeperen"** toont alle studenten in één lijst zonder groepskoppen, gesorteerd op naam (toegevoegd 2026-11-10).
  - *Acceptatie:* een student zonder squad staat onder "Zonder project"; een student zonder semester onder "Nog in te delen". Bij "Niet groeperen" staan er geen groepskoppen en alle studenten op naam.
- [x] **F17 – Zoeken.** Zoekveld op naam, squad en profiel, met sneltoets ⌘K. Het zoeken filtert terwijl je typt.
  - *Acceptatie:* zoeken op "cond" toont alleen studenten van squad "02 Condor".
- [x] **F18 – Sorteren.** Binnen een groep standaard op naam. Een klik op een kolomkop sorteert op die kolom; een tweede klik draait de volgorde om. Een vaardigheidskolom sorteert op aantal behaalde evaluaties en daarna op het hoogste niveau.
  - *Acceptatie:* oplopend sorteren op OC zet studenten zonder OC-evaluatie bovenaan, daarna die met één evaluatie (laagste niveau eerst).
- [x] **F19 – Legenda en teller.** Legenda: 0 evaluaties, 1 evaluatie, 2 evaluaties, openstaand (`?`). Onderaan "X van Y studenten".
  - *Acceptatie:* 18 gevolgde studenten, waarvan 7 zichtbaar na filteren → "7 van 18 studenten".

- [x] **F23 – Kleuren aan- en uitzetten via de legenda.** Voor elk van de vier legenda-items (0 evaluaties, 1 evaluatie, 2 evaluaties, openstaand `?`) staat een vinkje, standaard aan. Zet de gebruiker een vinkje uit, dan krijgen de cellen van die soort een **witte achtergrond en zwarte letters**; de tekst in de cel blijft staan. Een cel met een `?` volgt het vinkje "openstaand". De keuze wordt bewaard, net als de kolomkeuze (F3). Werkt ook zonder JavaScript (met een knop "Toepassen").
  - *Acceptatie:* vinkje "0 evaluaties" uit → alle `-/-`-cellen zijn wit met zwarte tekst, de andere cellen houden hun kleur; na herladen staat het vinkje nog uit.

### Toestanden

- [x] **F20 – Lege toestand.** Zonder gevolgde studenten: dezelfde lege staat als op Overzicht, met uitleg en de knop "Studenten toevoegen" ([spec 004](../004-studenten-toevoegen/spec.md), F1 en F2).
  - *Acceptatie:* 0 studenten → geen lege tabel, maar de uitleg en de knop.
- [x] **F21 – Niet verbonden.** Is Portflow niet verbonden, dan toont de tabel de laatst bewaarde gegevens met de tijd ervan ([architectuur.md](../../docs/architectuur.md#verversen)).
  - *Acceptatie:* bij een verlopen token blijft de tabel gevuld en toont de bovenbalk "Niet verbonden".

### Semesterperiode

- [x] **F22 – Semesterperiode in Instellingen.** Instellingen krijgt een blok **Semesterperiode** met een begin- en een einddatum ([gegevensmodel.md](../../docs/gegevensmodel.md#gebruiker)). Zolang de gebruiker niets heeft opgeslagen, is het **lopende semester** vooringevuld: van 1 september tot en met 31 januari, of van 1 februari tot en met 31 augustus, afhankelijk van de datum van vandaag. Een begindatum na de einddatum wordt geweigerd met uitleg. Alleen evaluaties binnen deze periode tellen mee (F6).
  - *Acceptatie:* op 9 november 2026, zonder opgeslagen periode, toont Instellingen 1-9-2026 t/m 31-1-2027 en telt een evaluatie van 15 juni 2026 niet mee; op 10 maart 2027 is dat 1-2-2027 t/m 31-8-2027.

### Buiten scope

- Semesterstatus (voldoet de student aan het toetsprogramma?): eigen spec
- Eigen kolommen aanmaken en beheren: spec *Kolommen*
- Studenten toevoegen ([spec 004](../004-studenten-toevoegen/spec.md)), bewerken en koppelen; Portflow verbinden ([spec 003](../003-portflow-verbinden/spec.md)) en verversen: eigen specs
- Te beoordelen, signaalkaarten, weekgrafiek, detailpagina: eigen specs
- Beroepstaken, BOKSA (semester 8)

## Schermen

| Scherm | Bestand | Opmerking |
|---|---|---|
| Studentenoverzicht | [`screenshots/kompas-dashboard-ontwerp.png`](../../screenshots/kompas-dashboard-ontwerp.png), het blok "Studentenoverzicht" | Bevat echte namen (in `.gitignore`). Afwijkingen: zie [design-system.md](../../docs/design-system.md#overzicht) |
| Console-tabel (referentie) | `screenshots/portflow-console-app-1.png` | Bevat echte namen (in `.gitignore`) |

Er is nog geen ontwerp met de afwijkingen (meerdere niveaus per cel, `?`, signaallabels, extra kolommen). Het Kompas-ontwerp geldt als richting; de eisen hierboven gaan voor.

## Data

- **Bron:** de lokale kopie van Portflow-gegevens ([architectuur.md](../../docs/architectuur.md#portflow-api)), oorspronkelijk uit `GET /portfolios/{id}/goals` en `GET /portfolios/{id}/goals/{goal_id}/feedback-items`, plus de status van verzoeken (geweigerd) uit `progress-review/invitations/received`. Studentgegevens en waarden van eigen kolommen komen uit de eigen opslag ([gegevensmodel.md](../../docs/gegevensmodel.md#student)).
- **Benodigde velden:**
  - per feedback item: doel (vaardigheid), type, rol (`self` of niet), niveau, datum, beoordelaar, `review_request_id`, `review_request_scored`, titel van het verzoek;
  - per student: naam, squad, semester, startdatum, profiel, rol, coach, gildemeester, invulling, Portflow-koppeling.
- **Verversen:** zoals in architectuur.md; deze functie haalt zelf niets op.
- **Privacy:** studentnamen en voortgang, alleen lokaal voor de gebruiker zelf.

## Technische eisen

- De regels uit voortgangsregels.md (welke evaluaties tellen, celinhoud, `?`, kleur, eindassessment, signalen, sorteersleutel) staan op **één plek** in de code, los van de weergave. Ze hebben **tests** met ten minste de voorbeelden uit F6, F7, F10, F12 en F18.
- De zichtbare kolommen (F3) worden per gebruiker lokaal bewaard.
- Testdata alleen met verzonnen namen.

## Open vragen

- [x] Plek: Studenten (volledig) en Overzicht (verkort).
- [x] Semesterstatus: eigen spec.
- [x] Eigen kolommen: tonen en invullen in deze spec; beheer bij Kolommen.
- [x] Signalen: labels bij de naam plus het filter "Aan te sporen".
- [x] Hover: details per evaluatie.
- [x] Sorteren: standaard op naam; klikbare koppen; een vaardigheid sorteert op aantal, dan niveau.
- [x] Pijl: weggelaten tot er een detailpagina is.
- [x] Extra kolommen: Coach, Gildemeester, Invulling; standaard alleen Gildemeester.
- [x] Bouwvolgorde: eerst [Portflow verbinden](../003-portflow-verbinden/spec.md) en [Studenten toevoegen](../004-studenten-toevoegen/spec.md).
- [x] Semesterperiode: nu al in te stellen in Instellingen (F22), met het lopende semester vooringevuld.
- [x] "Mijn gildestudenten": de eigen gildes van de gebruiker komen uit de kandidaat-spec *Eerste start en instellingen*. Tot die er is, toont het filter alleen studenten bij wie de gebruiker als gildemeester is ingevuld.
- [x] Semester onbekend: een lege cel is grijs, zoals bij semester 1 en 2 ([voortgangsregels.md](../../docs/voortgangsregels.md#weergave-per-vaardigheid)).
- [x] Kleur van het `?`-accent en van de signaallabels: gekozen tijdens het bouwen en vastgelegd in [design-system.md](../../docs/design-system.md#niveaulabels).

## Logboek

- 2026-11-09 – spec aangemaakt
- 2026-11-09 – antwoorden op de open vragen verwerkt; status uitgewerkt
- 2026-11-09 – lege cel bij onbekend semester vastgelegd; bouwvolgorde aangevuld met specs 005–007; F22 semesterperiode toegevoegd
- 2026-11-09 – gebouwd en getest (unit tests en in de browser met echte gegevens); status klaar. Keuzes tijdens het bouwen: Overzicht toont de eerste 10 rijen; groeperen op "Gilde" gebruikt de primaire beroepsrol, op "Beroepsrol" ook de secundaire (een student kan dan in meer groepen staan); een `?` telt alleen binnen de semesterperiode; kleuren van `?`, signalen en grijs vastgelegd in design-system.md
- 2026-11-09 – F1 gewijzigd op verzoek van de gebruiker: de voortgangstabel staat volledig op Overzicht; Studenten toont de basisgegevens (spec 010)
- 2026-11-09 – F1 (gewijzigd) gebouwd en getest; status klaar
- 2026-11-10 – F7 gewijzigd op verzoek van de gebruiker: een cel met een `?` krijgt een blauwe achtergrond (eerder: de kleur van het aantal evaluaties met een blauwe rand)
- 2026-11-10 – op verzoek van de gebruiker: de signaallabels "Product nog leeg" en "Coach nog leeg" zijn weg (F12, F19; het filter "Aan te sporen" blijft), en de subregel bij de naam toont alleen nog het semester, niet het project (F2)
- 2026-11-10 – F23 toegevoegd op verzoek van de gebruiker: per legenda-item een vinkje om die kleur uit te zetten (keuze wordt bewaard)
- 2026-11-10 – F23 gebouwd en getest (unit test en in de browser); status klaar
- 2026-11-10 – F16 uitgebreid op verzoek van de gebruiker met de keuze "Niet groeperen" (geldt ook voor de studentenlijst, spec 010)
- 2026-11-10 – aangepast door [spec 016](../016-gildes-van-een-student/spec.md): de kolom Profiel heet Gilde en toont alle codes; filter, groeperen en "Mijn gildestudenten" kijken naar alle gildes; "Groeperen: Beroepsrol" vervalt
- 2026-11-10 – projecten worden getoond met hun weergavenaam ([spec 012](../012-projecten/spec.md), F12)
- 2026-11-10 – het filter Invulling toont de opties met uitleg ("Open Projecten (jaar 2)", …; [gegevensmodel.md](../../docs/gegevensmodel.md#student))
- 2026-11-10 – de extra kolommen Coach en Gildemeester tonen de voornaam; kolommen met de volledige naam zijn erbij te kiezen ([spec 006](../006-gildemeesters/spec.md), F21)
- 2026-11-10 – aangepast door [spec 018](../018-beroepsrol-in-gilde/spec.md): het filter Beroepsrol heet Gilde en toont de gildes
