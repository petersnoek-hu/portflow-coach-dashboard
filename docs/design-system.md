# Design system

Alle schermen volgen deze afspraken, zodat het dashboard één geheel vormt.

## Visuele richting

De ontwerpen in [`screenshots/`](../screenshots/) zijn gemaakt met Figma Make en geven de visuele richting aan. De naam "Kompas" in die ontwerpen is een verzonnen werktitel; de app heet vermoedelijk **Portflow coach dashboard** (zie [begrippen](begrippen.md#dashboard)).

> De ontwerpen bevatten echte namen en staan daarom in `.gitignore`. Ze worden pas gecommit als ze geanonimiseerd zijn.

Waar de ontwerpen en de docs van elkaar afwijken, gelden de docs. Bekende afwijkingen staan per scherm hieronder.

### Schil (alle schermen)

- **Zijbalk** (donkergroen) met bovenaan het terminal-woordmerk `>_ portflow` / "coach dashboard" (in plaats van het Kompas-logo), het kopje "Werkruimte" en de menu-items: Overzicht, Studenten, Evaluaties (met teller), **Beheer** (een uitklapbare groep met Semesters, Beroepsrollen, Gildes, Gildemeesters, Coaches, Projecten en Kolommen, in het ontwerp nog "Leerdoelen"; dicht, behalve op een pagina daarbinnen; [spec 002](../features/002-app-schil/spec.md), F17), Instellingen. De groep Beheer en Coaches, Gildemeesters en Gildes staan niet in het ontwerp ([spec 007](../features/007-coaches/spec.md), [spec 006](../features/006-gildemeesters/spec.md)). Onderaan de gebruiker met naam en rollen ("Coach · Gildemeester"). De hulpkaart uit het ontwerp ("Hulp nodig?", "Open handleiding") komt pas als er een handleiding is.
- **Bovenbalk** met de verbindingsstatus van Portflow (een statusknop met gekleurde stip: grijs, blauw, groen, oranje of rood, en een paneel met details; zie [spec 003](../features/003-portflow-verbinden/spec.md)), daarnaast de knop **"Verversen"**, even hoog en even breed als de statusknop (260 × 52 pixels; een te lange onderregel wordt afgekapt met "…", de volledige tekst staat bij hover) en met dezelfde opbouw: "Verversen" met daaronder "Bijgewerkt om …" of de voortgang van het ophalen ([spec 005](../features/005-gegevens-ophalen/spec.md)), en de avatar van de gebruiker. Het belletje uit het ontwerp komt pas als er meldingen zijn.
- **Paginakop:** klein kopje in hoofdletters (bijvoorbeeld "Beheer", "Studievoortgang"), titel, één zin uitleg, en rechts de primaire knop (bijvoorbeeld "+ Nieuw project").

<a id="overzicht"></a>
### Overzicht ([`kompas-dashboard-ontwerp.png`](../screenshots/kompas-dashboard-ontwerp.png))

- Kop met datum, begroeting ("Goedemorgen, …") en subtitel "Dit vraagt vandaag je aandacht." **Afwijking:** "Bijgewerkt om …" staat niet in deze kop, maar in de bovenbalk naast de knop "Verversen".
- **Drie signaalkaarten** met een getal, een label en "Bekijken →": evaluaties te beoordelen, studenten zonder recente update (geen activiteit in Portflow in de laatste *X* dagen; *X* instelbaar, standaard 14), actieve coachstudenten.
- **Studentenoverzicht:** tabel met student (avatar met initialen, naam, squad en semester), gilde (alle codes, bijvoorbeeld "FE, UX") en per vaardigheid (OC … RE) een niveaulabel. Daarboven een zoekveld (sneltoets ⌘K; **afwijking:** zoeken op naam, squad of profiel, niet op tribe), een filter en een legenda. Rijen zijn standaard gegroepeerd per squad (groepskop met gekleurde streep, naam, volledige squadnaam en aantal studenten), met "Nog in te delen" en "Zonder project" als laatste groepen. Onderaan "7 van 18 studenten". **Afwijking:** de tabel staat volledig op Overzicht, zonder "Alle studenten bekijken →"; de pagina Studenten toont de basisgegevens zonder voortgang ([spec 001](../features/001-studentenoverzicht/spec.md), F1; [spec 010](../features/010-studentenlijst/spec.md)).
  - Een rij kan het **rol-label** van de student tonen (PO, SM, 2ePO, 2eSM) en de markering **"Assessment ingeleverd"**.
  - Een student zonder toegang staat grijs, met `n/b` in de cellen.
  - **Geen signaallabels** bij de naam: de signalen uit [voortgangsregels.md](voortgangsregels.md#signalen) bepalen alleen het filter "Aan te sporen". Onder de naam staat alleen het semester ("Sem 3"); het project staat al in de groepskop.
  - Extra kolommen Coach, Gildemeester en Invulling, aan en uit te zetten; standaard alleen Gildemeester. De pijl naar de detailpagina komt pas met die pagina.
  - De uitgewerkte eisen staan in [spec 001](../features/001-studentenoverzicht/spec.md).
- **Weekgrafiek** (uit de console-app): een staafgrafiek met per week van de semesterperiode het aantal evaluaties, gestapeld als *behaald* (groen) en *ingediend, nog te beoordelen* (`?`, blauw). Plaats in het ontwerp nog bepalen.
  - Filter: Mijn coachstudenten, Mijn gildestudenten, Alle gevolgde studenten, plus filters op semester, invulling, squad en beroepsrol.
  - Groeperen: standaard per squad; ook te kiezen per invulling, semester, gilde of beroepsrol.
  - **Afwijking:** het ontwerp toont één getal per cel. De cel toont alle behaalde niveaus volgens [voortgangsregels.md](voortgangsregels.md#weergave-per-vaardigheid), bijvoorbeeld `1/2`.
- **Zijpaneel "Te beoordelen"** met openstaande evaluatieverzoeken aan de gebruiker: student, titel van het verzoek (door de student gekozen, bijvoorbeeld "OC & KO 1ste evaluatie"), inleverdatum en gewenste datum ("Vandaag", "Morgen", datum), plus "Alle evaluaties bekijken →". Een klik opent het verzoek in Portflow; beoordelen gebeurt daar.

<a id="projecten"></a>
### Projecten ([`projecten-CRUD-met-studenten.png`](../screenshots/projecten-CRUD-met-studenten.png))

Beheer van squads ("Beheer de projectgroepen waarin je studenten zijn ingedeeld."). Uitgewerkt in [spec 012](../features/012-projecten/spec.md); **afwijkingen**: de kaart toont ook de opdrachtgever; "+ Nieuw project" opent een keuze tussen handmatig toevoegen en de Open-ICT-projecten; de knoppen Bewerken en Verwijderen staan onderaan de kaart, zoals op de andere beheerpagina's. **Kleurreeks** voor projecten (uit de ontwerpen): `#7D6BA8`, `#C17661`, `#5E8C74`, `#5B76A8`, `#B58A4A`, `#A86B8A`, `#4F8FA8`, `#6B8F3F`. Een samenvattingsbalk (actieve projecten, studenten, zonder project), een kaart per squad (initialen in een gekleurd vlak, naam, volledige naam, avatars, aantal studenten, knoppen Bewerken en Verwijderen), een kaart "Project toevoegen" en een balk "Zonder project" ("Studenten blijven hier zichtbaar nadat een project is verwijderd.").

<a id="semesters"></a>
### Semesters ([`semesters-CRUD-met-studenten.png`](../screenshots/semesters-CRUD-met-studenten.png))

"Bekijk de bezetting van semester 1 tot en met 8 en verplaats studenten." Een samenvattingsbalk ("7 studenten verdeeld over 3 actieve semesters", "Iedere student is aan exact één semester gekoppeld") en acht kaarten: nummer, fase, naam, aantal studenten, avatars en "Open semester →".

- **Afwijking:** het ontwerp zet semester 7 in de afstudeerfase. Juist is: propedeuse 1–2, hoofdfase 3–7, afstudeerfase 8 (zie [begrippen](begrippen.md)).
- **Kleur per fase** (nummervlak, uit het ontwerp): propedeuse `#5B76A8` (blauw), hoofdfase `#4F6F62` (groen), afstudeerfase `#7D6BA8` (paars).
- **Afwijkingen** ([spec 009](../features/009-semesters/spec.md)): het dashboard start zonder semesters, met een knop voor de 8 Open-ICT-semesters; de kaart toont ook de eisen uit het toetsprogramma (Osiris-code, minimum niveau toetsing, niveau KPM, beheersingsniveau) en de knoppen Bewerken en Verwijderen. "Open semester →" en studenten verplaatsen komen pas met de spec *Studenten beheren*.

<a id="beroepsrollen"></a>
### Beroepsrollen ([`beroepsrollen-CRUD-met-studenten.png`](../screenshots/beroepsrollen-CRUD-met-studenten.png))

"Beheer rollen en zie direct welke studenten primair of secundair gekoppeld zijn." **Afwijking** ([spec 016](../features/016-gildes-van-een-student/spec.md)): er is geen primair of secundair meer; de kaart toont "N studenten" en de samenvattingsbalk "Een student kan een of meer gildes hebben, elk met een eigen gildemeester." Een samenvattingsbalk en een kaart per rol: code, naam, korte beschrijving, aantal primair en secundair, avatars, "Studenten beheren →", Bewerken en Verwijderen.

- **Afwijkingen** ([spec 008](../features/008-beroepsrollen/spec.md)):
  - Het ontwerp toont vier rollen met eigen namen ("BIT engineer"). Het dashboard start zonder rollen; de negen Open-ICT-rollen met de namen uit [beroepsrollen.md](beroepsrollen.md) zijn met één knop toe te voegen.
  - De knop heet "+ Beroepsrol toevoegen" (zoals op de andere beheerpagina's), niet "Nieuwe beroepsrol".
  - "Studenten beheren →" komt pas met de spec *Studenten beheren*.
  - De kaart toont ook het gilde van de rol.

### Kolommen ([`leerdoelen-CRUD.png`](../screenshots/leerdoelen-CRUD.png))

In het ontwerp heet dit scherm "Leerdoelen" ("De bouwstenen van je studentenoverzicht, op één plek beheerd."; "Elk leerdoel wordt automatisch als kolom toegevoegd aan de studentenmatrix."). Een samenvattingsbalk met het aantal kolommen per type (niveaus, percentages, vrije tekst), een zoekveld, een filter op type (Alles, Niveau, Percentage, Vrije tekst) en een kaart per kolom: code, naam, beschrijving, type, "Kolom OC in studentenoverzicht", Bewerken en Verwijderen.

- **Afwijkingen:**
  - Het scherm heet **Kolommen**.
  - De tien vaardigheden zijn vast: zonder Bewerken en Verwijderen, en met de letterlijke LEF-tekst als beschrijving in plaats van de korte teksten uit het ontwerp.
  - Eigen kolommen hebben het type percentage of vrije tekst (zie [gegevensmodel.md](gegevensmodel.md#kolommen)).

> De kleurwaarden hieronder zijn uit de screenshots gemeten en dus benaderingen. Vervang ze door de exacte waarden zodra het ontwerpbestand beschikbaar is.

## Kleuren

### Basis

| Rol | Waarde | Gebruik |
|---|---|---|
| Zijbalk | `#223B33` | achtergrond navigatie |
| Zijbalk actief | `#3B584E` | geselecteerd menu-item |
| Pagina-achtergrond | `#F5F6F2` | achter de kaarten |
| Kaart | `#FFFFFF` | kaarten en panelen |
| Melding / urgent | `#C17661` | tellerbadge, "Vandaag" |
| Icoonvlak paars | `#EDEAF6` | signaalkaart evaluaties |
| Icoonvlak oranje | `#F5EAE0` | signaalkaart zonder recente update |
| Icoonvlak groen | `#E6F0E8` | signaalkaart actieve studenten |

<a id="niveaulabels"></a>
### Niveaulabels

De **tekst** in de cel volgt [voortgangsregels.md](voortgangsregels.md#weergave-per-vaardigheid): `-/-`, `0`, `1`, `1/2`, en bij uitzondering `1/1/2` of `1/1/2/2`. De **kleur** hangt af van het **aantal behaalde evaluaties**, niet van het niveau:

| Aantal evaluaties | Legenda-kleur (gemeten) | Voorbeeld |
|---|---|---|
| 0 | `#E1BFAE` (rood/zalm) | `-/-` |
| 1 | `#ECDDA4` (geel) | `2` |
| 2 of meer | `#A7CBB1` (groen) | `1/2`, `1/1/2` |
| semester 1–2 of semester onbekend, nog niet geëvalueerd | grijs `#ECEEEA` | geen tekst |

Een cel met een openstaande evaluatie (`?`, bijvoorbeeld `1/?`) krijgt **altijd een blauwe achtergrond** `#D6E2F5` met tekst `#2F4F86` en een vet `?` in `#1F4A9A`, in plaats van de kleur voor het aantal evaluaties ([spec 001](../features/001-studentenoverzicht/spec.md), F7). Een cel zonder toegang toont `n/b` in grijze tekst (`#9AA29E`).

Het label "Assessment ingeleverd" is paars (`#EDE9F6` / `#5A4A8A`), het rol-label (PO, SM, …) blauwgrijs (`#E6ECF5` / `#3F5578`).

Achtergrond- en tekstkleur van het label zelf (gemeten in het eerste ontwerp):

| Kleurgroep | Achtergrond | Tekst |
|---|---|---|
| Rood | `#EBD5CB` | `#8E5A49` |
| Geel | `#F2EAC1` | `#837031` |
| Groen | `#DAE9DD` | `#406B52` |

- Het label groeit mee met de tekst. Het meest voorkomende geval (`1/2`) blijft compact. Een langere waarde zoals `0/1/1/2` mag de kolom breder maken of afbreken, maar wordt niet afgekapt.
- De legenda boven de tabel toont: 0 evaluaties, 1 evaluatie, 2 evaluaties en openstaand, elk met een vinkje. Een uitgezet vinkje maakt die cellen wit met zwarte letters ([spec 001](../features/001-studentenoverzicht/spec.md), F23).

### Vaardigheidscategorieën (uit LEF)

Kleuren van de tegels op [lef.hu.nl](https://lef.hu.nl) (zie [`screenshots/vaardigheden-niveaus-LEF.png`](../screenshots/vaardigheden-niveaus-LEF.png)). Worden gebruikt in de **kolomkoppen** van het studentenoverzicht: een dunne gekleurde streep of achtergrond per categorie boven OC … KPM, PL … SW en FO … RE. (Dit staat niet in het ontwerp.)

| Categorie | Vaardigheden | Kleur |
|---|---|---|
| Productvaardigheden | OC, KO, JKO, KPM | `#909DB9` (grijsblauw) |
| Sociale vaardigheden | PL, BD, SW | `#A6B392` (saliegroen) |
| Persoonsvormende vaardigheden | FO, PH, RE | `#CBA084` (terracotta) |

## Typografie

- Lettertype: **DM Sans** (vrije licentie, SIL OFL), meegeleverd in de app als `woff2`. Het lettertype van het ontwerp is onbekend; DM Sans lijkt erop. Terugval: het systeemlettertype.
- Logo: terminal-woordmerk in de monospace letter van het systeem.
- Schermbreedte: laptop en groter (vanaf ongeveer 1280 pixels).
- Iconen: eenvoudige, zelfgetekende **SVG-lijniconen** in de stijl van het ontwerp, in `dashboard/templates/_icons.html`; geen icoonbibliotheek.
- Kleine koppen in hoofdletters met extra letterafstand (zoals "WERKRUIMTE", "BEHEER" en kolomkoppen).

<a id="componenten"></a>
## Componenten

Herbruikbare onderdelen uit de ontwerpen:

- **Zijbalknavigatie** met tellerbadge
- **Bovenbalk** met Portflow-status en avatar
- **Statusknop + paneel**: knop met gekleurde stip, tekst en subtekst; een klik opent een paneel met details en acties (sluit met Escape of een klik ernaast)
- **Banner**: smalle balk onder de bovenbalk voor demodata (geel) of een verlopen verbinding (rood), met één actie
- **Paginakop** met kopje, titel, uitleg en primaire knop
- **Samenvattingsbalk** met kerngetallen bovenaan een beheerscherm
- **Beheerkaart**: gekleurd vlak met initialen of code, naam, subregel, avatars, aantal, Bewerken / Verwijderen
- **Toevoegkaart** met stippellijn ("Project toevoegen")
- **Signaalkaart**: icoon, getal, label, link
- **Niveaulabel**: label met de behaalde niveaus, gekleurd naar aantal evaluaties
- **Studentrij**: avatar met initialen, naam, subregel, profiel, tien niveaulabels (plus eigen kolommen), pijl naar detail
- **Groepskop** in een tabel: gekleurde streep, naam, aantal studenten
- **Evaluatie-item**: avatar, naam, type, inleverdatum, deadline-indicatie
- **Zoekveld** met sneltoets (⌘K)
- **Avatar-stapel**: overlappende avatars met initialen
- **Weekgrafiek**: gestapelde staven per week (behaald / ingediend)

## Taal en toon

- Interface in het Nederlands.
- Ontwikkelingsgericht formuleren ("nog te ontwikkelen"), niet beoordelend ("onvoldoende").
- Gebruik voor vaardigheden en beroepsrollen de codes en namen uit [begrippen](begrippen.md).

## Open vragen

- [x] De kleur van een label hangt af van het aantal evaluaties (0, 1, 2 of meer), niet van het niveau.
- [x] Semester 1–2, niet geëvalueerd: grijs.
- [x] Grijswaarde van een niet-geëvalueerde cel in semester 1–2: `#ECEEEA`.
- [x] Categoriekleuren van LEF: ja, in de kolomkoppen.
- [ ] Wat meldt het belletje in de bovenbalk? (Later bepalen.)
- [x] Kleur van het `?`-accent en van de signaallabels: zie [Niveaulabels](#niveaulabels).
- [ ] Waar staat de weekgrafiek: op het Overzicht of op een eigen pagina?
- [ ] De link naar een evaluatieverzoek in Portflow: welke URL opent een verzoek? Nog uitzoeken.
