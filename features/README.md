# Features

Elke functie van het dashboard heeft hier een eigen map met een beschrijving van wat hij moet doen. **Eerst de spec, dan de code.**

## Structuur

```
features/
  _sjabloon/              ← kopieer deze map voor een nieuwe functie
    spec.md
  001-studentenoverzicht/
    spec.md               ← functionele en technische eisen
    design/               ← screenshots, schetsen, Figma-exports van déze functie
      overzicht.png
  002-…/
```

- Mapnaam: `NNN-korte-naam`, met een oplopend nummer van drie cijfers en kleine letters met streepjes.
- Code staat hier níét; die komt in de codemap van het project (zie [`docs/architectuur.md`](../docs/architectuur.md)).
- Ontwerpen die meerdere functies beslaan staan in [`screenshots/`](../screenshots/). Een spec verwijst daarnaar en beschrijft welk deel van dat ontwerp bij de functie hoort.

## Gedeelde bronnen

Een spec herhaalt deze informatie niet, maar verwijst ernaar:

| Bestand | Inhoud |
|---|---|
| [`docs/begrippen.md`](../docs/begrippen.md) | Domeintaal: squad, tribe, gilde, coach, gildemeester, … |
| [`docs/vaardigheden-openict.md`](../docs/vaardigheden-openict.md) | De tien vaardigheden: codes, volgorde, categorieën |
| [`docs/vaardigheden-niveaus-LEF.md`](../docs/vaardigheden-niveaus-LEF.md) | Volledige LEF-tekst per vaardigheid en niveau 1–4 |
| [`docs/voortgangsregels.md`](../docs/voortgangsregels.md) | Evaluaties, toetsprogramma per semester, semester behaald, weergave van niveaus (`-/-`, `1/2`) |
| [`docs/beroepsrollen.md`](../docs/beroepsrollen.md) | De negen beroepsrollen en hun codes |
| [`docs/HBOi-beroepstaken.md`](../docs/HBOi-beroepstaken.md) | De 25 HBO-i-beroepstaken (laag × activiteit) |
| [`docs/gegevensmodel.md`](../docs/gegevensmodel.md) | Bron van de gegevens, velden van een student, studenten toevoegen, kolommen, gebruiker |
| [`docs/design-system.md`](../docs/design-system.md) | Beschrijving van de ontwerpschermen (met afwijkingen), kleuren, niveaulabels, componenten, toon |
| [`docs/architectuur.md`](../docs/architectuur.md) | Techstack, Portflow-gebruik (inloggen, endpoints, verversen), privacy, beslissingen |
| [`docs/portflow-API-reverse-engineer.md`](../docs/portflow-API-reverse-engineer.md) | Volledige beschrijving van de onofficiële Portflow API |
| [`docs/portflow-console-app.py`](../docs/portflow-console-app.py) | Bestaande console-app (referentie) |
| [`screenshots/kompas-dashboard-ontwerp.png`](../screenshots/kompas-dashboard-ontwerp.png) | Ontwerp van het Overzicht ("Kompas" is een werktitel) |
| [`screenshots/projecten-CRUD-met-studenten.png`](../screenshots/projecten-CRUD-met-studenten.png), [`semesters-…`](../screenshots/semesters-CRUD-met-studenten.png), [`beroepsrollen-…`](../screenshots/beroepsrollen-CRUD-met-studenten.png), [`leerdoelen-…`](../screenshots/leerdoelen-CRUD.png) | Ontwerpen van de beheerschermen |
| [`screenshots/vaardigheden-niveaus-LEF.png`](../screenshots/vaardigheden-niveaus-LEF.png) | Weergave van de vaardigheden op lef.hu.nl |

## Werkwijze per functie

1. **Idee:** kopieer `_sjabloon/` naar `NNN-korte-naam/` en vul het doel in. Status `idee`.
2. **Uitwerken:** vul eisen, schermen, data en technische eisen in. Een spec is klaar om te bouwen (status `uitgewerkt`) als:
   - elke functionele eis een toetsbaar acceptatiecriterium heeft;
   - duidelijk is voor welke gebruiker de functie is (coach, gildemeester of beide);
   - termen, vaardigheidscodes en niveaus overeenkomen met de gedeelde bronnen;
   - er een ontwerp is (eigen `design/` of een verwijzing naar `screenshots/`);
   - bekend is welke gegevens uit Portflow nodig zijn;
   - er geen open vragen meer zijn die het bouwen blokkeren.
