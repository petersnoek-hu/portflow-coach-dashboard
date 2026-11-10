# 009 – Semesters

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-09

> **Bouwvolgorde:** los te bouwen; werkt op dezelfde manier als [spec 008 – Beroepsrollen](../008-beroepsrollen/spec.md) (lijst met kaarten, zelf aanmaken of de Open-ICT-set in één keer toevoegen).

## Doel

Als **coach** of **gildemeester** wil ik de semesters van de opleiding beheren, met per semester de eisen uit het toetsprogramma, zodat ik zie hoeveel studenten in elk semester zitten en wat er in dat semester van hen gevraagd wordt.

Nu is de pagina Semesters nog een placeholder. Het semester van een student is een nummer (1–8, [gegevensmodel.md](../../docs/gegevensmodel.md#student)).

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- Semester, fase, niveau opdracht, toetsprogramma, eindniveau, BOKSA ([begrippen.md](../../docs/begrippen.md))
- Toetsprogramma: eisen per semester ([voortgangsregels.md](../../docs/voortgangsregels.md#toetsprogramma-eisen-per-semester))
- "Nog in te delen" ([gegevensmodel.md](../../docs/gegevensmodel.md#student))

## Functionele eisen

### Pagina

- [x] **F1 – Paginakop.** Het bestaande menu-item **Semesters** opent de pagina met kopje "Studievoortgang", titel "Semesters", uitleg "Bekijk de semesters, hun eisen en hoeveel studenten erin zitten." en de primaire knop **"+ Semester toevoegen"**.
  - *Acceptatie:* de pagina toont deze kop en de knop opent de pagina van F5.
- [x] **F2 – Samenvattingsbalk.** "N studenten verdeeld over M actieve semesters" (een semester is actief als er minstens één student in zit) en rechts "Iedere student is aan precies één semester gekoppeld."
  - *Acceptatie:* 7 studenten in de semesters 3, 4 en 5 → "7 studenten verdeeld over 3 actieve semesters".
- [x] **F3 – Kaarten.** Per semester een kaart, op nummer: het nummer in een gekleurd vlak, de **fase** erboven (Propedeuse, Hoofdfase of Afstudeerfase), de titel "Semester N", het aantal studenten met de avatars, en de velden die zijn ingevuld: Osiris-code, minimum niveau toetsing (LEF), niveau KPM en beheersingsniveau. Knoppen Bewerken en Verwijderen. De fase en de kleur volgen uit het nummer (F9).
  - *Acceptatie:* semester 3 met 3 studenten toont "Hoofdfase", "Semester 3", "3 studenten" en drie avatars.
- [x] **F4 – Lege toestand.** Zonder semesters: uitleg ("Nog geen semesters.") en de knop "+ Semester toevoegen". Studenten houden hun semesternummer, ook als er nog geen semesters zijn aangemaakt.
  - *Acceptatie:* 0 semesters → uitleg en knop, geen lege kaartenlijst.

### Toevoegen, bewerken, verwijderen

- [x] **F5 – Toevoegen.** "+ Semester toevoegen" opent een pagina met twee kaarten:
  - **"Zelf een semester aanmaken"**: een formulier met
    - **semesternummer** (verplicht, 1 tot en met 8),
    - **Osiris-code** (niet verplicht, bijvoorbeeld TICT-OV1SE1-26),
    - **minimum niveau toetsing (LEF)** (vrije tekst, bijvoorbeeld "4 van 10 op 1" of "3 op 3, 7 op 2"),
    - **niveau KPM** (vrije tekst, bijvoorbeeld "Minimaal KPM op 1"),
    - **beheersingsniveau** (vrije tekst, bijvoorbeeld "Taakgericht", "Probleemgericht" of "Situatiegericht");
  - **"Open-ICT-semesters toevoegen"**: voegt in één keer de 8 semesters toe uit de tabel in [voortgangsregels.md](../../docs/voortgangsregels.md#toetsprogramma-eisen-per-semester) (F6). Een semester waarvan het nummer al bestaat, wordt overgeslagen. Daarna terug naar Semesters met de bevestiging hoeveel er zijn toegevoegd.
  - *Acceptatie:* 0 semesters + "Open-ICT-semesters toevoegen" → 8 semesters; nog een keer klikken voegt er 0 toe.
- [x] **F6 – Open-ICT-semesters.** Per rij uit de tabel van het toetsprogramma:
  - nummer ← *Semester*;
  - Osiris-code ← *Code*, alleen de code zelf (bij semester 6 zonder "(keuze, minor)");
  - minimum niveau toetsing (LEF) ← *Minimum niveau toetsing (LEF)*, letterlijk (leeg bij semester 8);
  - niveau KPM ← *Niveau KPM*, letterlijk ("Nvt" bij semester 1, "BOKSA" bij semester 8);
  - beheersingsniveau ← *Niveau opdracht* als "…gericht": Taak → "Taakgericht", Probleem → "Probleemgericht", Situatie → "Situatiegericht". De kolom *Beheersingsniveau studenten* (hbo-i niveau T, P, S) wordt niet overgenomen.
  - *Acceptatie:* semester 3 krijgt TICT-OV2SE3-26, "4 op 2, 6 op 1", "Minimaal KPM op 1" en "Probleemgericht"; semester 6 krijgt TICT-OV3SE6-26.
- [x] **F7 – Controle.** Het semesternummer is een geheel getal van 1 tot en met 8 en uniek. De andere velden zijn niet verplicht. Bij een fout blijft het formulier ingevuld en staat de uitleg erbij.
  - *Acceptatie:* nummer 0, 9 of "drie" wordt geweigerd; een tweede semester 3 wordt geweigerd.
- [x] **F8 – Bewerken.** Alle velden zijn te wijzigen, met dezelfde controle als F7. Wijzigt het nummer, dan verhuizen de studenten van dat semester mee naar het nieuwe nummer.
  - *Acceptatie:* "minimum niveau toetsing" van semester 3 wijzigen → de kaart toont de nieuwe tekst; nummer 6 wijzigen in 7 (als 7 nog niet bestaat) → de studenten van semester 6 staan in semester 7.
- [x] **F9 – Fase en kleur.** De fase volgt uit het nummer ([begrippen.md](../../docs/begrippen.md)): 1–2 Propedeuse, 3–7 Hoofdfase, 8 Afstudeerfase. Elke fase heeft een vaste kleur voor het nummervlak (zie [design-system.md](../../docs/design-system.md#semesters)). Er zijn geen velden voor fase of kleur.
  - *Acceptatie:* semester 7 toont "Hoofdfase" (het ontwerp zegt ten onrechte "Afstudeerfase").
- [x] **F10 – Verwijderen.** Na bevestiging ("In semester 3 zitten 4 studenten; zij komen bij Nog in te delen.") verdwijnt het semester. Bij die studenten wordt het semester leeg.
  - *Acceptatie:* na verwijderen van semester 3 staan de 4 studenten onder "Nog in te delen".

### Buiten scope

- "Open semester →" en studenten verplaatsen tussen semesters (uit het ontwerp): spec *Studenten beheren*
- Berekenen of een student zijn semester heeft behaald op basis van deze velden: spec *Semesterstatus*. De velden hier zijn vrije tekst voor de weergave; de rekenregels staan in [voortgangsregels.md](../../docs/voortgangsregels.md#semester-behaald)
- De keuzelijst semester in de filters van het studentenoverzicht blijft 1 tot en met 8 ([spec 001](../001-studentenoverzicht/spec.md), F15)

## Schermen

| Scherm | Bestand | Opmerking |
|---|---|---|
| Semesters | [`screenshots/semesters-CRUD-met-studenten.png`](../../screenshots/semesters-CRUD-met-studenten.png) | Bevat echte namen (in `.gitignore`). Afwijkingen: zie [design-system.md](../../docs/design-system.md#semesters) |

Toevoegen en het formulier volgen de pagina's van de beroepsrollen ([spec 008](../008-beroepsrollen/spec.md), F5–F7).

## Data

- **Bron:** eigen opslag; de lijst van F5 komt uit de tabel in [voortgangsregels.md](../../docs/voortgangsregels.md#toetsprogramma-eisen-per-semester). Deze functie roept Portflow niet aan.
- **Benodigde velden:** nummer, Osiris-code, minimum niveau toetsing (LEF), niveau KPM, beheersingsniveau.
- **Privacy:** alleen avatars met initialen van studenten; lokaal.

## Technische eisen

- Een nieuwe tabel `semesters` (nummer uniek). Het semester van een student blijft een nummer in `students`; verwijderen (F10) en hernummeren (F8) passen dat nummer bij de studenten aan.
- De lijst van F5 wordt gelezen uit de tabel in `docs/voortgangsregels.md` (één bron).
- Demodata gebruikt semesters 2 tot en met 6: bij het laden voegt de demo ontbrekende Open-ICT-semesters toe, gemarkeerd als demo, en verwijdert ze weer bij het verwijderen van de demodata.
- Tests voor F5 (twee keer toevoegen), F6 (overname uit de tabel), F7 (controle), F8 (hernummeren) en F10 (studenten naar Nog in te delen).

## Open vragen

- [x] **Beheersingsniveau:** uit de kolom *Niveau opdracht*, als Taakgericht, Probleemgericht of Situatiegericht (F6). De hbo-i-niveaus (T, P, S) worden niet overgenomen.
- [x] **Start:** leeg, met een knop voor de 8 Open-ICT-semesters (F4, F5).
- [x] **Verwijderen:** studenten van dat semester komen bij "Nog in te delen" (F10).
- [x] **Fase en kleur:** volgen uit het nummer; geen extra velden (F9).

## Logboek

- 2026-11-09 – spec aangemaakt op verzoek van de gebruiker; antwoorden verwerkt; status uitgewerkt
- 2026-11-09 – gebouwd en getest (unit tests en in de browser); status klaar
