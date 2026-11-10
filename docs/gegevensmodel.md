# Gegevensmodel

Welke gegevens het dashboard bijhoudt, waar ze vandaan komen en wie ze invult. Begrippen staan in [begrippen.md](begrippen.md). Hoe de gegevens worden opgeslagen, staat in [architectuur.md](architectuur.md).

## Uitgangspunt: wie is de bron?

| Gegevens | Bron |
|---|---|
| Evaluaties (vaardigheid, niveau, datum, beoordelaar), openstaande evaluatieverzoeken, lijst met gedeelde portfolio's | **Portflow** (alleen lezen; lokaal bewaard als kopie, zie [architectuur.md](architectuur.md#verversen)) |
| Studenten, hun indeling (semester, squad, invulling, beroepsrol), coach en gildemeester | **Het dashboard zelf**: de gebruiker voegt ze toe en beheert ze |
| Squads (in de interface: projecten), beroepsrollen, gildes, eigen kolommen, coaches en gildemeesters | **Het dashboard zelf** |
| Gebruiker (naam, gildes) | **Het dashboard zelf**, ingevuld bij de eerste start |

Elke coach heeft **eigen gegevens**: er is geen gedeelde database tussen coaches.

## Gebruiker

Bij de **eerste start** vult de gebruiker in:

| Veld | Toelichting |
|---|---|
| Naam | Komt uit Portflow na het verbinden ([spec 003](../features/003-portflow-verbinden/spec.md)). Wordt vergeleken met de velden *coach* en *gildemeester* van elke student |
| Gildes | De gildes waarvan de gebruiker gildemeester is; mag leeg zijn (niet elke gebruiker is gildemeester) |

In **Instellingen** beheert de gebruiker daarnaast:

| Instelling | Toelichting |
|---|---|
| **Semesterperiode** | Begin- en einddatum van het huidige semester, bijvoorbeeld 01-09-2026 t/m 31-01-2027. Alleen evaluaties in deze periode tellen. Zolang de gebruiker niets heeft opgeslagen, geldt het lopende semester: 1 september t/m 31 januari, of 1 februari t/m 31 augustus ([spec 001](../features/001-studentenoverzicht/spec.md), F22) |
| **Drempel "zonder recente update"** | Aantal dagen, standaard 14 |
| **Portflow-koppeling** | Verbinden, opnieuw verbinden en verbreken; het Canvas-adres van de Portflow-tool; "Zichtbaar verversen" (standaard aan). Zie [spec 003](../features/003-portflow-verbinden/spec.md) |

<a id="coaches-en-gildemeesters"></a>
### Coaches en gildemeesters

De **lijst met coaches en gildemeesters** heeft twee eigen pagina's in het menu: **Coaches** en **Gildemeesters** ([spec 007](../features/007-coaches/spec.md), [spec 006](../features/006-gildemeesters/spec.md)).

