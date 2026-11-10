# 013 – Studenten importeren uit Excel

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-09

> **Bouwvolgorde:** na [spec 004](../004-studenten-toevoegen/spec.md) (de kaart "Excelbestand uploaden" wordt hiermee werkend), [spec 011](../011-student-bewerken/spec.md) (studentvelden), [spec 012](../012-projecten/spec.md) (projecten), [spec 009](../009-semesters/spec.md) (semesters), [spec 008](../008-beroepsrollen/spec.md) (beroepsrollen) en [spec 007](../007-coaches/spec.md) (coaches).

## Doel

Als **coach** of **gildemeester** wil ik een Excelbestand met studenten inlezen, zodat studenten die nog niet in het dashboard staan worden aangemaakt, en studenten die er al staan worden aangevuld met wat het bestand extra weet (studentnummer, semester, project, coach, gilde, …). De import moet robuust zijn: een andere kolomvolgorde of andere kolomnamen mogen niet tot fouten leiden. Herkent de app een kolom niet, dan vraagt hij de gebruiker welke kolom bij welk veld hoort.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- Velden van een student, "Nog in te delen", manier 2 "Excelbestand uploaden" ([gegevensmodel.md](../../docs/gegevensmodel.md#studenten-toevoegen))
- Semesters, projecten, beroepsrollen (gilde = primaire beroepsrol), coaches en gildemeesters

## Aanleiding: twee voorbeeldbestanden (geanalyseerd 2026-11-09)

Alleen de structuur; de bestanden bevatten echte gegevens en horen niet in de repository.

| Bestand (werkblad) | Kolommen | Bijzonderheden |
|---|---|---|
| Studentenlijst jaar 2 (eerste werkblad) | Nummer, Naam, Project, Coach, Herkomst, Propedeuse, Vorige coach, Email, Discord, Mobiel, Osiris actief, Semester, Gilde, Eventueel 2e gilde, een open vraag over betrokkenheid in het gilde | Project als "01 - Opdrachtgever Projecttitel"; Coach als **voornaam**, soms "Stage", "Minor …" of "Studiepauze …"; Semester als "Semester 3" of "Semester 3 (her)"; Gilde als "Front-end developer (FE)", soms "#N/A" of "ja"; lege rijen; meer werkbladen (draaitabel, adreslijsten uit Osiris, formulierantwoorden, keuzelijsten) |
| Projectindeling (één werkblad) | Nummer, Naam, Email, Project, Coach, Discord | Zelfde vorm van Project en Coach |

Daarnaast kent de console-app drie vormen ([gegevensmodel.md](../../docs/gegevensmodel.md#studenten-toevoegen)). De import werkt niet met vaste vormen, maar herkent kolommen op naam (F4).

## Functionele eisen

### Bestand kiezen

- [x] **F1 – Instappen.** Op de pagina Studenten toevoegen ([spec 004](../004-studenten-toevoegen/spec.md), F3) is de kaart **"Excelbestand uploaden"** nu werkend. Die opent een pagina waar de gebruiker een **.xlsx**-bestand kiest en op "Inlezen" klikt.
  - *Acceptatie:* de kaart is niet meer uitgeschakeld en opent de uploadpagina.
- [x] **F2 – Controle van het bestand.** Alleen .xlsx (geen oud .xls, geen .csv), hooguit 10 MB. Een ander of kapot bestand geeft een duidelijke melding ("Dit is geen Excelbestand (.xlsx) dat de app kan lezen.") en de gebruiker kan een ander bestand kiezen.
  - *Acceptatie:* een .txt-bestand of een kapot .xlsx geeft de melding; er wordt niets opgeslagen.
- [x] **F3 – Werkblad.** Heeft het bestand meer werkbladen, dan kiest de app het eerste werkblad waarin hij een naamkolom herkent, en toont hij een keuzelijst met alle werkbladen (met het aantal rijen) om een ander te kiezen. Verborgen werkbladen staan erbij met "(verborgen)".
  - *Acceptatie:* bij een bestand met een draaitabel als eerste werkblad en een studentenlijst als tweede kiest de app het tweede.

### Kolommen herkennen en koppelen

- [x] **F4 – Kopregel en kolommen herkennen.** De kopregel hoeft niet op rij 1 te staan: de app zoekt in de eerste 20 rijen de rij met de meeste herkende kolomnamen. Kolomnamen worden vergeleken zonder onderscheid tussen hoofd- en kleine letters, spaties, `-`, `_` en leestekens. De **volgorde van de kolommen maakt niet uit.** Herkende namen (uitbreidbaar in de code, op één plek):

  | Veld | Herkende kolomnamen (voorbeelden) |
  |---|---|
  | Studentnummer | Nummer, Studentnummer, Studentnr, OV-nummer |
  | Naam | Naam, Student, Studentnaam, Voor- en achternaam |
  | Semester | Semester, Sem |
  | Project | Project, Projectgroep, Squad |
  | Invulling | Invulling |
  | Rol in de squad | Rol, Rol in squad, Squadrol |
  | Primaire beroepsrol | Gilde, Beroepsrol, Primaire beroepsrol, Gilde voorkeur |
  | Secundaire beroepsrollen | Eventueel 2e gilde, 2e gilde, Secundaire beroepsrol(len) |
  | Coach | Coach |
  | Gildemeester | Gildemeester |

  Elke andere kolom krijgt standaard de koppeling **Notitie** (F8). Een veld wordt hooguit aan één kolom gekoppeld (de eerste die past).
  - *Acceptatie:* hetzelfde bestand met de kolommen in een andere volgorde levert hetzelfde voorbeeld op; een kopregel op rij 3 wordt gevonden.
- [x] **F5 – Koppelen door de gebruiker.** Wordt er **geen naamkolom** herkend, dan toont de app eerst de stap **"Kolommen koppelen"**: per kolom uit het bestand de kolomnaam, drie voorbeeldwaarden en een keuzelijst met alle velden, plus "Notitie" en "Niet gebruiken". Ook als alles herkend is, kan de gebruiker vanuit het voorbeeld (F6) via **"Kolommen anders koppelen"** naar deze stap. Een veld kan maar aan één kolom gekoppeld zijn; zonder naamkolom kan de gebruiker niet verder ("Koppel een kolom aan Naam.").
  - *Acceptatie:* een bestand met de kolom "Leerling" in plaats van "Naam" toont de koppelstap; na het koppelen van "Leerling" aan Naam volgt het voorbeeld.

### Voorbeeld en importeren

- [x] **F6 – Voorbeeld.** Vóór er iets wordt opgeslagen, toont de app per rij met een naam:
  - **Nieuw**: de student staat nog niet in het dashboard; met een aankruisvakje, "Selecteer alles" en "Selecteer niets". Het vakje staat **alleen aan als de naam van de gebruiker in een cel van die rij staat**: de volledige naam of de voornaam (bijvoorbeeld "Peter" in de kolom Coach), als hele celwaarde en zonder onderscheid tussen hoofd- en kleine letters, extra spaties en accenten. Bij zo'n rij staat het label "Jouw naam in kolom Coach". De gebruiker kan andere studenten aanvinken of het vinkje weghalen. Is de naam van de gebruiker nog niet bekend (nooit verbonden met Portflow), dan staan alle vakjes aan;
  - **Bestaand**: de student staat er al. Lege velden worden aangevuld (getoond als "+ semester 3"). Velden met een **andere** waarde staan er als "project: 02 Gamified Learning → 05 AI Cluster team", elk met een aankruisvakje **"overnemen"** (standaard uit);
  - **Ongewijzigd**: de student staat er al en het bestand voegt niets toe;
  - **Overgeslagen**: lege rijen, rijen zonder naam en een tweede rij voor dezelfde student (met de reden).
  Per rij staan de meldingen van F7 erbij. Bovenaan staat de telling ("12 nieuw, 30 aanvullen, 50 ongewijzigd, 3 overgeslagen") en een zoekveld.
  - *Acceptatie:* een bestand met 2 nieuwe en 1 bestaande student met een ander project toont 2 rijen "Nieuw" en 1 rij "Bestaand" met "project: … → …" en een uitgevinkt "overnemen". Is de gebruiker "Peter Snoek", dan is van de nieuwe rijen alleen die met "Peter" (of "Peter Snoek") in een cel aangevinkt; een cel "Pieter" of een zin waarin "Peter" voorkomt telt niet.
- [x] **F7 – Waarden omzetten.** Per veld:
  - **Studentnummer**: als tekst; een getal uit Excel zonder ".0".
  - **Semester**: het eerste getal van 1 tot en met 8 in de tekst ("Semester 3 (her)" → 3). Het semester moet op de pagina Semesters bestaan ([spec 009](../009-semesters/spec.md)); anders leeg met de melding "Semester 3 bestaat nog niet".
  - **Project**: het nummer vooraan ("01 - …" → project 01). Een onbekend nummer blijft leeg met de melding "Project 21 bestaat niet".
  - **Primaire en secundaire beroepsrol**: de code tussen haakjes ("Front-end developer (FE)" → FE), anders een code of naam die precies overeenkomt. Anders leeg met een melding (bijvoorbeeld bij "ja").
  - **Coach en gildemeester**: eerst de volledige naam; anders een **voornaam** die bij precies één persoon met die rol hoort ("Peter" → de enige coach die zo heet). Namen worden vergeleken zonder hoofdletters, extra spaties en accenten ("André" = "Andre"). Bij de coachkolom wordt "Stage" de invulling **Stage** en "Minor …" de invulling **Minor** (als de invulling nog leeg is). Al het andere (geen of meer dan één match, "Studiepauze …") blijft leeg met een melding.
  - **Invulling** en **rol in de squad**: alleen de bekende waarden ([gegevensmodel.md](../../docs/gegevensmodel.md#student)), zonder onderscheid tussen hoofd- en kleine letters.
  - Excel-foutwaarden ("#N/A", "#N/B", "#REF!", …) en lege cellen tellen als leeg.
  - *Acceptatie:* "Semester 4 (her)" → 4; "02 - Iets anders" → project 02; "Game developer (GD)" → GD; "ja" in de gildekolom → leeg met melding; "Peter" met één coach "Peter Snoek" → die coach; "Stage" in de coachkolom → invulling Stage.
- [x] **F8 – Notities.** Kolommen met de koppeling Notitie worden per student één regel **"Kolomnaam: waarde"** in het veld **Notities** (lege waarden niet). Bij een bestaande student worden alleen regels toegevoegd die er nog niet staan; wat er al staat, blijft staan.
  - *Acceptatie:* kolommen "Discord" en "Herkomst" → twee regels; dezelfde import nog een keer → geen dubbele regels.
- [x] **F9 – Coach voor nieuwe studenten.** In het voorbeeld staat de keuze **"Coach voor nieuwe studenten zonder coach"** (de coaches van de pagina Coaches, standaard leeg). Die geldt alleen voor nieuwe studenten zonder coach uit het bestand.
  - *Acceptatie:* een bestand zonder coachkolom + keuze "Peter Snoek" → alle nieuwe studenten hebben coach Peter Snoek.
- [x] **F10 – Herkennen van bestaande studenten.** Een rij hoort bij een bestaande student als het **studentnummer** gelijk is, of anders als de **naam** gelijk is (zonder onderscheid tussen hoofd- en kleine letters en extra spaties, [gegevensmodel.md](../../docs/gegevensmodel.md#koppelen-aan-portflow)). Demostudenten tellen niet mee.
  - *Acceptatie:* een student zonder studentnummer met dezelfde naam als een rij wordt "Bestaand" en krijgt het studentnummer erbij.
- [x] **F11 – Importeren.** De knop **"Importeren"** ("12 toevoegen, 30 bijwerken") slaat op wat is aangevinkt en aangevuld, en gaat naar Studenten met de melding "12 studenten toegevoegd, 30 bijgewerkt." Annuleren slaat niets op. Nieuwe studenten zonder semester of primaire beroepsrol komen in "Nog in te delen".
  - *Acceptatie:* na importeren staan de nieuwe studenten in de lijst; bij Annuleren is er niets veranderd.

### Notities bij een student

- [x] **F12 – Notities in Student bewerken.** De pagina Student bewerken ([spec 011](../011-student-bewerken/spec.md)) krijgt een tekstvak **"Notities"** (niet verplicht). De notities staan niet in de tabellen.
  - *Acceptatie:* een notitie wijzigen en opslaan bewaart de nieuwe tekst.

### Buiten scope

- .xls, .csv en geplakte cellen (manier 4 is een eigen spec)
- Een naam samenstellen uit meer kolommen (zoals roepnaam, voorvoegsels en achternaam in een Osiris-export)
- Projecten, semesters, rollen of coaches aanmaken tijdens het importeren
- Automatisch koppelen aan Portflow op naam ([gegevensmodel.md](../../docs/gegevensmodel.md#koppelen-aan-portflow)): eigen spec

## Schermen

Geen eigen ontwerp. Uploadpagina, koppelstap en voorbeeld volgen de pagina's van Studenten toevoegen ([spec 004](../004-studenten-toevoegen/spec.md)): kaarten, een lijst met aankruisvakjes, zoeken en "Selecteer alles / niets".

## Data

- **Bron:** het gekozen .xlsx-bestand en de eigen opslag. Deze functie roept Portflow niet aan.
- **Velden:** zie F4; nieuw is het studentveld **Notities** ([gegevensmodel.md](../../docs/gegevensmodel.md#student)).
- **Privacy:** het bestand wordt **niet bewaard**: de app leest het in het geheugen, houdt de ingelezen rijen alleen vast tot de import klaar of afgebroken is (of de app herstart), en gooit ze dan weg. Notities kunnen contactgegevens bevatten (bijvoorbeeld een Discord-naam of telefoonnummer) als de gebruiker die kolommen niet op "Niet gebruiken" zet; ze blijven lokaal in de database.

## Technische eisen

- Inlezen zonder extra pakket: een .xlsx is een zip met XML ([architectuur.md](../../docs/architectuur.md)). Ondersteund: gedeelde tekst, getallen, booleans, inline-tekst; formules via hun bewaarde waarde.
- Het herkennen van kolommen (F4), het omzetten van waarden (F7) en het herkennen van bestaande studenten (F10) staan op één plek in de code, los van de pagina's.
- De studenttabel krijgt de kolom `notes`; migratie bij het starten.
- Tests met **zelf gemaakte .xlsx-bestanden met verzonnen namen** (geen echte bestanden): andere kolomvolgorde, kopregel op rij 3, onbekende kolomnaam (koppelstap), meer werkbladen, foutwaarden, F7-omzettingen, F8 zonder dubbele regels, F10 en een kapot bestand.

## Open vragen

- [x] **Onbekende kolommen:** als notitie bij de student (F8); per kolom ook "Niet gebruiken" (F5).
- [x] **Bestaande student met andere waarde:** lege velden aanvullen, verschillen tonen met "overnemen" (standaard uit) (F6).
- [x] **Coach als voornaam, "Stage", "Minor …":** voornaam koppelen als die uniek is; Stage en Minor worden de invulling (F7).
- [x] **Project en semester:** op nummer; onbekend project blijft leeg met melding; "(her)" wordt niet bewaard (F7).
- [x] **Notitie bij opnieuw importeren:** nieuwe regels aanvullen (F8).
- [x] **Notitie tonen:** bij Student bewerken, niet in de tabellen (F12).
- [x] **Inlezen:** zonder extra pakket, alleen .xlsx.
- [x] **Coach voor nieuwe studenten:** een keuze in het voorbeeld, standaard leeg (F9).

## Logboek

- 2026-11-09 – spec aangemaakt op verzoek van de gebruiker, na analyse van twee voorbeeldbestanden (alleen de structuur); antwoorden verwerkt; status uitgewerkt
- 2026-11-09 – gebouwd en getest: unit tests met verzonnen bestanden, een droge proef op de twee echte bestanden (alleen tellingen, niets opgeslagen) en de browser; status klaar. Toegevoegd tijdens het bouwen: namen van coaches en gildemeesters worden zonder accenten vergeleken ("André" = "Andre")
- 2026-11-09 – F6 gewijzigd op verzoek van de gebruiker: nieuwe studenten zijn alleen aangevinkt als de naam van de gebruiker in hun rij staat
- 2026-11-09 – gewijzigde F6 gebouwd en getest; status klaar
- 2026-11-09 – na het importeren wordt direct aan Portflow gekoppeld als de verbinding geldig is ([spec 015](../015-koppelen-aan-portflow/spec.md), F3)
- 2026-11-10 – aangepast door [spec 016](../016-gildes-van-een-student/spec.md): de gildekolommen worden samen de gildes van de student; een kolom Gildemeester hoort bij het eerste gilde in de rij
- 2026-11-10 – aangepast door [spec 018](../018-beroepsrol-in-gilde/spec.md): een gildekolom herkent een gilde aan zijn code, naam of beroepsrol
