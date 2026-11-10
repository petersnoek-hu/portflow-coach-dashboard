# Begrippen

Gebruik deze termen overal op dezelfde manier: in specs, code en interface. Afkortingen (OC, KO, FE, …) zijn vast en worden ook in de interface gebruikt.

## Open-ICT

| Begrip | Betekenis |
|---|---|
| **Open-ICT** | Opleiding van de Hogeschool Utrecht met praktijkgericht, agile onderwijs |
| **LEF** | Leveling-Education-Framework: het framework waarin de vaardigheden en niveaus zijn vastgelegd ([lef.hu.nl](https://lef.hu.nl)). LEF wordt gedeeld door Open-ICT, Duaal en de master HCAI |
| **Sprint** | Periode van twee weken waarin studenten aan echte ICT-producten werken |
| **Squad** | Ontwikkelteam van studenten (maximaal 7); alle studenten in een squad hebben dezelfde coach. Ook wel **projectgroep**; in de interface heet een squad **project** (bijvoorbeeld "02 Condor" of "19 Cuimed": squadnummer en naam). In de console-app heette deze kolom ten onrechte "Tribe". Zie [gegevensmodel.md](gegevensmodel.md#squad-project) |
| **Tribe** | Leergemeenschap waarin meerdere squads samenkomen, bijvoorbeeld "Tribe Peter/David". Wordt in het dashboard niet bijgehouden |
| **Rol in de squad** | Scrumrol van een student: **PO** (product owner), **SM** (scrum master), **2ePO**, **2eSM** (tweede PO of SM) |
| **Leerteam** | Team waarin studenten samen leren (genoemd in LEF, naast squad, tribe en gilde) |
| **Beroepsrol** | ICT-beroep waarin de student zich ontwikkelt. Een student heeft nul of meer beroepsrollen, en daarmee gildes, zonder volgorde of "primair" ([spec 016](../features/016-gildes-van-een-student/spec.md)). Zie [beroepsrollen.md](beroepsrollen.md) |
| **Gilde** | Groep studenten met dezelfde beroepsrol; bij elke beroepsrol hoort hoogstens één gilde, met een eigen code en naam (bijvoorbeeld FE, "Front-end gilde"). Een student kan in meer gildes zitten, elk met een eigen gildemeester ([spec 016](../features/016-gildes-van-een-student/spec.md)). Studenten worden wekelijks in hun gildebijeenkomst verwacht. In het gilde worden de vier productvaardigheden (OC, KO, JKO, KPM) beoordeeld. Zie [gegevensmodel.md](gegevensmodel.md#gilde) |
| **Coach** | Begeleider van studenten; de **primaire gebruiker** van dit dashboard. Beoordeelt de sociale en persoonsvormende vaardigheden PL, BD, SW, FO, PH en RE |
| **Gildemeester** | Beoordelaar van studenten binnen het gilde; de **secundaire gebruiker** van dit dashboard. Beoordeelt de vier productvaardigheden OC, KO, JKO en KPM. Sommige gildemeesters zijn ook coach, sommige coaches zijn ook gildemeester; het dashboard moet dus beide rollen tegelijk aankunnen |
| **Opdrachtgever** | Externe partij voor wie de squad een product maakt |
| **Open Inno / Stage / Duaal** | Onderwijsvormen die in LEF genoemd worden; de werkmethodiek kan per vorm verschillen |
| **Invulling** | Wat een student in zijn semester doet: open projecten (jaar 2), open innovatieproject (semester 5, 6 of 7), stage (semester 5, 6 of 7), minor (semester 6) of afstuderen (semester 8). Zie [gegevensmodel.md](gegevensmodel.md#student) |
| **Studentnummer** | Het **OV-nummer** (onderwijsovereenkomstnummer) van een student |
| **Coachstudent** | Student bij wie de gebruiker als coach is ingevuld |
| **Gildestudent** | Student bij wie de gebruiker als gildemeester is ingevuld, of die in een gilde zit waarvan de gebruiker gildemeester is. Zie [gegevensmodel.md](gegevensmodel.md#gebruiker) |
| **HBO-i** | Landelijk beroepsprofiel voor ICT-opleidingen waarop de vaardigheden aansluiten; beschrijft onder meer de [beroepstaken](HBOi-beroepstaken.md) |

## Beroepsrollen en gildes

De negen beroepsrollen met hun codes (UX, BIT, CS, CI, FE, BE, AI, GD, TI) staan in [beroepsrollen.md](beroepsrollen.md).

## Vaardigheden, niveaus en beroepstaken

| Begrip | Betekenis |
|---|---|
| **Vaardigheid** | Een van de tien te ontwikkelen vaardigheden van een student, in drie categorieën: product-, sociale en persoonsvormende vaardigheden. Codes en volgorde: [vaardigheden-openict.md](vaardigheden-openict.md); volledige beschrijving: [vaardigheden-niveaus-LEF.md](vaardigheden-niveaus-LEF.md) |
| **Niveau** | In LEF vastgelegd ontwikkelniveau per vaardigheid. Mogelijke waarden: **startniveau, 1, 2, 3, 4**. In de interface weergegeven als `0`, `1`, `2`, `3`, `4` (startniveau = `0`). **Startniveau** betekent: er is een evaluatie gedaan, maar het niveau is nog geen 1. Zie [voortgangsregels.md](voortgangsregels.md#startniveau) |
| **Evaluatie** | Beoordeling van één vaardigheid van een student; een evaluatie levert altijd een niveau op (een niet-behaalde evaluatie bestaat niet). Productvaardigheden door de gildemeester, sociale en persoonsvormende vaardigheden door de coach |
| **Semester** | De opleiding telt 8 semesters; elk semester vraagt een hoger eindniveau. Elke student is gekoppeld aan precies één semester. Semester 8 is afstuderen en gebruikt BOKSA |
| **Fase** | Groepering van semesters: **propedeuse** (semester 1–2), **hoofdfase** (semester 3–7), **afstudeerfase** (semester 8) |
| **BOKSA** | Methodiek voor het afstuderen (semester 8), met 5 vermogens in plaats van 10 vaardigheden. Wordt later uitgewerkt |
| **Toetsprogramma** | De eisen per semester: hoeveel vaardigheden op welk niveau moeten zijn aangetoond, plus een minimum voor KPM. Zie [voortgangsregels.md](voortgangsregels.md#toetsprogramma-eisen-per-semester) |
| **Eindniveau** | Het niveau dat in een semester moet zijn aangetoond. Ligt niet vast per vaardigheid, maar als verdeling over de tien vaardigheden (bijvoorbeeld "4 op 2, 6 op 1") |
| **Niveau opdracht** | Niveau van de opdracht per semester: taak (sem. 1–2), probleem (sem. 3–4), situatie (sem. 5–8) |
| **Beheersingsniveau (hbo-i)** | HBO-i-niveau dat de student beheerst: T na semester 2, P na semester 4, S na semester 8 |
| **Assessment** | De student maakt in Portflow een assessmentportfolio om het behaalde niveau aan te tonen |
| **Semester behaald** | Voor alle te evalueren vaardigheden (semester 1: 4, semester 2: 8, daarna 10) minstens twee evaluaties behaald, waarvan minstens één op het benodigde eindniveau; het hoogste niveau telt. Geldt voor iedereen, ongeacht beroepsrol. Details in [voortgangsregels.md](voortgangsregels.md) |
| **Essentiële waarden** | De vijf waarden die het instituut IICT meeneemt in het onderwijs: duurzame energie, toegankelijkheid en inclusie, verantwoorde hardware, privacy, en security |
| **Beroepstaak** | HBO-i-combinatie van architectuurlaag en activiteit, bijvoorbeeld `SW-RE` (Software Realiseren). Zie [HBOi-beroepstaken.md](HBOi-beroepstaken.md). Let op: `SW` en `RE` zijn ook vaardigheidscodes |

## Ontwikkeling en feedback

| Begrip | Betekenis |
|---|---|
| **Peer review** | Feedback van medestudenten |
| **Sprint review** | Feedback op het opgeleverde werk aan het eind van een sprint |
| **Coachingsgesprek** | Gesprek tussen student en coach |
| **Actiepunt** | Concrete actie die een student op korte termijn uitvoert (uit LEF, RE) |
| **Ontwikkeldoel** | Persoonlijk, uitdagend doel dat over een langere periode vaardigheden of gedrag versterkt (uit LEF, RE) |
| **Leerdoel / leerplan** | Wat een student moet leren voor een taak, en de stappen om dat te bereiken (uit LEF, JKO) |
| **User story / research story / learning story** | Werkvormen bij Open-ICT voor respectievelijk productvereisten, onderzoek en persoonlijk leren |

## Dashboard

| Begrip | Betekenis |
|---|---|
| **Portflow coach dashboard** | Vermoedelijke naam van de applicatie. "Kompas" in de ontwerpen is een verzonnen werktitel en wordt niet gebruikt |
| **Gebruiker** | Coach en/of gildemeester die het dashboard gebruikt. Elke gebruiker heeft eigen gegevens; zie [gegevensmodel.md](gegevensmodel.md#gebruiker) |
| **Project** | Interfacenaam voor een **squad** |
| **Nog in te delen** | Groep voor studenten zonder semester of zonder gilde |
| **Profiel** | Interfacenaam voor de **beroepsrol** |
| **Kolom** | Kolom van het studentenoverzicht: de tien vaste vaardigheden plus eigen kolommen (percentage of vrije tekst). Het beheerscherm heet **Kolommen**; in het ontwerp heette het nog "Leerdoelen", maar dat woord betekent in LEF iets anders (zie *Leerdoel / leerplan*) |
| **Te beoordelen** | Openstaande **evaluatieverzoeken** die aan de gebruiker gericht zijn. Titel komt van de student (bijvoorbeeld "OC & KO 1ste evaluatie"). Het dashboard toont ze; beoordelen gebeurt in Portflow |
| **`?` (openstaande evaluatie)** | In een cel: de student heeft een evaluatie aangevraagd die nog niet beoordeeld is. Zie [voortgangsregels.md](voortgangsregels.md#openstaand) |
| **Eindassessment** | Evaluatieverzoek waarin de student in één keer alle tien vaardigheden indient; getoond als "Assessment ingeleverd" |
| **`n/b`** | Niet beschikbaar: het portfolio van de student is niet (meer) met de gebruiker gedeeld |

## Portflow

| Begrip | Betekenis |
|---|---|
| **Portflow** | Portfolio-omgeving waarin studenten hun ontwikkeling vastleggen; bron van de gegevens in dit dashboard |
| **Drieam** | Leverancier van Portflow; de API draait op `portfolio.drieam.app`. Portflow wordt via Canvas (LTI) geopend |
| **Portfolio** | Het portfolio van één student in Portflow; heeft een portfolio-id. De gebruiker heeft ook een eigen portfolio-id |
| **Delen** | Een student deelt zijn portfolio met een coach of gildemeester; alleen gedeelde portfolio's zijn zichtbaar |
| **Doel (goal)** | Onderdeel van een portfolio; de tien vaardigheden zijn doelen. Beroepstaken komen voor als doel of als subcriterium onder een doel |
| **Evaluatieverzoek (review request)** | Verzoek van een student om een of meer vaardigheden te beoordelen, met een titel en toelichting. Gaat naar een beoordelaar; status: niet begonnen, in uitvoering, ingediend, beoordeeld of geweigerd |
| **Zelfevaluatie** | Het deel van een evaluatieverzoek dat de student zelf invult (rol `self`). Telt niet mee als evaluatie |
| **Feedback item** | Eén zelfevaluatie of beoordeling op een doel, met niveau, datum en beoordelaar |
| **Beoordelaar** | Wie een evaluatie geeft. Telt alleen mee als die in de lijst met coaches en gildemeesters staat ([voortgangsregels.md](voortgangsregels.md#welke-evaluaties-tellen)) |
| **Bewijsstuk (evidence)** | Bestand dat de student in een toelichting noemt ("@bestand"); te downloaden via de API |

<a id="begrippen-in-de-code"></a>
## Begrippen in de code

De code is Engelstalig, de interface Nederlands. Gebruik deze vertalingen, zodat een begrip overal hetzelfde heet. Vaardigheidscodes (OC … RE), `squad` en `tribe` blijven ongewijzigd.

| Begrip (NL) | In de code |
|---|---|
| Student | `student` |
| Coach | `coach` |
| Gildemeester | `guild_master` |
| Gilde | `guild` |
| Gebruiker | `user` |
| Beroepsrol | `professional_role` |
| Gildes van een student (beroepsrol + gildemeester) | `student_guilds` |
| Rol in de squad (PO, SM, …) | `squad_role` |
| Squad (in de interface "project") | `squad` |
| Invulling | `track` |
| Semester, fase | `semester`, `phase` |
| Semesterperiode, startdatum | `semester_period`, `start_date` |
| Vaardigheid | `skill` |
| Niveau, startniveau | `level`, `start_level` (weergave `0`) |
| Evaluatie | `evaluation` |
| Evaluatieverzoek | `review_request` |
| Zelfevaluatie | `self_evaluation` |
| Beoordelaar | `assessor` |
| Coach of gildemeester in de beheerde lijst (een persoon met rollen) | `staff` (`staff_member`) |
| Gegevens ophalen, verversen | `fetch`, `refresh` |
| Openstaande evaluatie (`?`) | `pending_evaluation` |
| Eindassessment | `full_assessment` |
| Toetsprogramma | `assessment_program` |
| Semester behaald | `semester_passed` |
| Signaal | `signal` |
| Kolom, eigen kolom | `column`, `custom_column` |
| Beroepstaak | `professional_task` |
| Portfolio, doel | `portfolio`, `goal` |
| Demodata | `demo_data` (records met `is_demo`) |

## Open vragen

- [x] **Te beoordelen:** openstaande evaluatieverzoeken aan de gebruiker, uit Portflow; beoordelen gebeurt in Portflow.