| Veld | Toelichting |
|---|---|
| Voornaam, achternaam | Een tussenvoegsel hoort bij de achternaam. Voornaam + spatie + achternaam is de volledige naam, precies zoals in Portflow, want de lijst bepaalt welke beoordelaars meetellen. Tabellen tonen standaard de voornaam ([spec 006](../features/006-gildemeesters/spec.md), F20–F21) |
| Rollen | Coach, gildemeester of beide. Een persoon staat één keer opgeslagen; verwijderen op een van de twee pagina's haalt alleen die rol weg |
| Gildes | Alleen bij een gildemeester: nul of meer gildes ([Gilde](#gilde)) |

- Alleen personen met de rol coach zijn te kiezen in het veld *coach* van een student; alleen gildemeesters in het veld *gildemeester*.
- Evaluaties van beoordelaars die op geen van beide pagina's staan, worden verborgen ([voortgangsregels.md](voortgangsregels.md#welke-evaluaties-tellen)).
- De naam van de gebruiker staat automatisch op **Coaches**, niet op Gildemeesters. Verwijdert de gebruiker zichzelf, dan wordt hij niet opnieuw toegevoegd.
- De gildes van een gildemeester staan los van de **gildes van de gebruiker** hierboven; die stelt de gebruiker apart in.

Daarmee bepaalt de app de filters:

- **Mijn coachstudenten:** studenten bij wie het veld *coach* gelijk is aan de naam van de gebruiker.
- **Mijn gildestudenten:** studenten bij wie de gebruiker gildemeester is bij één van hun gildes ([spec 016](../features/016-gildes-van-een-student/spec.md)). (De eigen gildes van de gebruiker komen met de spec *Eerste start*.)
- **Alle gevolgde studenten:** alle studenten in het dashboard.

Nieuwe studenten krijgen **niet** automatisch de naam van de gebruiker als coach of gildemeester. **Uitzondering:** bij "Uit Portflow kiezen" staat het vinkje "Ik ben hun coach" standaard aan ([spec 004](../features/004-studenten-toevoegen/spec.md), F11). Voor de andere manieren bepaalt hun eigen spec dit.

## Student

| Veld | Verplicht | Toelichting |
|---|---|---|
| Naam | ja | |
| Studentnummer | nee | Het **OV-nummer** (onderwijsovereenkomstnummer) |
| Semester | ja, maar mag tijdelijk ontbreken | Precies één semester (1–8) per student |
| Squad | nee | In de interface "project"; zonder squad valt de student onder "Zonder project" |
| Invulling | nee | Open projecten, Open innovatieproject, Stage, Minor of Afstuderen. In keuzelijsten en filters met uitleg: "Open Projecten (jaar 2)", "Open Innovatieproject (semester 5, 6 of 7)", "Stage (semester 5, 6 of 7)", "Minor (semester 6)", "Afstuderen (semester 8)" |
| Rol in de squad | nee | PO, SM, 2ePO of 2eSM (product owner, scrum master, tweede PO, tweede SM) |
| Startdatum | nee | Eigen begin van de semesterperiode voor deze student (bijvoorbeeld bij een latere instroom); anders geldt het begin uit Instellingen |
| Gildes | ja, maar mag tijdelijk ontbreken | Nul of meer beroepsrollen (en daarmee gildes), elk met een eigen **gildemeester** (keuze uit de gildemeesters, niet verplicht); geen volgorde of "primair" ([spec 016](../features/016-gildes-van-een-student/spec.md)) |
| Coach | nee | Keuze uit de beheerde lijst met coaches en gildemeesters |
| Portflow-koppeling | nee | De Portflow-gebruiker (id en naam) en zijn portfolio-id's; een student kan meer dan één portfolio hebben. Zonder koppeling komen er geen evaluaties binnen |
| Waarden eigen kolommen | nee | Per eigen kolom een percentage of tekst, ingevuld door de gebruiker in de tabel |
| Notities | nee | Vrije tekst, te zien en te bewerken bij Student bewerken; de Excel-import zet onbekende kolommen hierin als regels "Kolomnaam: waarde" ([spec 013](../features/013-excel-importeren/spec.md)) |

- Een tribe (bijvoorbeeld "Tribe Peter/David") wordt **niet** bijgehouden.
- Een student blijft bestaan als zijn squad wordt verwijderd; hij komt dan onder "Zonder project".
- Een student zonder semester of zonder gilde (bijvoorbeeld na toevoegen op naam, of nadat zijn laatste beroepsrol is verwijderd) komt in de groep **Nog in te delen**, tot de gegevens zijn ingevuld.

## Studenten toevoegen

Bij de eerste start zijn er **0 studenten**. De gebruiker kan studenten op vijf manieren toevoegen (de vijfde, **handmatig invoeren** van één student met een formulier, staat in [spec 017](../features/017-student-handmatig-toevoegen/spec.md)):

1. **Uit Portflow kiezen:** inloggen bij Portflow, en in de lijst met alle studentportfolio's die met de gebruiker **gedeeld** zijn de studenten aanvinken die de gebruiker wil volgen.
2. **Excelbestand uploaden** ([spec 013](../features/013-excel-importeren/spec.md)): de app leest het bestand (.xlsx), herkent de kolommen op naam (in elke volgorde; kolomkoppen ongevoelig voor hoofdletters, spaties, `-` en `_`; de kopregel hoeft niet op rij 1 te staan), vraagt de gebruiker om kolommen te koppelen die hij niet herkent, en toont een voorbeeld: nieuwe studenten om aan te vinken, met "selecteer alles" en "selecteer niets", en bestaande studenten die worden aangevuld. Onbekende kolommen komen als notitie bij de student. De console-app kende deze drie bestandsvormen:

   | Bestand | Kolommen | Bijzonderheden |
   |---|---|---|
   | Studentenlijst | Nummer, Naam, Email, Semester, Project, Coach, Gilde voorkeur | *Project* levert de squad (bijvoorbeeld "(08) Commerciële economie - …"); *Gilde voorkeur* kan meerdere gildes bevatten, gescheiden door `/` |
   | Aanwezigheidsbestand gilde | Student, Coach, Semester, Gildemeester | Gilde soms af te leiden uit kolommen als *Frontend* en *UX-UI* |
   | Coachstudenten (één coach) | Nummer, Naam, Project, Gilde, Sem | Geen kolom coach; de app vraagt welke coach |

3. **Namen typen of plakken:** een tekstveld met één studentnaam per regel.
4. **CSV of Excel-cellen plakken:** een tekstveld waarin de gebruiker CSV of uit Excel gekopieerde cellen plakt. De app zoekt naar bruikbare velden: naam, studentnummer, semester, squad (projectgroep), invulling, gilde, coach en gildemeester.

### Koppelen aan Portflow

Kiest de gebruiker bij manier 1 een portfolio van iemand die al als ongekoppelde student met dezelfde naam bestaat, dan koppelt de app die bestaande student in plaats van een nieuwe aan te maken ([spec 004](../features/004-studenten-toevoegen/spec.md), F10).

Studenten die niet via Portflow zijn toegevoegd (manier 2 tot en met 4), koppelt de app **automatisch** aan een portfolio uit de lijst met gedeelde portfolio's: **op naam** (ongevoelig voor hoofdletters, extra spaties en accenten), als er precies één gedeelde student met die naam is. Dat gebeurt bij elke Verversen-ronde en direct na een Excel-import. Portflow levert voor zover bekend geen studentnummer. Studenten die niet gekoppeld kunnen worden, meldt de Verversen-knop; de gebruiker koppelt ze zelf bij Student bewerken ([spec 015](../features/015-koppelen-aan-portflow/spec.md)).

## Squad (project)

| Veld | Toelichting |
|---|---|
| Nummer | Niet verplicht; twee cijfers, uniek, bijvoorbeeld "02" |
| Naam | Verplicht, bijvoorbeeld "Gamified Learning" |
| Opdrachtgever | Niet verplicht, bijvoorbeeld "Condor Arnhem OT" |
| Weergavenaam | Vrij veld, bijvoorbeeld "Condor - Gamified learning (02)": de ingekorte opdrachtgever en projectnaam met het nummer tussen haakjes. Wordt in de overzichten getoond in plaats van de projectnaam ([spec 012](../features/012-projecten/spec.md), F10–F12) |

- Een project heeft geen kleur; de **initialen** volgen uit de naam.
- De **volledige naam** is nummer en naam samen, bijvoorbeeld "02 Gamified Learning"; zonder nummer alleen de naam.
- Het dashboard start **zonder projecten**. De Open-ICT-projecten van september 2026 ([openict-projecten.md](openict-projecten.md)) zijn met één knop toe te voegen. De gebruiker kan projecten toevoegen, bewerken en verwijderen ([spec 012](../features/012-projecten/spec.md)).

## Beroepsrol

Het dashboard start **zonder beroepsrollen**. De negen beroepsrollen van Open-ICT uit [beroepsrollen.md](beroepsrollen.md) zijn met één knop toe te voegen. De gebruiker kan rollen toevoegen, bewerken en verwijderen ([spec 008](../features/008-beroepsrollen/spec.md)). Velden: code (2 of 3 letters, uniek), naam, korte beschrijving (niet verplicht), kleur.

Wordt een rol verwijderd, dan verdwijnt dat gilde bij alle studenten; wie daarna geen gilde meer heeft, komt bij **Nog in te delen**. Het gilde van de rol wordt ook verwijderd.

<a id="semester"></a>
## Semester

De semesters van de opleiding, met de eisen uit het toetsprogramma als vrije tekst ([spec 009](../features/009-semesters/spec.md)):

| Veld | Toelichting |
|---|---|
| Nummer | 1 tot en met 8, uniek |
| Osiris-code | Niet verplicht, bijvoorbeeld TICT-OV1SE1-26 |
| Minimum niveau toetsing (LEF) | Vrije tekst, bijvoorbeeld "4 van 10 op 1" |
| Niveau KPM | Vrije tekst, bijvoorbeeld "Minimaal KPM op 1" |
| Beheersingsniveau | Vrije tekst: Taakgericht, Probleemgericht of Situatiegericht (uit *Niveau opdracht*) |

- Het dashboard start **zonder semesters**; de 8 semesters uit het [toetsprogramma](voortgangsregels.md#toetsprogramma-eisen-per-semester) zijn met één knop toe te voegen.
- Fase en kleur volgen uit het nummer (zie [begrippen.md](begrippen.md)).
- Het semester van een student blijft een nummer. Wordt een semester verwijderd, dan komen de studenten ervan bij **Nog in te delen**; wordt het nummer gewijzigd, dan verhuizen ze mee.
- De rekenregels voor "semester behaald" staan alleen in [voortgangsregels.md](voortgangsregels.md#semester-behaald), niet in deze velden.

<a id="gilde"></a>
## Gilde

| Veld | Toelichting |
|---|---|
| Code | 2 of 3 hoofdletters, uniek, bijvoorbeeld BIT of TI |
| Naam | Bijvoorbeeld "Front-end gilde" |
| Beroepsrol | Precies één; per beroepsrol hoogstens één gilde |
| Kleur | Gekozen door de gebruiker |

- De **gildes van een student** volgen uit zijn beroepsrollen (nul of meer, elk met een eigen gildemeester) ([spec 016](../features/016-gildes-van-een-student/spec.md)).
- Het dashboard start **zonder gildes**. De negen gildes van Open-ICT ([gildes-openict.md](gildes-openict.md)) zijn met één knop toe te voegen. De gebruiker kan gildes toevoegen, bewerken en verwijderen ([spec 006](../features/006-gildemeesters/spec.md), F12–F19).
- Wordt een gilde verwijderd, dan blijven de gildemeesters gildemeester, zonder dat gilde. Wordt een beroepsrol verwijderd, dan verdwijnt ook het gilde van die rol.

## Kolommen

De kolommen van het studentenoverzicht:

- De **tien vaardigheden** (OC … RE) staan altijd vast, in de vaste volgorde. Ze zijn niet te bewerken of te verwijderen. Hun beschrijving is letterlijk de LEF-tekst ([vaardigheden-niveaus-LEF.md](vaardigheden-niveaus-LEF.md)). De waarde komt uit de evaluaties in Portflow.
- **Eigen kolommen** kan de gebruiker toevoegen, bewerken en verwijderen. Velden: code, naam, beschrijving, type (**percentage** of **vrije tekst**). De gebruiker vult de waarde per student in de tabel in.

## Open vragen

- [x] Keuzelijst coach en gildemeester: een beheerde lijst in Instellingen.
- [x] Student zonder semester of gilde: mag tijdelijk, in de groep "Nog in te delen".
- [x] De naam van de gebruiker staat automatisch in de lijst met coaches en gildemeesters.
- [x] Excelbestand: in elk geval de drie vormen uit de console-app (zie hierboven).
- [x] Wat Portflow levert: zie [architectuur.md](architectuur.md#portflow-api).
- [x] Koppelen gaat op naam; Portflow levert voor zover bekend geen studentnummer.
- [ ] Herkent de app bij manier 2 ook andere Excelbestanden, net als bij manier 4?
