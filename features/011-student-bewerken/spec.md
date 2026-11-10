# 011 – Student bewerken

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-09

> **Bouwvolgorde:** na [spec 010 – Studentenlijst](../010-studentenlijst/spec.md), vanwaar deze pagina wordt geopend. Dit is (een eerste deel van) de kandidaat-spec *Studenten beheren*.

## Doel

Als **coach** of **gildemeester** wil ik vanuit de lijst met studenten één student openen en al zijn gegevens aanpassen (semester, project, invulling, rol, beroepsrollen, coach, gildemeester, …), zodat de indeling klopt en de student uit "Nog in te delen" verdwijnt. Ook wil ik een student kunnen verwijderen als ik hem niet meer volg.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- Velden van een student ([gegevensmodel.md](../../docs/gegevensmodel.md#student)), "Nog in te delen"
- Semesters ([spec 009](../009-semesters/spec.md)), beroepsrollen ([spec 008](../008-beroepsrollen/spec.md)), gildes ([spec 006](../006-gildemeesters/spec.md)), coaches en gildemeesters ([spec 006](../006-gildemeesters/spec.md), [spec 007](../007-coaches/spec.md))

## Functionele eisen

- [x] **F1 – Openen.** Op de pagina Studenten is de naam van een student een link. Een klik opent de pagina **"Student bewerken"** van die student. De pagina onthoudt met welke filters de lijst openstond.
  - *Acceptatie:* een klik op "Sem Bakker" in de lijst (met filter semester 3) opent "Student bewerken · Sem Bakker".
- [x] **F2 – Velden.** Het formulier toont de huidige waarden en heeft deze velden:
  - **naam** (verplicht);
  - **studentnummer** (OV-nummer, niet verplicht);
  - **semester**: een keuze uit de semesters op de pagina Semesters, met de Osiris-code erbij, plus "Geen (Nog in te delen)". Bestaan er nog geen semesters, dan staat er een link naar Semester toevoegen;
  - **startdatum** (niet verplicht): eigen begin van de semesterperiode;
  - **project**: een keuze uit de projecten (squads), plus "Zonder project";
  - **invulling**: Open projecten, Open innovatieproject, Stage, Minor of Afstuderen, of leeg;
  - **rol in de squad**: PO, SM, 2ePO of 2eSM (met de volledige naam), of geen;
  - **primaire beroepsrol**: een keuze uit de beroepsrollen, plus "Geen (Nog in te delen)". Het **gilde** dat daaruit volgt, staat ernaast (alleen lezen);
  - **secundaire beroepsrollen**: aanvinken uit de beroepsrollen; de primaire rol telt niet als secundaire rol;
  - **coach**: een keuze uit de coaches, plus "Geen";
  - **gildemeester**: een keuze uit de gildemeesters, plus "Geen".
  - *Acceptatie:* een student met semester 3 en coach "A. Coach" toont die waarden vooringevuld.
- [x] **F3 – Portflow (alleen lezen).** Onder het formulier staat de Portflow-koppeling: "Gekoppeld" met de portfolio-id's, "Portfolio niet gedeeld" of "Niet gekoppeld". Wijzigen kan sinds [spec 015](../015-koppelen-aan-portflow/spec.md) (F5) met een keuzelijst.
  - *Acceptatie:* een gekoppelde student met twee portfolio's toont beide id's.
- [x] **F4 – Opslaan.** "Opslaan" bewaart alle velden en gaat terug naar Studenten, met dezelfde filters als waarmee de gebruiker kwam, en de melding "Gegevens van Sem Bakker opgeslagen." Een student met semester én primaire beroepsrol staat daarna niet meer onder "Nog in te delen". "Annuleren" gaat terug zonder iets te bewaren.
  - *Acceptatie:* semester 3 en primaire rol FE invullen bij een student uit "Nog in te delen" → terug in de lijst staat hij onder zijn project (of "Zonder project") en niet meer onder "Nog in te delen".
- [x] **F5 – Controle.** De naam is verplicht; een startdatum moet een geldige datum zijn; gekozen semesters, projecten, rollen, coaches en gildemeesters moeten bestaan. Bij een fout blijft het formulier ingevuld en staat de uitleg erbij.
  - *Acceptatie:* een lege naam wordt geweigerd met "Vul een naam in." en de andere ingevulde velden blijven staan.
- [x] **F6 – Niet meer volgen.** De knop **"Student niet meer volgen"** vraagt eerst om bevestiging ("Sem Bakker niet meer volgen? De student, zijn bewaarde evaluaties en de waarden in eigen kolommen verdwijnen uit het dashboard. In Portflow verandert niets."). Na bevestiging is de student weg en gaat de gebruiker terug naar Studenten met de melding "Sem Bakker wordt niet meer gevolgd."
  - *Acceptatie:* na bevestigen is de student met zijn evaluaties uit de database verdwenen; bij Annuleren blijft alles staan.

### Buiten scope

- De Portflow-koppeling wijzigen of verwijderen
- Meerdere studenten tegelijk bewerken, studenten verplaatsen tussen semesters vanaf de pagina Semesters
- Waarden van eigen kolommen: die vult de gebruiker in de voortgangstabel in ([spec 001](../001-studentenoverzicht/spec.md), F8)
- Projecten (squads) beheren: eigen spec

## Schermen

Geen eigen ontwerp. Het formulier volgt de formulieren van de beheerpagina's ([spec 008](../008-beroepsrollen/spec.md), [spec 009](../009-semesters/spec.md)), in twee kolommen; de bevestiging volgt die van de andere verwijderknoppen.

## Data

- **Bron:** eigen opslag. Deze functie roept Portflow niet aan.
- **Privacy:** gegevens van één student; lokaal.

## Technische eisen

- Het semester blijft een nummer in `students`; de keuzelijst toont alleen bestaande semesters.
- Verwijderen gebruikt de bestaande koppelingen in de database (evaluaties, portfolio's, secundaire rollen en eigen-kolomwaarden verdwijnen mee).
- De terugweg naar de lijst neemt alleen lokale paden over.
- Tests voor F1, F2 (vooringevuld), F4 (opslaan, uit "Nog in te delen"), F5 (lege naam) en F6.

## Open vragen

- [x] **Semester:** keuze uit de pagina Semesters (F2).
- [x] **Portflow-koppeling:** alleen bekijken (F3).
- [x] **Verwijderen:** ja, met bevestiging (F6).
- [x] **Na opslaan:** terug naar Studenten, met dezelfde filters (F4).

## Logboek

- 2026-11-09 – spec aangemaakt op verzoek van de gebruiker; antwoorden verwerkt; status in bouw
- 2026-11-09 – gebouwd en getest (unit tests en in de browser); status klaar
- 2026-11-09 – het veld Notities is toegevoegd via [spec 013](../013-excel-importeren/spec.md), F12
- 2026-11-09 – F3 gewijzigd op verzoek van de gebruiker: de Portflow-koppeling is te wijzigen ([spec 015](../015-koppelen-aan-portflow/spec.md), F5)
- 2026-11-10 – aangepast door [spec 016](../016-gildes-van-een-student/spec.md): de velden Primaire beroepsrol, Secundaire beroepsrollen en Gildemeester zijn vervangen door het blok Gildes
