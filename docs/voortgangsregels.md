# Voortgangsregels

Hoe de voortgang van een student wordt bepaald en weergegeven. Dit document is de bron voor alle berekeningen en weergaven van voortgang in het dashboard. Begrippen staan in [begrippen.md](begrippen.md), de vaardigheden in [vaardigheden-openict.md](vaardigheden-openict.md).

## Wie beoordeelt wat

| Vaardigheden | Beoordeeld door |
|---|---|
| Productvaardigheden: OC, KO, JKO, KPM | Gildemeester (in het gilde) |
| Sociale vaardigheden: PL, BD, SW | Coach |
| Persoonsvormende vaardigheden: FO, PH, RE | Coach |

Een beoordeling gebeurt via een **evaluatie** per vaardigheid. Een evaluatie levert altijd een niveau op: startniveau, 1, 2, 3 of 4. Een niet-behaalde evaluatie bestaat niet; elke evaluatie telt mee.

<a id="startniveau"></a>
### Startniveau

Een evaluatie op **startniveau** betekent: de evaluatie is gedaan, maar het niveau is nog geen 1. Zo'n evaluatie wordt **wel bewaard en getoond** (als `0`), want er heeft een evaluatie plaatsgevonden:

- Ze telt mee als evaluatie voor de regel "minstens twee behaalde evaluaties".
- Voor het niveau telt het hoogste niveau. Voorbeeld: eerst startniveau, daarna niveau 2 → weergave `0/2`, hoogste niveau **2**.

<a id="welke-evaluaties-tellen"></a>
## Welke evaluaties tellen

