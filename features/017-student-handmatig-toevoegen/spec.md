# 017 – Student handmatig toevoegen

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-10

> **Bouwvolgorde:** na [spec 011 – Student bewerken](../011-student-bewerken/spec.md) en [spec 016 – Gildes van een student](../016-gildes-van-een-student/spec.md), waarvan dit formulier de velden overneemt, en [spec 015 – Koppelen aan Portflow](../015-koppelen-aan-portflow/spec.md).

## Doel

Als **coach** of **gildemeester** wil ik één student met de hand toevoegen, met al zijn gegevens in één keer, bijvoorbeeld een student die later instroomt of die (nog) niet in een Excelbestand of de gedeelde portfolio's staat.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- Velden van een student en "Nog in te delen" ([gegevensmodel.md](../../docs/gegevensmodel.md#student)), de manieren van toevoegen ([gegevensmodel.md](../../docs/gegevensmodel.md#studenten-toevoegen))

## Functionele eisen

- [x] **F1 – Kaart.** Op de pagina Studenten toevoegen ([spec 004](../004-studenten-toevoegen/spec.md), F3) komt een **extra kaart "Handmatig invoeren"** ("Voeg één student toe en vul meteen zijn gegevens in."), naast de bestaande kaarten. De kaarten "Namen typen of plakken" en "CSV of Excelcellen plakken" blijven "Binnenkort beschikbaar".
  - *Acceptatie:* de pagina toont vijf kaarten; "Handmatig invoeren" opent het formulier van F2.
- [x] **F2 – Formulier.** Een pagina **"Student toevoegen"** met dezelfde velden en keuzes als Student bewerken ([spec 011](../011-student-bewerken/spec.md) F2, met het blok Gildes van [spec 016](../016-gildes-van-een-student/spec.md) F4 en Notities), leeg. Alleen de **naam** is verplicht; dezelfde controles als bij bewerken ([spec 011](../011-student-bewerken/spec.md), F5). Het blok Portflow en de knop "Student niet meer volgen" staan er niet bij.
  - *Acceptatie:* het formulier toont naam, studentnummer, semester, startdatum, project, invulling, rol in de squad, gildes (met gildemeester), coach en notities; een lege naam wordt geweigerd met "Vul een naam in." en de andere velden blijven ingevuld.
- [x] **F3 – Dubbele student.** Is er al een student met **dezelfde naam** (zonder onderscheid tussen hoofd- en kleine letters, extra spaties en accenten), dan toont de app eerst de waarschuwing **"Er is al een student met deze naam"** met een link naar die student, en een vinkje **"Toch toevoegen"**; pas met dat vinkje wordt hij toegevoegd. Een **studentnummer** dat al bij een andere student hoort, wordt geweigerd ("Dit studentnummer hoort al bij Eva Kok.").
  - *Acceptatie:* een tweede "Eva Kok" → waarschuwing; met "Toch toevoegen" → twee studenten. Een bestaand studentnummer → geweigerd.
- [x] **F4 – Opslaan.** "Opslaan" voegt de student toe en gaat naar **Studenten** met de melding **"Eva Kok toegevoegd."** Is de verbinding met Portflow geldig, dan koppelt de app de student meteen op naam aan een gedeeld portfolio ([spec 015](../015-koppelen-aan-portflow/spec.md), F1), en de melding zegt "… gekoppeld aan Portflow. Klik op Verversen om de evaluaties op te halen." of "… niet gevonden in je gedeelde portfolio's." Zonder verbinding: "Klik op Verversen om de student aan Portflow te koppelen." "Annuleren" gaat terug naar Studenten toevoegen zonder iets op te slaan.
  - *Acceptatie:* een student met semester 3 en één gilde staat daarna in de lijst onder zijn project, niet onder "Nog in te delen"; een student zonder semester of gilde staat onder "Nog in te delen".

### Buiten scope

- Meer studenten tegelijk invoeren ("Namen typen of plakken", "CSV of Excelcellen plakken": eigen specs)
- De Portflow-koppeling in dit formulier kiezen (kan daarna bij Student bewerken, [spec 015](../015-koppelen-aan-portflow/spec.md) F5)

## Schermen

Geen eigen ontwerp: het formulier van Student bewerken, met de titel "Student toevoegen".

## Data

- **Bron:** eigen opslag; alleen bij een geldige verbinding de lijst met gedeelde portfolio's (F4, [spec 015](../015-koppelen-aan-portflow/spec.md)).
- **Privacy:** gegevens van één student; lokaal.

## Technische eisen

- Hetzelfde formulier en dezelfde controles als Student bewerken (één sjabloon en één controlefunctie), zonder kopie van de code.
- Tests voor F1–F4.

## Open vragen

- [x] **Wat:** één student via een formulier (F2).
- [x] **Kaart:** een extra kaart; "Namen typen of plakken" blijft bestaan (F1).
- [x] **Na opslaan:** terug naar Studenten, met koppelen aan Portflow als dat kan (F4).
- [x] **Dubbele student:** bij dezelfde naam waarschuwen en toch toestaan; een gelijk studentnummer weigeren (F3).

## Logboek

- 2026-11-10 – spec aangemaakt op verzoek van de gebruiker; antwoorden verwerkt; status uitgewerkt
- 2026-11-10 – gebouwd en getest (unit tests en in de browser); status klaar