3. **Bouwen:** status `in bouw`. Vink eisen af zodra ze gebouwd én gecontroleerd zijn.
4. **Afronden:** status `klaar`, regel in het logboek en de tabel hieronder bijwerken.

Wijkt de bouw af van de spec? Dan wordt eerst de spec aangepast.

## Status

| Status | Betekenis |
|---|---|
| `idee` | Alleen het doel is beschreven |
| `uitgewerkt` | Eisen en schermen zijn compleet genoeg om te bouwen |
| `in bouw` | Wordt gebouwd; checklist wordt bijgewerkt |
| `klaar` | Alle eisen gebouwd en gecontroleerd |

## Overzicht

| Nr | Functie | Status |
|---|---|---|
| 001 | [Studentenoverzicht](001-studentenoverzicht/spec.md) | `klaar` |
| 002 | [Basisapplicatie en schil](002-app-schil/spec.md) | `klaar` |
| 003 | [Portflow verbinden](003-portflow-verbinden/spec.md) | `klaar` (F17 niet getest) |
| 004 | [Studenten toevoegen](004-studenten-toevoegen/spec.md) | `klaar` (dekt nu alleen de lege staat, het keuzescherm en "Uit Portflow kiezen"; niet echt getest met Portflow) |
| 005 | [Gegevens ophalen en verversen](005-gegevens-ophalen/spec.md) | `klaar` |
| 006 | [Gildemeesters en gildes](006-gildemeesters/spec.md) | `klaar` |
| 007 | [Coaches](007-coaches/spec.md) | `klaar` (werkt als 006) |
| 008 | [Beroepsrollen](008-beroepsrollen/spec.md) | `klaar` (vervangen door 018) |
| 009 | [Semesters](009-semesters/spec.md) | `klaar` |
| 010 | [Studentenlijst](010-studentenlijst/spec.md) | `klaar` |
| 011 | [Student bewerken](011-student-bewerken/spec.md) | `klaar` |
| 012 | [Projecten](012-projecten/spec.md) | `klaar` |
| 013 | [Studenten importeren uit Excel](013-excel-importeren/spec.md) | `klaar` |
| 014 | [Alles verwijderen](014-alles-verwijderen/spec.md) | `klaar` (nog niet in de browser bekeken) |
| 015 | [Koppelen aan Portflow](015-koppelen-aan-portflow/spec.md) | `klaar` |
| 016 | [Gildes van een student](016-gildes-van-een-student/spec.md) | `klaar` |
| 017 | [Student handmatig toevoegen](017-student-handmatig-toevoegen/spec.md) | `klaar` |
| 018 | [Beroepsrol als onderdeel van het gilde](018-beroepsrol-in-gilde/spec.md) | `klaar` |

## Kandidaten

Deze onderdelen volgen uit de ontwerpen en de docs. Ze zijn nog géén spec; ze kunnen er een worden:

- **Eerste start en instellingen:** gildes van de gebruiker (de naam komt uit Portflow), rollen bij de naam ("Coach · Gildemeester"), semesterperiode, drempel "zonder recente update" ([gegevensmodel](../docs/gegevensmodel.md#gebruiker))
- **Studenten toevoegen (vervolg):** namen plakken, CSV/cellen plakken, ([gegevensmodel](../docs/gegevensmodel.md#studenten-toevoegen)); "uit Portflow kiezen" staat al in [spec 004](004-studenten-toevoegen/spec.md)
- **Studenten beheren:** het bewerken van één student staat in [spec 011](011-student-bewerken/spec.md); nog open: meerdere studenten tegelijk, de Portflow-koppeling wijzigen
- **Semesterstatus:** voldoet een student aan het toetsprogramma van zijn semester, en wat ontbreekt nog? (Volgt uit [voortgangsregels](../docs/voortgangsregels.md).)
- **Kolommen:** het beheerscherm (Projecten: [spec 012](012-projecten/spec.md), Gildes: [spec 018](018-beroepsrol-in-gilde/spec.md), Semesters: [spec 009](009-semesters/spec.md))
- **Signaalkaarten:** evaluaties te beoordelen, studenten zonder recente update, actieve coachstudenten
- **Te beoordelen:** openstaande evaluatieverzoeken aan de gebruiker, met link naar Portflow
- **Weekgrafiek:** evaluaties per week, behaald en ingediend
- **Detailpagina van een student** (later ook met HBO-i-beroepstaken)