Uit Portflow komen per vaardigheid alle *feedback items* (zie [architectuur.md](architectuur.md#portflow-api)). Een evaluatie **telt mee** en verschijnt in de cel als alle vier de voorwaarden gelden:

1. **Beoordeeld door een ander:** het is geen zelfevaluatie van de student, en er is een niveau toegekend.
2. **Bekende beoordelaar:** de beoordelaar staat in de lijst met coaches en gildemeesters in Instellingen ([gegevensmodel.md](gegevensmodel.md#gebruiker)). Dit geldt voor alle tien vaardigheden. Evaluaties van andere beoordelaars (bijvoorbeeld een ouderejaars student die evaluaties afnam) worden **volledig verborgen** en tellen niet mee.
3. **Binnen de semesterperiode:** de datum van de evaluatie valt binnen de semesterperiode uit Instellingen. Heeft de student een eigen startdatum, dan geldt die als begin. Een evaluatie zonder herkenbare datum telt mee.
4. **Een van de tien vaardigheden:** het doel in Portflow is een van de tien vaardigheden. Beroepstaken tellen **niet** mee voor het semester (zie [HBOi-beroepstaken.md](HBOi-beroepstaken.md)).

<a id="openstaand"></a>
### Openstaande evaluaties (`?`)

Heeft de student een evaluatie aangevraagd (zelfevaluatie ingediend), maar is die nog niet beoordeeld, dan staat er een `?` in de cel, na de behaalde niveaus. Voorbeeld: `1/?`. Een `?` telt **niet** mee voor "semester behaald" en niet voor de kleur van de cel; het heeft een eigen kleur ([design-system.md](design-system.md#niveaulabels)).

Geen `?` (overgenomen uit de console-app):

- als het verzoek door de beoordelaar is **geweigerd**;
- als er voor die vaardigheid al een beoordeling is **op of na** de datum van de zelfevaluatie (het verzoek is dan beantwoord);
- als er voor dezelfde vaardigheid een **nieuwer** openstaand verzoek is (alleen het nieuwste telt);
- bij een **eindassessment**: een verzoek waarin de student in één keer alle tien vaardigheden indient. Dan staan er geen tien losse `?`, maar krijgt de student één markering **"Assessment ingeleverd"**.

### Geen toegang

Is het portfolio van een gevolgde student (niet meer) met de gebruiker gedeeld, dan blijft de rij staan, grijs, met `n/b` in de cellen en de uitleg "portfolio niet gedeeld".

## Assessment

De student doet assessment door in Portflow een **assessmentportfolio** te maken. De student is ingeschreven voor een bepaald semester. De student werkt vanuit een beroepsrol, maar de eisen voor het semester (zie hieronder) zijn voor alle beroepsrollen gelijk.

<a id="toetsprogramma-eisen-per-semester"></a>
## Toetsprogramma: eisen per semester

Bron: *Tabel 1: Toetsprogramma – de eisen per semester* ([`screenshots/toetsprogramma-eisen-per-semester.webp`](../screenshots/toetsprogramma-eisen-per-semester.webp)).

| Semester | Niveau opdracht | Code | Minimum niveau toetsing (LEF) | Niveau KPM | Beheersingsniveau studenten |
|---|---|---|---|---|---|
| 1 | Taak | TICT-OV1SE1-26 | 4 van 10 op 1 | Nvt | |
| 2 | Taak | TICT-OV1SE2-26 | 8 van 10 op 1 | Minimaal KPM op 1 | hbo-i niveau T |
| 3 | Probleem | TICT-OV2SE3-26 | 4 op 2, 6 op 1 | Minimaal KPM op 1 | |
| 4 | Probleem | TICT-OV2SE4-26 | 8 op 2, 2 op 1 | Minimaal KPM op 2 | hbo-i niveau P |
| 5 | Situatie | TICT-OV3SE5-26 | 3 op 3, 7 op 2 | Minimaal KPM op 2 | |
| 6 | Situatie | TICT-OV3SE6-26 (keuze, minor) | 4 op 3, 6 op 2 | Minimaal KPM op 2 | |
| 7 | Situatie | TICT-OV4SE7-26 | 5 op 3, 5 op 2 | Minimaal KPM op 2 | |
| 8 | Situatie | TICT-AFSTUD-25 | | BOKSA | hbo-i niveau S |

Hoe de tabel te lezen is:

- **Niveau opdracht** sluit aan bij de niveautitels in LEF: taakgericht (1), probleemgericht (2), situatiegericht (3).
- **Minimum niveau toetsing** geeft per semester **hoeveel** van de tien vaardigheden op **welk** niveau moeten zijn aangetoond. De eis ligt dus niet vast per vaardigheid; de student kiest welke vaardigheden hoger uitkomen. Uitzondering: **KPM** heeft vanaf semester 2 een eigen minimum.
- "Op 2" betekent **op 2 of hoger**: een vaardigheid op niveau 3 telt ook mee voor "op 2".
- **Semester 1 en 2:** de student hoeft nog niet alle vaardigheden te evalueren. In semester 1 zijn dat er **4**, in semester 2 **8**. Vanaf semester 3 worden alle 10 vaardigheden geëvalueerd.
- De eisen gelden voor **iedereen, ongeacht de beroepsrol**.
- **Semester 8** (afstuderen) gebruikt een andere methodiek, **BOKSA**, met 5 vermogens in plaats van 10 vaardigheden. Valt voorlopig buiten deze regels; wordt later uitgewerkt.
- Niveau 4 komt in dit toetsprogramma niet voor; het hoogste gevraagde niveau is 3.

## Semester behaald

De opleiding telt **8 semesters**. Een student heeft een semester behaald als geldt:

> Voor **alle te evalueren vaardigheden** (semester 1: 4, semester 2: 8, vanaf semester 3: alle 10) zijn **minstens twee evaluaties behaald**, waarvan **minstens één op het benodigde eindniveau**.

Dit geldt ook in semester 1 en 2: elk van de 4 (of 8) geëvalueerde vaardigheden heeft minstens twee behaalde evaluaties.

Samen met het toetsprogramma (semester 1 t/m 7):

1. Bepaal per vaardigheid of er **minstens twee behaalde evaluaties** zijn. Alleen die vaardigheden tellen mee.
2. Bepaal per vaardigheid het **hoogste behaalde niveau**. Alleen het hoogste niveau telt.
3. Controleer de verdeling uit het toetsprogramma, waarbij een hoger niveau ook meetelt voor een lager niveau. Voorbeelden:
   - Semester 2 ("8 van 10 op 1"): minstens 8 vaardigheden met een hoogste niveau van 1 of hoger.
   - Semester 4 ("8 op 2, 2 op 1"): minstens 8 vaardigheden met hoogste niveau 2 of hoger, en de overige 2 met hoogste niveau 1 of hoger.
4. Controleer het minimum voor **KPM** (hoogste niveau van KPM).

### Voorbeeld

Een student in semester 3 (eis: 4 op 2, 6 op 1, KPM minimaal 1):

| | OC | KO | JKO | KPM | PL | BD | SW | FO | PH | RE |
|---|---|---|---|---|---|---|---|---|---|---|
| Weergave | `1/2` | `2/2` | `1/1` | `1/2` | `1/1` | `2/1` | `1/1` | `1/1` | `1/1` | `1/1` |
| Hoogste | 2 | 2 | 1 | 2 | 1 | 2 | 1 | 1 | 1 | 1 |

Vier vaardigheden op 2, zes op 1, KPM op 2: **behaald**.

## Weergave per vaardigheid

In de voortgangstabel (één rij per student, één kolom per vaardigheid OC … RE) staan in elke cel **alle behaalde niveaus** van die vaardigheid, **chronologisch** (eerst behaald staat links), gescheiden door `/`:

| Situatie | Weergave | Voorbeeld |
|---|---|---|
| Nog geen evaluatie behaald, semester 3 of hoger | `-/-` | |
| Nog geen evaluatie behaald, semester 1 of 2 | grijze cel | in deze semesters hoeft niet elke vaardigheid geëvalueerd te worden |
| Eén evaluatie behaald | het niveau | `0` (startniveau), `1`, `2` of `3` |
| Twee evaluaties behaald | beide niveaus | eerst niveau 1, daarna niveau 2 voor Samenwerken → `1/2`; andersom → `2/1`; eerst startniveau, daarna 1 → `0/1` |
| Drie evaluaties (uitzondering) | alle drie | `1/1/2` |
| Vier evaluaties (hoge uitzondering) | alle vier | `1/1/2/2` |

- Het startniveau wordt weergegeven als `0`.
- Een openstaande evaluatie komt achteraan als `?`, bijvoorbeeld `1/?` (zie [Openstaande evaluaties](#openstaand)).
- De **kleur** van de cel hangt af van het aantal evaluaties (0, 1, 2 of meer), niet van het niveau. De kleuren staan in [design-system.md](design-system.md#niveaulabels).
- Meer dan vier evaluaties per vaardigheid komt niet voor. Mocht het toch gebeuren, dan worden ze allemaal getoond en breekt de tabel niet.

<a id="signalen"></a>
## Signalen: lege vaardigheden

Overgenomen uit de console-app. Alleen voor studenten in **semester 3 en hoger** (in semester 1 en 2 blijven lege cellen grijs). Per student, kijkend naar vaardigheden zonder behaalde evaluatie:

Doel: de coach ziet snel welke studenten aangespoord moeten worden. Een signaal geldt voor de student als geheel en staat daarom als **label bij de naam**, niet in de cellen. De cellen houden hun gewone kleur.

| Situatie | Signaal |
|---|---|
| Alle vier productvaardigheden (OC, KO, JKO, KPM) leeg | rood label **"Product nog leeg"** |
| Alle zes sociale en persoonsvormende vaardigheden (PL … RE) leeg | oranje label **"Coach nog leeg"** |
| Vier of vijf van die zes leeg | geel label **"Coach nog leeg"** |

Een `?` telt niet als gevuld. Het filter **"Aan te sporen"** toont alleen studenten met minstens één signaal.

## Open vragen

- [x] **Verdeling lezen:** een vaardigheid op niveau 3 telt mee voor "op 2".
- [x] **Welke evaluatie telt:** het hoogste behaalde niveau.
- [x] **Semester 1 en 2:** alleen 4 respectievelijk 8 vaardigheden worden geëvalueerd.
- [x] **Beroepsrol:** de eisen gelden voor iedereen, ongeacht de beroepsrol.
- [x] **Semester 1 en 2, twee evaluaties:** ja, ook dan minstens twee behaalde evaluaties per geëvalueerde vaardigheid.
- [x] **Semester 1 en 2, weergave:** grijs of leeg in plaats van `-/-`.
- [x] **Volgorde:** chronologisch.
- [x] **Meer dan twee evaluaties:** mogelijk; alle tonen. Drie is een uitzondering, vier een hoge uitzondering, meer komt niet voor.
- [ ] **Semester 8 / BOKSA:** 5 vermogens in plaats van 10 vaardigheden. Komt later.
- [x] **Grijs of leeg:** grijs.
- [x] **Niet behaald:** bestaat niet; een evaluatie levert altijd een niveau op.
- [x] **Startniveau:** evaluatie gedaan, niveau nog geen 1. Wordt bewaard, telt mee als evaluatie en wordt weergegeven als `0` (bijvoorbeeld `0/2`, hoogste niveau 2).
- [x] **Semester van de student:** komt niet uit Portflow, maar wordt in het dashboard bijgehouden (zie [gegevensmodel.md](gegevensmodel.md)).
- [x] **Bron evaluaties:** ja; per vaardigheid via de feedback items in Portflow (vaardigheid, niveau, datum, beoordelaar). Zie [architectuur.md](architectuur.md#portflow-api).
- [x] **Semesterregel uit de console-app** (met beroepstaken, en voor semester 3 "2 op 2"): vervalt. Alleen het toetsprogramma hierboven geldt.
- [x] **Periode:** alleen evaluaties binnen de semesterperiode tellen.
- [x] **Wie telt als beoordelaar:** alleen namen uit de lijst met coaches en gildemeesters; andere worden verborgen.
- [x] **Signalen in semester 1 en 2:** niet; alleen vanaf semester 3.
- [x] **Signalen en celkleur:** signalen zijn labels bij de naam; de celkleur blijft het aantal evaluaties tonen.
