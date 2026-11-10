# 008 – Beroepsrollen

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-09

> **Bouwvolgorde:** na [spec 006 – Gildemeesters en gildes](../006-gildemeesters/spec.md); een gilde hoort bij een beroepsrol, en deze spec werkt op dezelfde manier als de gildes daar (F12–F17).

## Doel

Als **coach** of **gildemeester** wil ik de beroepsrollen beheren: zelf aanmaken, bewerken en verwijderen, of de negen beroepsrollen van Open-ICT in één keer toevoegen. Zo kloppen de profielen van mijn studenten en kan ik bij elke rol een gilde maken.

Nu maakt de app de negen rollen bij elke start vanzelf aan, en een verwijderde rol komt terug. De pagina Beroepsrollen is nog een placeholder.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- Beroepsrol, primair en secundair, gilde ([begrippen.md](../../docs/begrippen.md), [beroepsrollen.md](../../docs/beroepsrollen.md))
- Velden van een beroepsrol, "Nog in te delen" ([gegevensmodel.md](../../docs/gegevensmodel.md#beroepsrol))
- Gilde: één per beroepsrol ([gegevensmodel.md](../../docs/gegevensmodel.md#gilde))

## Functionele eisen

### Pagina

- [x] **F1 – Paginakop.** Het bestaande menu-item **Beroepsrollen** opent de pagina met kopje "Opleidingsprofiel", titel "Beroepsrollen", uitleg "Beheer rollen en zie direct welke studenten primair of secundair gekoppeld zijn." en de primaire knop **"+ Beroepsrol toevoegen"** (het ontwerp zegt "Nieuwe beroepsrol"; "+ … toevoegen" past bij de andere beheerpagina's).
  - *Acceptatie:* de pagina toont deze kop en de knop opent de pagina van F5.
- [x] **F2 – Samenvattingsbalk.** Bovenaan: het aantal beroepsrollen, het aantal studenten met een primaire rol ("studenten gekoppeld") en de zin "Iedere student heeft precies één primaire rol; secundaire rollen zijn optioneel."
  - *Acceptatie:* 9 rollen en 7 studenten met een primaire rol → "9 Beroepsrollen" en "7 Studenten gekoppeld".
- [x] **F3 – Kaarten.** Per beroepsrol een beheerkaart, gesorteerd op code: de code in een vlak met de kleur van de rol, de naam, de beschrijving (als die er is), het gilde van de rol als klein label (als dat er is, [spec 006](../006-gildemeesters/spec.md)), de tellers **"N primair"** en **"N secundair"**, de avatars van de studenten met deze rol, en de knoppen Bewerken en Verwijderen.
  - *Acceptatie:* een rol FE met 3 primaire en 1 secundaire student toont "3 primair", "1 secundair" en vier avatars.
- [x] **F4 – Lege toestand.** Zonder beroepsrollen: uitleg ("Nog geen beroepsrollen.") en de knop "+ Beroepsrol toevoegen".
  - *Acceptatie:* 0 rollen → uitleg en knop, geen lege kaartenlijst.

### Toevoegen, bewerken, verwijderen

- [x] **F5 – Toevoegen.** "+ Beroepsrol toevoegen" opent een pagina met twee kaarten:
  - **"Zelf een beroepsrol aanmaken"**: een formulier met code, naam, korte beschrijving (niet verplicht) en kleur (een kleurkiezer, vooringevuld met `#909DB9`);
  - **"Open-ICT-beroepsrollen toevoegen"**: voegt in één keer de negen beroepsrollen uit [`docs/beroepsrollen.md`](../../docs/beroepsrollen.md) toe, met code en naam, een lege beschrijving en de standaardkleur. Een rol waarvan de code al bestaat, wordt overgeslagen. Daarna terug naar Beroepsrollen met de bevestiging hoeveel er zijn toegevoegd.
  - *Acceptatie:* 0 rollen + "Open-ICT-beroepsrollen toevoegen" → 9 rollen, onder wie "FE · Front-end developer"; nog een keer klikken voegt er 0 toe.
- [x] **F6 – Controle.** De code bestaat uit 2 of 3 letters en wordt als hoofdletters opgeslagen; hij is uniek. De naam is verplicht. Bij een fout blijft het formulier ingevuld en staat de uitleg erbij.
  - *Acceptatie:* code "F", "FRON" of "F1" wordt geweigerd; een tweede rol met code FE wordt geweigerd; "fe" wordt "FE".
- [x] **F7 – Bewerken.** Code, naam, beschrijving en kleur zijn te wijzigen, met dezelfde controle als F6. Studenten en het gilde blijven aan de rol gekoppeld.
  - *Acceptatie:* de naam van FE wijzigen in "Frontend developer" → de kaart, het studentenoverzicht (Profiel, filter) en de gildekaart tonen de nieuwe naam.
- [x] **F8 – Verwijderen.** Na bevestiging verdwijnt de rol. De bevestiging noemt de gevolgen, bijvoorbeeld: "Front-end developer is de primaire rol van 3 studenten; zij komen bij Nog in te delen. Bij 1 student verdwijnt deze secundaire rol. Het Front-end gilde wordt ook verwijderd." ([gegevensmodel.md](../../docs/gegevensmodel.md#beroepsrol), [spec 006, F17](../006-gildemeesters/spec.md)).
  - *Acceptatie:* na verwijderen van FE staan de 3 studenten onder "Nog in te delen", heeft de student met FE als secundaire rol die rol niet meer, en is het gilde FE weg.

### Start

- [x] **F9 – Leeg starten.** Een nieuw dashboard start **zonder beroepsrollen**; de app maakt ze niet meer vanzelf aan. Een bestaande database houdt zijn rollen. Een verwijderde rol komt bij een herstart niet terug.
  - *Acceptatie:* een nieuwe database heeft 0 rollen; na het verwijderen van FE en een herstart is FE er nog steeds niet.
- [x] **F10 – Gildes zonder rollen.** Zijn er nog geen beroepsrollen, dan tonen de pagina's Gilde toevoegen en Gilde aanmaken ([spec 006](../006-gildemeesters/spec.md), F14) de uitleg "Voeg eerst beroepsrollen toe." met een link naar de pagina van F5.
  - *Acceptatie:* 0 rollen → op Gilde toevoegen staat de uitleg met de link.

### Buiten scope

- "Studenten beheren →" op de kaart (uit het ontwerp) en de beroepsrollen van een student wijzigen: spec *Studenten beheren*
- Beschrijvingen voor de Open-ICT-rollen: die vult de gebruiker zelf in (F7)
- Samenhang met de HBO-i-beroepstaken ([beroepsrollen.md](../../docs/beroepsrollen.md), open vraag)

## Schermen

| Scherm | Bestand | Opmerking |
|---|---|---|
| Beroepsrollen | [`screenshots/beroepsrollen-CRUD-met-studenten.png`](../../screenshots/beroepsrollen-CRUD-met-studenten.png) | Bevat echte namen (in `.gitignore`). Afwijkingen: zie [design-system.md](../../docs/design-system.md#beroepsrollen) en F1, F3 |

Toevoegen en het formulier volgen de pagina's van de gildes ([spec 006](../006-gildemeesters/spec.md), F14–F16).

## Data

- **Bron:** eigen opslag; de lijst van F5 komt uit de tabel in [`docs/beroepsrollen.md`](../../docs/beroepsrollen.md). Deze functie roept Portflow niet aan.
- **Benodigde velden:** code, naam, korte beschrijving, kleur.
- **Privacy:** alleen avatars met initialen van studenten; lokaal.

## Technische eisen

- De tabel `professional_roles` krijgt een kolom `color`; migratie bij het starten. Het automatisch invoegen van de negen rollen bij elke start vervalt.
- De lijst van F5 wordt gelezen uit de tabel in `docs/beroepsrollen.md` (één bron); de vaste lijst `DEFAULT_ROLES` in de code vervalt.
- Demodata gebruikt beroepsrollen: bij het laden voegt de demo ontbrekende Open-ICT-rollen toe, gemarkeerd als demo, en verwijdert ze weer bij het verwijderen van de demodata (zoals de demo-gildes).
- Tests voor F5 (twee keer toevoegen), F6 (controle), F8 (studenten naar Nog in te delen, secundaire rol weg, gilde weg) en F9 (geen rollen na herstart).

## Open vragen

- [x] **Start:** leeg, met een knop voor de negen Open-ICT-rollen (F5, F9). Een bestaande database houdt zijn rollen.
- [x] **Kleur:** de gebruiker kiest die, net als bij gildes (F5, F7).
- [x] **Beschrijving van de Open-ICT-rollen:** leeg; de gebruiker vult ze later in.

## Logboek

- 2026-11-09 – spec aangemaakt op verzoek van de gebruiker; antwoorden verwerkt; status uitgewerkt
- 2026-11-09 – gebouwd en getest (unit tests en in de browser); status klaar
- 2026-11-10 – aangepast door [spec 016](../016-gildes-van-een-student/spec.md): de kaart toont "N studenten" (geen primair/secundair meer); verwijderen haalt het gilde bij de studenten weg
