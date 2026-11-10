# 007 – Coaches

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-09

> **Bouwvolgorde:** samen met [spec 006 – Gildemeesters](../006-gildemeesters/spec.md), na [spec 005 – Gegevens ophalen](../005-gegevens-ophalen/spec.md).
>
> **Werkt als spec 006.** Deze spec noemt alleen wat anders is. Overal waar spec 006 "gildemeester" zegt, geldt hier "coach", met de verschillen die hieronder staan.

## Doel

Als **coach** of **gildemeester** wil ik de coaches beheren waarvan de evaluaties meetellen, zodat de sociale en persoonsvormende vaardigheden van mijn studenten kloppen en ik bij een student de juiste coach kan kiezen.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- Coach, coachstudent, beoordelaar ([begrippen.md](../../docs/begrippen.md))
- Filter "Mijn coachstudenten" ([gegevensmodel.md](../../docs/gegevensmodel.md#gebruiker))
- Welke evaluaties tellen ([voortgangsregels.md](../../docs/voortgangsregels.md#welke-evaluaties-tellen))

## Functionele eisen

- [x] **F1 – Menu-item.** De zijbalk krijgt het menu-item **Coaches**, direct vóór Gildemeesters (zie [spec 006, F1](../006-gildemeesters/spec.md)). Paginakop: kopje "Beheer", titel "Coaches", uitleg "Beheer de coaches van wie de evaluaties meetellen." en de primaire knop **"+ Coach toevoegen"**.
  - *Acceptatie:* het menu-item opent de pagina met deze kop.
- [x] **F2 – Kaarten, lege toestand, bewerken en verwijderen.** Als [spec 006](../006-gildemeesters/spec.md), F2, F3, F7 en F8, met "coach" in plaats van "gildemeester". Verschillen: de kaart en het formulier hebben **geen gildes**; de subregel telt de studenten bij wie de persoon als **coach** is ingevuld; verwijderen haalt alleen de rol coach weg.
  - *Acceptatie:* een coach bij 6 studenten toont "6 studenten"; verwijderen maakt bij die 6 studenten het veld coach leeg.
- [x] **F2a – De gebruiker zelf.** De naam van de gebruiker (uit Portflow, [spec 003](../003-portflow-verbinden/spec.md)) staat **automatisch** op de pagina Coaches, met het label "Jij". De gebruiker kan zichzelf verwijderen; bij een volgende keer verbinden wordt hij niet opnieuw toegevoegd.
  - *Acceptatie:* na de eerste keer verbinden staat de eigen naam met "Jij" op Coaches; na verwijderen en opnieuw verbinden niet meer.
- [x] **F3 – Toevoegen.** Dezelfde twee manieren als [spec 006](../006-gildemeesters/spec.md), F4–F6. Verschil bij "Uit Portflow kiezen": de lijst sorteert op het aantal evaluaties van **coachvaardigheden** (PL … RE), hoogste eerst, en wie al coach is, krijgt het label "Al coach".
  - *Acceptatie:* evaluaties van "A. Gilde" (5 product, 0 coach) en "B. Coach" (0 product, 7 coach) → "B. Coach" staat bovenaan.
- [x] **F4 – Coach en gildemeester tegelijk.** Wie op beide pagina's staat, krijgt op elke kaart het label "Ook gildemeester" (op de pagina Coaches) of "Ook coach" (op de pagina Gildemeesters).
  - *Acceptatie:* een persoon die op beide lijsten staat, toont op de pagina Coaches het label "Ook gildemeester".

### Buiten scope

- Een coach bij een student invullen: spec *Studenten beheren* (het vinkje "Ik ben hun coach" uit [spec 004](../004-studenten-toevoegen/spec.md) blijft werken)
- Gildemeesters: [spec 006](../006-gildemeesters/spec.md)

## Schermen

Als [spec 006](../006-gildemeesters/spec.md).

## Data

Als [spec 006](../006-gildemeesters/spec.md).

## Technische eisen

- Dezelfde tabel en code als spec 006; alleen de rol verschilt. Geen tweede kopie van de pagina's.

## Open vragen

- [x] De antwoorden bij [spec 006](../006-gildemeesters/spec.md) gelden voor beide specs. Specifiek voor coaches: de gebruiker staat er automatisch op (F2a); coaches hebben geen gildes.

## Logboek

- 2026-11-09 – spec aangemaakt op verzoek van de gebruiker
- 2026-11-09 – antwoorden verwerkt (zie spec 006); status uitgewerkt
- 2026-11-09 – gebouwd en getest; status klaar
- 2026-11-09 – het menu-item Coaches staat nu onder Beheer ([spec 002](../002-app-schil/spec.md), F17); de volgorde in F1 is daarmee vervangen
- 2026-11-10 – een coach heeft voornaam en achternaam, en de kolom Coach toont standaard de voornaam ([spec 006](../006-gildemeesters/spec.md), F20–F21)
