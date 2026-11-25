# Design system

Alle schermen volgen deze afspraken, zodat het dashboard één geheel vormt.

## Visuele richting

De ontwerpen in [`screenshots/`](../screenshots/) zijn gemaakt met Figma Make en geven de visuele richting aan. De naam "Kompas" in die ontwerpen is een verzonnen werktitel; de app heet vermoedelijk **Portflow coach dashboard** (zie [begrippen](begrippen.md#dashboard)).

> De ontwerpen bevatten echte namen en staan daarom in `.gitignore`. Ze worden pas gecommit als ze geanonimiseerd zijn.

Waar de ontwerpen en de docs van elkaar afwijken, gelden de docs. Bekende afwijkingen staan per scherm hieronder.

### Schil (alle schermen)

- **Zijbalk** (donkergroen) met bovenaan het terminal-woordmerk `>_ portflow` / "coach dashboard" (in plaats van het Kompas-logo), het kopje "Werkruimte" en de menu-items: Overzicht, Studenten, Evaluaties (met teller), **Beheer** (een uitklapbare groep met Semesters, Gildes, Gildemeesters, Coaches, Projecten en Kolommen, in het ontwerp nog "Leerdoelen"; dicht, behalve op een pagina daarbinnen; [spec 002](../features/002-app-schil/spec.md), F17), Instellingen. De groep Beheer en Coaches, Gildemeesters en Gildes staan niet in het ontwerp ([spec 007](../features/007-coaches/spec.md), [spec 006](../features/006-gildemeesters/spec.md)). Onderaan de gebruiker met naam en rollen ("Coach · Gildemeester"); een klik opent een klein menu met de schakelaar **"Namen verbergen"** ([spec 033](../features/033-namen-verbergen/spec.md); dan staat er een paarse balk bovenaan), **"Dashboard afsluiten"** en het versienummer ([spec 020](../features/020-installatie/spec.md), I5). De hulpkaart uit het ontwerp ("Hulp nodig?", "Open handleiding") komt pas als er een handleiding is.
- **Bovenbalk** met links het kruimelpad van de pagina (zie Paginakop) en rechts de verbindingsstatus van Portflow (een statusknop met gekleurde stip: grijs, blauw, groen, oranje of rood, en een paneel met details; zie [spec 003](../features/003-portflow-verbinden/spec.md)), daarnaast de knop **"Verversen"**, even hoog en even breed als de statusknop (260 × 52 pixels; een te lange onderregel wordt afgekapt met "…", de volledige tekst staat bij hover) en met dezelfde opbouw: "Verversen" met daaronder "Bijgewerkt om …" of de voortgang van het ophalen ([spec 005](../features/005-gegevens-ophalen/spec.md)), en de avatar van de gebruiker. Het belletje uit het ontwerp komt pas als er meldingen zijn.
- **Paginakop:** **afwijking** van de ontwerpen (kopje, grote titel en uitleg boven de inhoud): de kop staat als kruimelpad links in de bovenbalk, bijvoorbeeld "Beheer › Studenten › Student bewerken"; pagina's buiten de menugroep Beheer tonen alleen hun titel. Er is geen uitlegzin. Het hele pad heeft één lettergrootte (22 px); de ouders ("Beheer", een link terug) en de scheidingstekens zijn gedempt grijs, de huidige pagina is donker en halfvet. De primaire knop (bijvoorbeeld "+ Nieuw project") staat rechts in de werkbalk boven de tabel, of rechtsboven de inhoud als er geen werkbalk is. Zo blijft er zoveel mogelijk ruimte voor de tabellen ([spec 002](../features/002-app-schil/spec.md), F8).

<a id="overzicht"></a>
### Overzicht ([`kompas-dashboard-ontwerp.png`](../screenshots/kompas-dashboard-ontwerp.png))

- Kop met datum, begroeting ("Goedemorgen, …") en subtitel "Dit vraagt vandaag je aandacht." **Afwijking:** er is geen aparte kop en geen begroeting; de bovenbalk toont alleen "Overzicht", zonder datum, en boven de tabel staat geen subkop "Studentenoverzicht" ([spec 002](../features/002-app-schil/spec.md), F8). **Afwijking:** "Bijgewerkt om …" staat niet in deze kop, maar in de bovenbalk naast de knop "Verversen".
- **Drie signaalkaarten** met een getal, een label en "Bekijken →": evaluaties te beoordelen, studenten zonder recente update (geen activiteit in Portflow in de laatste *X* dagen; *X* instelbaar, standaard 14), actieve coachstudenten.
- **Studentenoverzicht:** tabel met student (naam, squad en semester; geen avatar, [spec 001](../features/001-studentenoverzicht/spec.md), F2), gilde (alle codes, bijvoorbeeld "FE, UX") en per vaardigheid (OC … RE) een niveaulabel. Daarboven een zoekveld (sneltoets ⌘K; **afwijking:** zoeken op naam, squad of profiel, niet op tribe), een filter en een legenda. Rijen zijn standaard gegroepeerd per squad (groepskop met gekleurde streep, naam, volledige squadnaam en aantal studenten), met "Nog in te delen" en "Zonder project" als laatste groepen. Onderaan "7 van 18 studenten". **Afwijking:** de tabel staat volledig op Overzicht, zonder "Alle studenten bekijken →"; de pagina Studenten toont de basisgegevens zonder voortgang ([spec 001](../features/001-studentenoverzicht/spec.md), F1; [spec 010](../features/010-studentenlijst/spec.md)).
  - Een rij kan het **rol-label** van de student tonen (PO, SM, 2ePO, 2eSM) en de markering **"Assessment ingeleverd"**.
  - Een student zonder toegang staat grijs, met `n/b` in de cellen.
  - **Geen signaallabels** bij de naam: de signalen uit [voortgangsregels.md](voortgangsregels.md#signalen) bepalen alleen het filter "Aan te sporen". Naast de naam staat alleen het semester ("Sem 3"), op dezelfde regel; het project staat al in de groepskop. Elke student past op één regel: ook meerdere gildes en namen in de extra kolommen lopen niet door naar een tweede regel.
  - Extra kolommen Coach, Gildemeester en Invulling, aan en uit te zetten; standaard alleen Gildemeester. De pijl naar de detailpagina komt pas met die pagina.
  - De uitgewerkte eisen staan in [spec 001](../features/001-studentenoverzicht/spec.md).
- **Weekgrafiek** (uit de console-app): een staafgrafiek met per week van de semesterperiode het aantal evaluaties, gestapeld als *behaald* (groen) en *ingediend, nog te beoordelen* (`?`, blauw). Op de pagina Evaluaties, onder een **compacte voortgangstabel** (dezelfde cellen als het studentenoverzicht, kleiner, alleen lezen, per project gescheiden door een dunne lijn; [spec 029](../features/029-tijdlijn-evaluaties/spec.md)).
  - Filter: Alle studenten die ik niet heb verborgen (standaard), Mijn coachstudenten, Studenten van wie ik gildemeester ben, per eigen gilde Alle studenten in mijn … gilde, Alle studenten van wie ik het portfolio kan zien, plus filters op semester, invulling, squad en gilde ([spec 019](../features/019-eenvoudige-start/spec.md)).
  - Verbergen: een icoon (oog met streep) aan het eind van de rij, altijd zichtbaar; een verborgen rij is gedimd met een open oog om hem weer te tonen. Het semester staat als tekst in de rij ("Sem 3"); wijzigen gaat bij Beheer › Studenten.
  - Groeperen: standaard per squad; ook te kiezen per invulling, semester of gilde.
  - **Afwijking:** het ontwerp toont één getal per cel. De cel toont alle behaalde niveaus volgens [voortgangsregels.md](voortgangsregels.md#weergave-per-vaardigheid), bijvoorbeeld `1/2`.
- **Zijpaneel "Te beoordelen"** met openstaande evaluatieverzoeken aan de gebruiker: student, titel van het verzoek (door de student gekozen, bijvoorbeeld "OC & KO 1ste evaluatie"), inleverdatum en gewenste datum ("Vandaag", "Morgen", datum), plus "Alle evaluaties bekijken →". Een klik opent het verzoek in Portflow; beoordelen gebeurt daar. **Afwijking:** een kaart "Te beoordelen" onderaan de pagina Evaluaties in plaats van een zijpaneel, met vaardigheden en wachttijd in plaats van de gewenste datum, zonder link naar Portflow; het menu-item Evaluaties toont het aantal ([spec 030](../features/030-te-beoordelen/spec.md)).

<a id="projecten"></a>
### Projecten ([`projecten-CRUD-met-studenten.png`](../screenshots/projecten-CRUD-met-studenten.png))

Beheer van squads ("Beheer de projectgroepen waarin je studenten zijn ingedeeld."). Uitgewerkt in [spec 012](../features/012-projecten/spec.md); **afwijkingen**: de kaart toont alleen de initialen en de weergavenaam, niet de naam en de opdrachtgever; "+ Nieuw project" opent een keuze tussen handmatig toevoegen en de Open-ICT-projecten; de knoppen Bewerken en Verwijderen staan onderaan de kaart, zoals op de andere beheerpagina's. Projecten hebben **geen kleur** (afwijking van het ontwerp, dat een kleurreeks gebruikte). Een samenvattingsbalk (actieve projecten, studenten, zonder project), een kaart per squad (initialen in een neutraal grijs vlak, de weergavenaam, avatars, aantal studenten, knoppen Bewerken en Verwijderen), een kaart "Project toevoegen" en een balk "Zonder project" ("Studenten blijven hier zichtbaar nadat een project is verwijderd.").

<a id="semesters"></a>
### Semesters ([`semesters-CRUD-met-studenten.png`](../screenshots/semesters-CRUD-met-studenten.png))

"Bekijk de bezetting van semester 1 tot en met 8 en verplaats studenten." Een samenvattingsbalk ("7 studenten verdeeld over 3 actieve semesters", "Iedere student is aan exact één semester gekoppeld"; **afwijking:** de beheerbalk van [spec 027](../features/027-beheerbalk/spec.md)) en acht kaarten: nummer, fase, naam, aantal studenten, avatars en "Open semester →".

- **Afwijking:** het ontwerp zet semester 7 in de afstudeerfase. Juist is: propedeuse 1–2, hoofdfase 3–7, afstudeerfase 8 (zie [begrippen](begrippen.md)).
- **Kleur per fase** (nummervlak, uit het ontwerp): propedeuse `#5B76A8` (blauw), hoofdfase `#4F6F62` (groen), afstudeerfase `#7D6BA8` (paars).
- **Afwijkingen** ([spec 009](../features/009-semesters/spec.md)): het dashboard start zonder semesters, met een knop voor de 8 Open-ICT-semesters; de kaart toont ook de eisen uit het toetsprogramma (Osiris-code, minimum niveau toetsing, niveau KPM, beheersingsniveau) en de knoppen Bewerken en Verwijderen. "Open semester →" en studenten verplaatsen komen pas met de spec *Studenten beheren*.

<a id="beroepsrollen"></a>
### Beroepsrollen ([`beroepsrollen-CRUD-met-studenten.png`](../screenshots/beroepsrollen-CRUD-met-studenten.png))

> **Vervallen (2026-11-10):** het dashboard heeft geen pagina Beroepsrollen meer; de beroepsrol is een veld van het gilde en staat op de gildekaart ([spec 018](../features/018-beroepsrol-in-gilde/spec.md)). Hieronder de oude beschrijving.

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

**Kleurschema's** ([spec 044](../features/044-kleurschema-niveaulabels/spec.md)): in Instellingen › Kleuren in de tabellen kiest de gebruiker wat de kleuren betekenen, voor alle tabellen met vaardigheden tegelijk. De legenda volgt de keuze.

| Schema | Kleuren |
|---|---|
| Geen kleuren | alle labels wit met een rand, ook een openstaande evaluatie (alleen de vette `?`) |
| Geen kleuren, alleen blauw voor ingediend | alle labels wit, een cel met een openstaande evaluatie blauw |
| Open-ICT: aantal evaluaties (standaard) | zoals hierboven: rood, geel, groen naar aantal; blauw voor openstaand |
| HCAI: peilmomenten | per peilmoment een vakje ([voortgangsregels.md](voortgangsregels.md#peilmomenten)): 1e roze `#F6D9E6`/`#8A3B62`, 2e geel `#F2EAC1`/`#837031`, 3e groen `#DAE9DD`/`#406B52`, 4e oranje `#F8DFC8`/`#8A4F1C`; nog niet geweest grijs `#ECEEEA`; openstaand blauw |

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
- Kleine koppen in hoofdletters met extra letterafstand (zoals "WERKRUIMTE" in de zijbalk en kolomkoppen; niet in het kruimelpad).

<a id="componenten"></a>
## Componenten

Herbruikbare onderdelen uit de ontwerpen:

- **Zijbalknavigatie** met tellerbadge
- **Bovenbalk** met Portflow-status en avatar
- **Statusknop + paneel**: knop met gekleurde stip, tekst en subtekst; een klik opent een paneel met details en acties (sluit met Escape of een klik ernaast)
- **Banner**: smalle balk onder de bovenbalk voor demodata (geel) of een verlopen verbinding (rood), met één actie
- **Filters inklappen** op Overzicht en Studenten: compact staat alleen het zoekveld met de knop "Filters" (met het aantal actieve filters, bijvoorbeeld "Filters · 2"); uitgeklapt de filters, de legenda, Kolommen en de knoppen ([spec 028](../features/028-filters-inklappen/spec.md))
- **Kruimelpad** in de bovenbalk ("Beheer › …" of alleen de titel); de primaire knop staat in de werkbalk
- **Beheerbalk** bovenaan elke Beheer-pagina: hoogstens drie aantallen (vet getal, kort label) in een vaste volgorde, met de primaire knop rechts; een aantal dat aandacht vraagt is oranje als het groter is dan 0. Geen uitlegzin. Niet bij een lege pagina ([spec 027](../features/027-beheerbalk/spec.md))
- **Beheerkaart**: gekleurd vlak met initialen of code, naam, subregel, avatars, aantal, Bewerken / Verwijderen
- **Toevoegkaart** met stippellijn ("Project toevoegen")
- **Signaalkaart**: icoon, getal, label, link
- **Niveaulabel**: label met de behaalde niveaus, gekleurd naar aantal evaluaties
- **Studentrij** (één regel): avatar met initialen, naam, semester, profiel, tien niveaulabels (plus eigen kolommen), pijl naar detail. Op Overzicht compact en zonder avatar (die herhaalde alleen de naam): een rij is ongeveer 34 px hoog, met 4 px ruimte boven en onder de cellen, niveaulabels van ongeveer 22 px en icoonknoppen van 24 px ([spec 001](../features/001-studentenoverzicht/spec.md), F2). De compacte tabel op Evaluaties en de studentpagina is nog dichter (geen avatar).
- **Groepskop** in een tabel: gekleurde streep, naam, aantal studenten
- **Evaluatie-item**: avatar, naam, type, inleverdatum, deadline-indicatie
- **Zoekveld** met sneltoets (⌘K)
- **Avatar-stapel**: overlappende avatars met initialen
- **Weekgrafiek**: gestapelde staven per week (behaald / ingediend)
- **Weekgrafiek van één student** ([spec 032](../features/032-studentpagina/spec.md)): per week een staaf van blokjes, één per evaluatie, met de vaardigheid en het niveau ("OC 1", "BD ?"); behaald in de kleur van de categorie (lichte tint), ingediend blauw
- **Updatebalk** ([spec 020](../features/020-installatie/spec.md), U2): een smalle balk onder de bovenbalk, zoals de demobanner, maar lichtblauw (`#E6ECF5` / `#2F4F86`): "Versie 1.3.0 is beschikbaar (je hebt 1.2.0)." met "Wat is er nieuw", "Nu bijwerken" (alleen in een installatie) en "Later". In Instellingen › Versie staat ook een knop "Nu bijwerken" die meteen controleert en een nieuwere versie aanbiedt (U6).

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
