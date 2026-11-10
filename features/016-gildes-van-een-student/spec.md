# 016 – Gildes van een student

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-10

> **Waarom:** bij Student bewerken waren de velden niet consequent: een primaire beroepsrol, losse secundaire beroepsrollen en maar één gildemeester. In de praktijk kiest een student per gilde een gildemeester; de meeste studenten hebben één gilde, sommigen doen productevaluaties in een tweede of derde gilde. Er is **geen onderscheid** tussen een primair en een ander gilde, en **geen volgorde**.

## Doel

Als **coach** of **gildemeester** wil ik per student een lijst gildes vastleggen, elk met een eigen gildemeester, zodat duidelijk is wie welke productvaardigheden van de student beoordeelt.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- Beroepsrol en gilde (één gilde per beroepsrol, [gegevensmodel.md](../../docs/gegevensmodel.md#gilde)), gildemeester, "Nog in te delen"

## Functionele eisen

### Gegevens

- [x] **F1 – Gildes van een student.** Een student heeft **nul of meer gildes**, zonder volgorde en zonder "primair". Per gilde: de **beroepsrol** (waaruit het gilde volgt) en de **gildemeester** (niet verplicht). Elke beroepsrol hooguit één keer per student. Dit vervangt de velden primaire beroepsrol, secundaire beroepsrollen en gildemeester.
  - *Acceptatie:* een student kan FE met gildemeester A en UX met gildemeester B hebben; twee keer FE kan niet.
- [x] **F2 – Nog in te delen.** Een student staat bij **"Nog in te delen"** als hij **geen semester of geen gilde** heeft.
  - *Acceptatie:* semester 3 zonder gilde → Nog in te delen; semester 3 met één gilde → ingedeeld.
- [x] **F3 – Overzetten van bestaande gegevens.** Bij het starten worden bestaande gegevens eenmalig omgezet: de primaire beroepsrol met de gildemeester van de student wordt één gilde; elke secundaire beroepsrol wordt een gilde zonder gildemeester.
  - *Acceptatie:* een student met primair FE, gildemeester A en secundair CS heeft daarna de gildes FE (A) en CS (geen gildemeester).

### Student bewerken ([spec 011](../011-student-bewerken/spec.md))

- [x] **F4 – Gildes bewerken.** In plaats van de velden Primaire beroepsrol, Gilde, Secundaire beroepsrollen en Gildemeester staat het blok **"Gildes"**: per gilde een regel met een keuze uit de beroepsrollen (met de gildenaam erbij) en een keuze uit **alle gildemeesters** (plus "Geen"), en een knop "Verwijderen". Onderaan **"+ Gilde toevoegen"**. Een lege regel (zonder beroepsrol) wordt genegeerd; dezelfde beroepsrol twee keer geeft de melding "FE staat er twee keer in." Werkt ook zonder JavaScript (er staat altijd één lege regel extra).
  - *Acceptatie:* een gilde UX met gildemeester B toevoegen en opslaan → de student heeft FE (A) en UX (B); FE verwijderen → alleen UX (B).

### Waar het verder doorwerkt

- [x] **F5 – Tabellen.** In het studentenoverzicht ([spec 001](../001-studentenoverzicht/spec.md)) heet de kolom Profiel voortaan **"Gilde"** en toont hij alle codes ("FE, UX"); de extra kolom Gildemeester toont alle gildemeesters. In de studentenlijst ([spec 010](../010-studentenlijst/spec.md)) vervangen de kolommen **Gilde** (alle codes, naam bij hover) en **Gildemeester** (alle namen) de kolommen Beroepsrol, Gilde, Secundaire rollen en Gildemeester. Sorteren gaat op de eerste code alfabetisch.
  - *Acceptatie:* een student met FE (A) en UX (B) toont "FE, UX" en "A, B".
- [x] **F6 – Filteren en groeperen.** Het filter op beroepsrol toont studenten die die rol bij **één van** hun gildes hebben. **"Groeperen: Gilde"** zet een student met meer gildes in **elke** groep; de keuze "Groeperen: Beroepsrol" vervalt (die is nu hetzelfde). **"Mijn gildestudenten"** = studenten bij wie de gebruiker gildemeester is bij één van hun gildes.
  - *Acceptatie:* een student met FE en UX staat bij "Groeperen: Gilde" in de groepen FE en UX; is de gebruiker gildemeester bij zijn UX-gilde, dan staat hij in "Mijn gildestudenten".
- [x] **F7 – Beheerpagina's.** Op Beroepsrollen ([spec 008](../008-beroepsrollen/spec.md)) toont een kaart **"N studenten"** (geen primair/secundair meer); verwijderen van een rol haalt dat gilde bij de studenten weg. Op Gildemeesters ([spec 006](../006-gildemeesters/spec.md)) telt een kaart de studenten bij wie de persoon bij één van hun gildes gildemeester is; de rol gildemeester verwijderen maakt die gildemeester bij al die gildes leeg.
  - *Acceptatie:* rol FE verwijderen → studenten met alleen FE staan bij Nog in te delen; studenten met FE en UX houden UX.
- [x] **F8 – Excel-import.** In de import ([spec 013](../013-excel-importeren/spec.md)) worden de kolommen **Gilde** en **Eventueel 2e gilde** (en andere gildekolommen) samen de gildes van de student; een kolom **Gildemeester** hoort bij het eerste gilde uit dezelfde rij. Bij een bestaande student worden alleen gildes toegevoegd die hij nog niet heeft (aanvullen), en een lege gildemeester bij een bestaand gilde wordt aangevuld.
  - *Acceptatie:* "Front-end developer (FE)" en "Cybersecurity engineer (CS)" in één rij → de gildes FE en CS.

### Buiten scope

- Een volgorde of "primair" gilde
- Per gilde bijhouden welke productvaardigheden de student daar laat evalueren

## Schermen

Geen eigen ontwerp. Het blok "Gildes" volgt de formulieren van de beheerpagina's: per regel twee keuzelijsten en een knop.

## Data

- **Bron:** eigen opslag. Deze functie roept Portflow niet aan.
- **Nieuw:** een koppeltabel student – beroepsrol – gildemeester. De velden primaire beroepsrol, gildemeester en de tabel secundaire beroepsrollen vervallen (na het overzetten van F3).

## Technische eisen

- Eén koppeltabel (`student_guilds`: student, beroepsrol, gildemeester; uniek per student en beroepsrol), met een migratie bij het starten (F3).
- Alle plekken die de primaire beroepsrol, de secundaire beroepsrollen of het veld gildemeester gebruikten, gebruiken de koppeltabel: overzicht en filters, studentenlijst, Student bewerken, Beroepsrollen, Gildemeesters, Gildes (aantal studenten), Excel-import, demodata en de tests.
- De docs ([begrippen.md](../../docs/begrippen.md), [gegevensmodel.md](../../docs/gegevensmodel.md), [beroepsrollen.md](../../docs/beroepsrollen.md)) worden aangepast: een student heeft nul of meer gildes, elk met een gildemeester; geen primaire beroepsrol meer.
- Tests voor F1–F8, waaronder de migratie.

## Open vragen

- [x] **Primair en volgorde:** geen van beide; alle gildes zijn gelijk (F1).
- [x] **Aantal gildes:** onbeperkt.
- [x] **Keuze van de gildemeester:** uit alle gildemeesters (F4).
- [x] **Mijn gildestudenten en de kolom Gildemeester:** alle gildes tellen (F5, F6).
- [x] **Nog in te delen:** geen semester of geen gilde (F2).
- [x] **Weergave en groeperen:** alle codes; bij groeperen in elke groep; "Groeperen: Beroepsrol" vervalt (F5, F6).

## Logboek

- 2026-11-10 – spec aangemaakt na de vraag van de gebruiker over het scherm Student bewerken; antwoorden verwerkt; status uitgewerkt
- 2026-11-10 – gebouwd en getest (unit tests, ook de migratie); docs en de logboeken van specs 001, 006, 008, 010, 011 en 013 bijgewerkt; status klaar
