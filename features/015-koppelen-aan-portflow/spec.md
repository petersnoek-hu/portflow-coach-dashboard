# 015 – Koppelen aan Portflow

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-09

> **Aanleiding:** na het terugzetten ([spec 014](../014-alles-verwijderen/spec.md)) en een Excel-import ([spec 013](../013-excel-importeren/spec.md)) toonde Overzicht na Verversen geen voortgang: studenten uit Excel hebben geen Portflow-koppeling, en Verversen haalt alleen evaluaties op voor gekoppelde studenten ([spec 005](../005-gegevens-ophalen/spec.md), F1). Het koppelen op naam stond al in [gegevensmodel.md](../../docs/gegevensmodel.md#koppelen-aan-portflow), maar was nog niet gebouwd.

## Doel

Als **coach** of **gildemeester** wil ik dat studenten die niet via "Uit Portflow kiezen" zijn toegevoegd, vanzelf aan hun gedeelde portfolio worden gekoppeld, zodat hun evaluaties worden opgehaald. Lukt dat niet automatisch, dan wil ik het zelf kunnen koppelen.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- Portflow-koppeling van een student, gedeelde portfolio's ([gegevensmodel.md](../../docs/gegevensmodel.md#koppelen-aan-portflow), [spec 004](../004-studenten-toevoegen/spec.md) F6)

## Functionele eisen

- [x] **F1 – Automatisch op naam.** Een niet-gekoppelde student (geen demostudent) wordt gekoppeld aan een gedeelde Portflow-student als de namen gelijk zijn, zonder onderscheid tussen hoofd- en kleine letters, extra spaties en accenten, en als er **precies één** gedeelde student met die naam is die nog niet aan een andere student gekoppeld is. Gekoppeld worden de Portflow-gebruiker en al zijn gedeelde portfolio's.
  - *Acceptatie:* de student "Anna de Boer" en een gedeeld portfolio van "anna de böer" → gekoppeld; twee gedeelde portfolio's van verschillende Portflow-gebruikers met dezelfde naam → niet gekoppeld.
- [x] **F2 – Bij Verversen.** Elke Verversen-ronde ([spec 005](../005-gegevens-ophalen/spec.md)) haalt eerst de gedeelde portfolio's op, koppelt volgens F1 en voegt bij al gekoppelde studenten nieuw gedeelde portfolio's toe; daarna haalt hij de evaluaties op, ook van de net gekoppelde studenten. Lukt het ophalen van de gedeelde portfolio's niet (anders dan 401), dan gaat de ronde door met de bestaande koppelingen.
  - *Acceptatie:* 12 ongekoppelde studenten met een gedeeld portfolio → na één ronde zijn ze gekoppeld en staan hun evaluaties op Overzicht.
- [x] **F3 – Na een Excel-import.** Is de verbinding geldig, dan koppelt de app direct na het importeren volgens F1 (zonder evaluaties op te halen). De melding wordt bijvoorbeeld "12 studenten toegevoegd, 0 bijgewerkt. 12 gekoppeld aan Portflow. Klik op Verversen om hun evaluaties op te halen." Zonder verbinding: "… Klik op Verversen om ze aan Portflow te koppelen en hun evaluaties op te halen."
  - *Acceptatie:* importeren terwijl de verbinding geldig is → de nieuwe studenten zijn gekoppeld.
- [x] **F4 – Melden wat niet lukt.** Studenten die na een ronde nog niet gekoppeld zijn, meldt de Verversen-knop: "Bijgewerkt om 14:32 · 2 niet gekoppeld", met hun namen bij hover. In Studenten staat bij hen "Niet gekoppeld" in de kolom Portflow ([spec 010](../010-studentenlijst/spec.md)).
  - *Acceptatie:* een student zonder gedeeld portfolio → de knop meldt "1 niet gekoppeld".
- [x] **F5 – Zelf koppelen.** Bij Student bewerken ([spec 011](../011-student-bewerken/spec.md), F3) staat bij Portflow een keuzelijst met de gedeelde Portflow-studenten (naam) die nog niet aan een andere student gekoppeld zijn, plus "Niet gekoppeld". De huidige koppeling is geselecteerd. Kiest de gebruiker een andere student of "Niet gekoppeld", dan vervallen ook de bewaarde evaluaties van de oude koppeling; de volgende Verversen-ronde haalt die van de nieuwe op. Zonder geldige verbinding is de keuze niet beschikbaar en staat er "Verbind met Portflow om te koppelen."
  - *Acceptatie:* een ongekoppelde student koppelen aan een gedeeld portfolio → na opslaan staat in Studenten "Gekoppeld"; daarna "Niet gekoppeld" kiezen → de koppeling en de evaluaties zijn weg.

### Buiten scope

- Koppelen op studentnummer (Portflow levert dat voor zover bekend niet)
- Gelijkende namen (bijvoorbeeld zonder tussenvoegsel) automatisch koppelen; die kun je zelf koppelen (F5)

## Schermen

Geen eigen ontwerp: een melding in de Verversen-knop, een keuzelijst bij Student bewerken en de bestaande kolom Portflow in Studenten.

## Data

- **Bron:** Portflow API: `GET /shares/shared-with-me` ([architectuur.md](../../docs/architectuur.md#portflow-api)), zoals in [spec 004](../004-studenten-toevoegen/spec.md). De lijst wordt kort (5 minuten) in het geheugen bewaard, zodat Student bewerken snel opent.
- **Privacy:** alleen naam, Portflow-gebruiker-id en portfolio-id's; lokaal.

## Technische eisen

- Het vergelijken van namen (F1) gebruikt dezelfde functie als de Excel-import (zonder hoofdletters, spaties en accenten), op één plek.
- Het koppelen staat op één plek in de code; Verversen, de import en Student bewerken gebruiken die.
- Tests met een nagebootste Portflow: F1 (uniek, dubbel, accenten, al gekoppeld), F2, F3, F4 en F5.

## Open vragen

- [x] **Twijfelgevallen:** melden (F4) en zelf koppelen bij Student bewerken (F5).
- [x] **Wanneer:** bij elke Verversen-ronde (F2) en direct na een Excel-import als de verbinding geldig is (F3).

## Logboek

- 2026-11-09 – spec aangemaakt na de melding van de gebruiker dat Overzicht na Verversen geen voortgang toonde; antwoorden verwerkt; status in bouw
- 2026-11-10 – gebouwd en getest (unit tests met een nagebootste Portflow; op een kopie van de echte database werden alle 12 ongekoppelde studenten gekoppeld); status klaar
