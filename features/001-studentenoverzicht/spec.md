# 001 – Studentenoverzicht

**Status:** uitgewerkt <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-09

> **Bouwvolgorde:** deze functie wordt gebouwd **na** de specs *Portflow verbinden* en *Studenten toevoegen*, zodat ze met echte gegevens werkt.

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

- [ ] **F1 – Twee plekken, één component.** De volledige tabel staat op de pagina **Studenten**. Op **Overzicht** staat dezelfde tabel verkort, met onderaan "X van Y studenten" en "Alle studenten bekijken →", dat naar de pagina Studenten leidt.
  - *Acceptatie:* de link op Overzicht opent de pagina Studenten, met hetzelfde filter.

### Tabel

- [ ] **F2 – Rijen en kolommen.** Eén rij per gevolgde student. Kolommen in deze volgorde: Student (avatar met initialen, naam, subregel "squad · Sem N"), Profiel (primaire beroepsrol), de tien vaardigheden OC … RE, de eigen kolommen (F8), en daarna de extra kolommen (F3). Zonder pijl naar een detailpagina; die komt met de spec *Detailpagina*.
  - *Acceptatie:* gegeven 7 gevolgde studenten en het filter "Alle gevolgde studenten", dan toont de tabel 7 rijen met de kolommen in deze volgorde.
- [ ] **F3 – Extra kolommen, aan en uit te zetten.** Extra kolommen zijn Coach, Gildemeester en Invulling. Standaard staat alleen **Gildemeester** aan. De gebruiker zet kolommen aan of uit, en die keuze blijft bewaard. Eigen kolommen zijn op dezelfde manier te verbergen.
  - *Acceptatie:* bij de eerste keer zijn Coach en Invulling verborgen; na het aanzetten van Coach en het herstarten van de app is Coach nog steeds zichtbaar.
