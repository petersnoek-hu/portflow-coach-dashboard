# 012 – Projecten

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-09

> **Bouwvolgorde:** los te bouwen; werkt zoals de andere beheerpagina's ([spec 008](../008-beroepsrollen/spec.md), [spec 009](../009-semesters/spec.md)). Nodig om bij [spec 011 – Student bewerken](../011-student-bewerken/spec.md) een project te kunnen kiezen.

## Doel

Als **coach** of **gildemeester** wil ik de projecten (squads) beheren: zelf aanmaken, bewerken en verwijderen, of de Open-ICT-projecten van september 2026 in één keer toevoegen. Zo kan ik studenten in hun project indelen en zie ik per project wie erin zit.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- Squad, in de interface **project** ([begrippen.md](../../docs/begrippen.md), [gegevensmodel.md](../../docs/gegevensmodel.md#squad-project)); "Zonder project"

## Functionele eisen

### Pagina

- [x] **F1 – Paginakop.** Het menu-item **Projecten** (onder Beheer) opent de pagina met kopje "Beheer", titel "Projecten", uitleg "Beheer de projectgroepen waarin je studenten zijn ingedeeld." en de primaire knop **"+ Nieuw project"**.
  - *Acceptatie:* de pagina toont deze kop en de knop opent de pagina van F5.
- [x] **F2 – Samenvattingsbalk.** "N actieve projecten" (projecten met minstens één student), "M studenten" (met een project) en "K zonder project".
  - *Acceptatie:* 3 projecten met studenten, 7 studenten met en 2 zonder project → "3 actieve projecten", "7 studenten", "2 zonder project".
- [x] **F3 – Kaarten.** Per project een kaart, op nummer (projecten zonder nummer daarna, op naam): de initialen van de naam in een vlak met de kleur van het project, de naam, de volledige naam ("02 Gamified Learning", of alleen de naam zonder nummer), de opdrachtgever (als die er is), de avatars van de studenten en "N studenten", en de knoppen Bewerken en Verwijderen. Na de kaarten een kaart met stippellijn **"Project toevoegen"** ("Maak een nieuwe groep voor studenten") die naar F5 leidt.
  - *Acceptatie:* project 02 "Gamified Learning" van "Condor Arnhem OT" met 2 studenten toont "GL", "02 Gamified Learning", "Condor Arnhem OT" en "2 studenten".
- [x] **F4 – Zonder project en lege toestand.** Onder de kaarten een balk **"Zonder project"** ("Studenten blijven hier zichtbaar nadat een project is verwijderd.") met het aantal studenten zonder project en hun avatars. Zonder projecten toont de pagina uitleg ("Nog geen projecten.") en de knop "+ Nieuw project".
  - *Acceptatie:* 0 projecten → uitleg en knop; 2 studenten zonder project → de balk toont "2 studenten".

### Toevoegen, bewerken, verwijderen

- [x] **F5 – Nieuw project.** "+ Nieuw project" opent een pagina met twee kaarten:
  - **"Handmatig toevoegen"**: een formulier met
    - **nummer** (niet verplicht; 1 of 2 cijfers, opgeslagen als twee cijfers: "2" → "02"),
    - **naam** (verplicht),
    - **opdrachtgever** (niet verplicht),
    - **kleur** (een kleurkiezer, vooringevuld met de volgende kleur uit de reeks van F6);
  - **"Open-ICT-projecten (sept 2026) toevoegen"**: voegt in één keer de projecten uit [`docs/openict-projecten.md`](../../docs/openict-projecten.md) toe, met nummer, naam en opdrachtgever. Een project waarvan het nummer al bestaat, wordt overgeslagen. Daarna terug naar Projecten met de bevestiging hoeveel er zijn toegevoegd.
  - *Acceptatie:* 0 projecten + "Open-ICT-projecten (sept 2026) toevoegen" → 19 projecten (01 tot en met 20, zonder 09); nog een keer klikken voegt er 0 toe.
- [x] **F6 – Kleuren.** De Open-ICT-projecten krijgen om de beurt een kleur uit een vaste reeks van acht ontwerpkleuren ([design-system.md](../../docs/design-system.md#projecten)), zodat ze in de tabellen van elkaar te onderscheiden zijn. De kleur is daarna per project aan te passen (F8).
  - *Acceptatie:* na het toevoegen hebben project 01 en 02 een verschillende kleur; de kleuren volgen de reeks in de volgorde van de tabel.
- [x] **F7 – Controle.** De naam is verplicht. Een nummer bestaat uit 1 of 2 cijfers en is uniek. Bij een fout blijft het formulier ingevuld en staat de uitleg erbij.
  - *Acceptatie:* een lege naam, nummer "123" of "a1" en een tweede project 02 worden geweigerd.
- [x] **F8 – Bewerken.** Nummer, naam, opdrachtgever en kleur zijn te wijzigen, met dezelfde controle als F7. De studenten blijven in het project.
  - *Acceptatie:* de naam van 02 wijzigen in "Gamified Learning 2" → de kaart, het studentenoverzicht (groepskop, filter) en de studentenlijst tonen de nieuwe naam.
- [x] **F9 – Verwijderen.** Na bevestiging ("In 02 Gamified Learning zitten 3 studenten; zij komen bij Zonder project.") verdwijnt het project. De studenten blijven bestaan, zonder project ([gegevensmodel.md](../../docs/gegevensmodel.md#squad-project)).
  - *Acceptatie:* na verwijderen staan de 3 studenten in de balk "Zonder project" en in het studentenoverzicht onder "Zonder project".

### Buiten scope

- Studenten in een project indelen: [spec 011](../011-student-bewerken/spec.md) (per student)
- Studenten tussen projecten verslepen of meerdere tegelijk verplaatsen
- Een coach per project (alle studenten in een squad hebben dezelfde coach, [begrippen.md](../../docs/begrippen.md)): niet afgedwongen

## Schermen

| Scherm | Bestand | Opmerking |
|---|---|---|
| Projecten | [`screenshots/projecten-CRUD-met-studenten.png`](../../screenshots/projecten-CRUD-met-studenten.png) | Bevat echte namen (in `.gitignore`). Afwijkingen: zie [design-system.md](../../docs/design-system.md#projecten) |

Nieuw project en het formulier volgen de pagina's van de beroepsrollen ([spec 008](../008-beroepsrollen/spec.md), F5–F7).

## Data

- **Bron:** eigen opslag; de lijst van F5 komt uit de tabel in [`docs/openict-projecten.md`](../../docs/openict-projecten.md). Deze functie roept Portflow niet aan.
- **Benodigde velden:** nummer, naam, opdrachtgever, kleur. De initialen en de volledige naam ("NN naam") volgen daaruit.
- **Privacy:** alleen avatars met initialen van studenten; lokaal.

## Technische eisen

- De tabel `squads` krijgt de kolommen `number` en `client`; `full_name` wordt afgeleid ("NN naam"). Migratie bij het starten: bij bestaande projecten wordt het nummer uit de volledige naam gehaald ("04 Horizon" → 04, "Horizon").
- De lijst van F5 wordt gelezen uit de tabel in `docs/openict-projecten.md` (één bron).
- Demodata: de demo-projecten krijgen ook een nummer en een opdrachtgever.
- Tests voor F5 (twee keer toevoegen, 19 projecten), F7 (controle), F8 (naam elders zichtbaar) en F9 (studenten naar Zonder project).

## Open vragen

- [x] **Bestand:** omgezet naar een tabel `| Nr | Projectnaam | Opdrachtgever |`; dubbele spaties opgeschoond.
- [x] **Inhoud:** "Beveligingstest team" verbeterd in "Beveiligingstest team". Nummers hoeven niet oplopend te zijn (een project kan op het laatste moment niet doorgaan); zie de uitleg in het bestand.
- [x] **Velden:** nummer (niet verplicht), naam, opdrachtgever (niet verplicht) en kleur; initialen en volledige naam volgen daaruit.
- [x] **Kleur:** de Open-ICT-projecten krijgen om de beurt een kleur uit een vaste reeks (F6).

## Logboek

- 2026-11-09 – spec aangemaakt op verzoek van de gebruiker; `docs/openict-projecten.md` omgezet naar een tabel; antwoorden verwerkt; status uitgewerkt
- 2026-11-09 – gebouwd en getest (unit tests en in de browser); status klaar. Initialen: eerste en laatste woord, bij één woord de eerste twee letters ("Beheerteam" → BE)
