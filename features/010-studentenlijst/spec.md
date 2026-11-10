# 010 – Studentenlijst

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-09

> **Bouwvolgorde:** na [spec 001 – Studentenoverzicht](../001-studentenoverzicht/spec.md), waarvan deze pagina de filters, het groeperen, het zoeken en het sorteren overneemt. Tegelijk verhuist de voortgangstabel volledig naar Overzicht (spec 001, F1).

## Doel

Als **coach** of **gildemeester** wil ik op de pagina **Studenten** de basisgegevens van mijn studenten in één tabel zien (semester, project, invulling, rol in de squad, beroepsrollen, gilde, coach, gildemeester en de Portflow-koppeling), zodat ik snel zie hoe iedereen is ingedeeld en wat nog ontbreekt. De voortgang staat op Overzicht en is hier niet nodig.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- Velden van een student ([gegevensmodel.md](../../docs/gegevensmodel.md#student)), "Nog in te delen"
- Gilde van een student: volgt uit de primaire beroepsrol ([gegevensmodel.md](../../docs/gegevensmodel.md#gilde))
- Rol in de squad: PO, SM, 2ePO, 2eSM ([begrippen.md](../../docs/begrippen.md))

## Functionele eisen

- [x] **F1 – Kolommen.** Eén rij per gevolgde student, met deze kolommen in deze volgorde:
  1. **Student**: avatar met initialen en naam;
  2. **Semester**;
  3. **Project**: de squad, bijvoorbeeld "02 Condor";
  4. **Invulling**;
  5. **Rol**: de rol in de squad als kort label (PO, SM, 2ePO, 2eSM), met de volledige naam bij hover (product owner, scrum master, tweede product owner, tweede scrum master);
  6. **Beroepsrol**: de primaire beroepsrol (code, met de naam bij hover);
  7. **Gilde**: het gilde van de primaire beroepsrol (code, met de naam bij hover);
  8. **Secundaire rollen**: de codes, gescheiden door komma's;
  9. **Coach**;
  10. **Gildemeester**;
  11. **Portflow**: "Gekoppeld", "Niet gekoppeld" of "Portfolio niet gedeeld".
  Een leeg veld toont "–". Geen voortgang, signalen of eigen kolommen.
  - *Acceptatie:* een student in semester 3, project "02 Condor", rol SM, primaire rol FE met gilde FE, coach "A. Coach" en een gedeeld portfolio toont precies die waarden in de genoemde kolommen.
- [x] **F2 – Filters, groeperen, zoeken en sorteren.** Dezelfde filters als het studentenoverzicht (wie, semester, invulling, project, beroepsrol, "Aan te sporen"), hetzelfde groeperen, zoeken (⌘K) en sorteren door op een kolomkop te klikken ([spec 001](../001-studentenoverzicht/spec.md), F13–F18). Onderaan "X van Y studenten".
  - *Acceptatie:* "Mijn coachstudenten" + semester 3 toont alleen coachstudenten in semester 3; klikken op "Coach" sorteert op coach.
- [x] **F3 – Lege toestand en knop.** Zonder studenten de lege staat van [spec 004](../004-studenten-toevoegen/spec.md) (F1); met studenten de knop "+ Student toevoegen" in de paginakop.
  - *Acceptatie:* 0 studenten → uitleg en knop; geen lege tabel.
- [x] **F4 – Paginakop.** Kopje "Studievoortgang", titel "Studenten", uitleg "Alle studenten die je volgt, met hun indeling."
  - *Acceptatie:* de pagina toont deze kop.

### Buiten scope

- Gegevens van een student bewerken: [spec 011](../011-student-bewerken/spec.md); de naam in de lijst opent die pagina
- Voortgang, signalen en eigen kolommen: op Overzicht ([spec 001](../001-studentenoverzicht/spec.md))

## Schermen

Geen eigen ontwerp. Volgt de tabel van het studentenoverzicht ([design-system.md](../../docs/design-system.md#overzicht)): dezelfde werkbalk met filters, groepskoppen en teller, met andere kolommen.

## Data

- **Bron:** eigen opslag (studenten, squads, beroepsrollen, gildes, coaches en gildemeesters). Deze functie roept Portflow niet aan.
- **Privacy:** studentnamen en indeling; lokaal.

## Technische eisen

- Werkbalk, filters, groeperen, zoeken en sorteren zijn dezelfde code als in spec 001 (één component voor de werkbalk); alleen de kolommen verschillen.
- Tests voor F1 (kolommen en waarden), F2 (filter en volgorde) en F3.

## Open vragen

- [x] **Overzicht:** toont voortaan de volledige voortgangstabel (spec 001, F1).
- [x] **Kolommen:** naast de genoemde ook project, primaire en secundaire beroepsrollen en de Portflow-koppeling.
- [x] **Rol:** als kort label met de volledige naam bij hover.

## Logboek

- 2026-11-09 – spec aangemaakt op verzoek van de gebruiker; antwoorden verwerkt; status uitgewerkt
- 2026-11-09 – gebouwd en getest (unit tests en in de browser); status klaar
- 2026-11-10 – de keuze "Niet groeperen" (spec 001, F16) geldt ook hier, via de gedeelde werkbalk
- 2026-11-10 – aangepast door [spec 016](../016-gildes-van-een-student/spec.md): de kolommen Beroepsrol, Gilde, Secundaire rollen en Gildemeester zijn samengevoegd tot Gilde en Gildemeester