- [ ] **F4 – Kolomkoppen per categorie.** De koppen OC … KPM, PL … SW en FO … RE krijgen de LEF-categoriekleur ([design-system.md](../../docs/design-system.md#vaardigheidscategorieën-uit-lef)).
  - *Acceptatie:* de kop van KPM heeft de productkleur, die van SW de sociale kleur en die van RE de persoonsvormende kleur.
- [ ] **F5 – Rol in de squad.** Heeft een student een rol (PO, SM, 2ePO, 2eSM), dan staat die als klein label bij de naam.
  - *Acceptatie:* een student met rol SM toont het label "SM"; een student zonder rol toont geen label.

### Cellen

- [ ] **F6 – Celinhoud.** Elke vaardigheidscel toont de behaalde niveaus volgens [voortgangsregels.md](../../docs/voortgangsregels.md#weergave-per-vaardigheid). Alleen evaluaties die [meetellen](../../docs/voortgangsregels.md#welke-evaluaties-tellen) verschijnen. Openstaande evaluaties staan erachter als `?` ([openstaand](../../docs/voortgangsregels.md#openstaand)). Lange waarden worden niet afgekapt.
  - *Acceptatie (voorbeelden):*
    - evaluaties 1 en daarna 2 → `1/2`
    - startniveau en daarna 2 → `0/2`
    - 1 behaald en een nieuw verzoek ingediend → `1/?`
    - een geweigerd verzoek → geen `?`
    - semester 3, geen evaluatie → `-/-`
    - semester 2, geen evaluatie → een grijze cel zonder tekst
    - een evaluatie van een beoordelaar die niet in de lijst staat → verschijnt niet
    - een evaluatie van vóór de semesterperiode → verschijnt niet
- [ ] **F7 – Celkleur.** De kleur hangt af van het aantal behaalde evaluaties: 0, 1, of 2 en meer ([design-system.md](../../docs/design-system.md#niveaulabels)). Een `?` telt niet mee en heeft een eigen accent.
  - *Acceptatie:* `1/?` heeft de kleur van "1 evaluatie" met het `?`-accent; `1/1/2` heeft de kleur van "2 evaluaties".
- [ ] **F8 – Eigen kolommen.** Eigen kolommen ([gegevensmodel.md](../../docs/gegevensmodel.md#kolommen)) staan na RE. De gebruiker klikt op een cel en vult de waarde in. Percentage: een geheel getal van 0 tot en met 100, getoond als `75%`. Tekst: vrije tekst; lange tekst wordt in de cel ingekort en bij hover volledig getoond. De waarde wordt lokaal bewaard. Het aanmaken en beheren van eigen kolommen hoort bij de spec *Kolommen*.
  - *Acceptatie:* invullen van `75` in een percentagekolom toont `75%` en blijft na herstart bewaard; `120` wordt geweigerd met een uitleg.
- [ ] **F9 – Details bij hover.** Hover (of klik) op een vaardigheidscel toont per evaluatie het niveau, de datum en de beoordelaar; bij een `?` de titel van het verzoek en de datum van indienen.
  - *Acceptatie:* een cel `1/2` toont twee regels, elk met niveau, datum en beoordelaar, in chronologische volgorde.
- [ ] **F10 – Eindassessment.** Dient een student alle tien vaardigheden in één verzoek in, dan staan er geen tien `?`, maar bij de naam de markering "Assessment ingeleverd".
  - *Acceptatie:* een verzoek met alle tien vaardigheden levert nul `?` en één markering op.
- [ ] **F11 – Geen toegang.** Is het portfolio niet met de gebruiker gedeeld, dan is de rij grijs, tonen de cellen `n/b` en staat er de uitleg "portfolio niet gedeeld".
  - *Acceptatie:* als Portflow voor die student `404` geeft, toont de rij tien keer `n/b`.

### Signalen

- [ ] **F12 – Signaallabels.** Voor studenten in semester 3 en hoger staat bij de naam een label volgens [voortgangsregels.md](../../docs/voortgangsregels.md#signalen):
  - rood **"Product nog leeg"**;
  - oranje of geel **"Coach nog leeg"**;
  - bij hover een korte, ontwikkelingsgerichte uitleg.
  - *Acceptatie:* semester 4 met OC, KO, JKO en KPM leeg → rood label; semester 4 met 5 van de 6 coachvaardigheden leeg → geel label; semester 2 → geen labels.
- [ ] **F13 – Filter "Aan te sporen".** Toont alleen studenten met minstens één signaallabel; te combineren met de andere filters.
  - *Acceptatie:* 18 studenten, waarvan 4 met een signaal → het filter toont 4 rijen.

### Filteren, groeperen, zoeken en sorteren

- [ ] **F14 – Filter op wie.** Keuze uit Mijn coachstudenten, Mijn gildestudenten en Alle gevolgde studenten ([gegevensmodel.md](../../docs/gegevensmodel.md#gebruiker)).
  - *Acceptatie:* de gebruiker "A. Coach" heeft 3 studenten bij wie coach = "A. Coach"; "Mijn coachstudenten" toont die 3.
- [ ] **F15 – Extra filters.** Op semester, invulling, squad en beroepsrol, te combineren met F13 en F14.
  - *Acceptatie:* "Mijn coachstudenten" + semester 3 toont alleen coachstudenten in semester 3.
- [ ] **F16 – Groeperen.** Standaard per squad; ook per invulling, semester, gilde of beroepsrol. De groepskop toont een gekleurde streep, de naam, de volledige naam en het aantal studenten. "Nog in te delen" en "Zonder project" komen als laatste.
  - *Acceptatie:* een student zonder squad staat onder "Zonder project"; een student zonder semester onder "Nog in te delen".
- [ ] **F17 – Zoeken.** Zoekveld op naam, squad en profiel, met sneltoets ⌘K. Het zoeken filtert terwijl je typt.
  - *Acceptatie:* zoeken op "cond" toont alleen studenten van squad "02 Condor".
- [ ] **F18 – Sorteren.** Binnen een groep standaard op naam. Een klik op een kolomkop sorteert op die kolom; een tweede klik draait de volgorde om. Een vaardigheidskolom sorteert op aantal behaalde evaluaties en daarna op het hoogste niveau.
  - *Acceptatie:* oplopend sorteren op OC zet studenten zonder OC-evaluatie bovenaan, daarna die met één evaluatie (laagste niveau eerst).
- [ ] **F19 – Legenda en teller.** Legenda: 0 evaluaties, 1 evaluatie, 2 evaluaties, openstaand (`?`), plus de signaallabels. Onderaan "X van Y studenten".
  - *Acceptatie:* 18 gevolgde studenten, waarvan 7 zichtbaar na filteren → "7 van 18 studenten".

### Toestanden

- [ ] **F20 – Lege toestand.** Zonder gevolgde studenten: een uitleg en een knop naar Studenten toevoegen.
  - *Acceptatie:* 0 studenten → geen lege tabel, maar de uitleg en de knop.
- [ ] **F21 – Niet verbonden.** Is Portflow niet verbonden, dan toont de tabel de laatst bewaarde gegevens met de tijd ervan ([architectuur.md](../../docs/architectuur.md#verversen)).
  - *Acceptatie:* bij een verlopen token blijft de tabel gevuld en toont de bovenbalk "Niet verbonden".

### Buiten scope

- Semesterstatus (voldoet de student aan het toetsprogramma?): eigen spec
- Eigen kolommen aanmaken en beheren: spec *Kolommen*
- Studenten toevoegen, bewerken en koppelen; Portflow verbinden en verversen: eigen specs
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
- [x] Bouwvolgorde: eerst Portflow verbinden en Studenten toevoegen.
- [ ] Kleur van het `?`-accent en van de signaallabels (niet blokkerend; te kiezen tijdens het bouwen, daarna vastleggen in design-system.md).

## Logboek

- 2026-11-09 – spec aangemaakt
- 2026-11-09 – antwoorden op de open vragen verwerkt; status uitgewerkt
