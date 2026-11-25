# 044 – Kleurschema van de niveaulabels

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-25

## Doel

Als **coach** of **gildemeester** wil ik kiezen wat de kleuren van de niveaulabels in de tabellen betekenen, zodat het dashboard past bij hoe mijn opleiding evalueert. Bij Open-ICT zegt de kleur hoeveel evaluaties er zijn (rood, geel, groen). Bij HCAI zijn er drie vaste **peilmomenten** (en soms een vierde na een herkansing), en daar moet de kleur laten zien **bij welk peilmoment** een niveau hoort. Wie liever geen kleuren ziet, moet die ook uit kunnen zetten.

Aanleiding: [issue #4](https://github.com/petersnoek-hu/portflow-coach-dashboard/issues/4) (vraag van een collega bij HCAI). Uit het issue:
- bij HCAI worden op elk peilmoment **alle tien** de vaardigheden bekeken;
- bij niveau 3 of 4 wordt het niveau ingevuld; bij startniveau, 1 of 2 blijft het niveau **leeg**, maar staat er wel feedback in de toelichting;
- HCAI wil in de tabel **altijd drie** waarden per vaardigheid zien (vier als er een vierde peilmoment was);
- de kleuren signaleren geen probleem; ze laten zien bij welk peilmoment een waarde hoort. Elke kleur is goed.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil. De keuze geldt voor de hele installatie (één gebruiker per laptop).

## Betrokken begrippen

- Niveaulabel, de kleuren nu: [design-system.md](../../docs/design-system.md#niveaulabels)
- Weergave per vaardigheid, openstaande evaluatie (`?`), welke evaluaties tellen: [voortgangsregels.md](../../docs/voortgangsregels.md)
- **Peilmoment** (nieuw, HCAI): een vast moment in het semester waarop alle tien de vaardigheden worden geëvalueerd; er zijn er drie, en een vierde na een herkansing. Wordt bij het bouwen toegevoegd aan [begrippen.md](../../docs/begrippen.md).
- Legenda met vinkjes: [spec 001](../001-studentenoverzicht/spec.md), F23

## Functionele eisen

- [x] **F1 – Keuze in Instellingen.** In Instellingen een sectie **"Kleuren in de tabellen"** met vier keuzes (één tegelijk), elk met een klein voorbeeldlabel:
  1. **Geen kleuren**: alle niveaulabels wit met donkere tekst, ook een openstaande evaluatie (`?`);
  2. **Geen kleuren, alleen blauw voor ingediend**: alle niveaulabels wit, behalve een cel met een openstaande evaluatie: die blijft blauw;
  3. **Open-ICT: aantal evaluaties** (standaard, zoals nu): rood = 0 evaluaties, geel = 1, groen = 2 of meer; blauw voor ingediend;
  4. **HCAI: peilmomenten**: elke waarde in de cel krijgt de kleur van zijn peilmoment: 1e = roze, 2e = geel, 3e = groen, 4e = oranje (F4, F5); blauw voor ingediend.
  De keuze wordt bewaard en geldt meteen, zonder opnieuw te verversen.
- [x] **F2 – Overal hetzelfde.** De keuze geldt voor elke tabel met vaardigheden en niveaus: **Overzicht**, de tabel op **Evaluaties**, de **pagina van een student** en de **pagina van één evaluatie** (de compacte tabel). De beoordeelde evaluaties op de studentpagina ([spec 032](../032-studentpagina/spec.md), F7) blijven neutraal.
- [x] **F3 – Legenda.** De legenda boven de tabel volgt de keuze: bij Open-ICT zoals nu (0, 1, 2 evaluaties, openstaand); bij HCAI "1e peilmoment", "2e", "3e", "4e" en "openstaand"; bij "Geen kleuren" alleen "openstaand" (als blauw) of geen legenda. De vinkjes van spec 001, F23 blijven werken per legenda-item van het gekozen schema.
- [x] **F4 – HCAI: per peilmoment een waarde.** Bij het schema HCAI toont een cel per peilmoment één waarde, in de volgorde van de peilmomenten, elk in de kleur van dat peilmoment:
  - een evaluatie met een niveau toont dat niveau (`3`, `4`, of `0`–`2` als het toch is ingevuld);
  - een evaluatie **zonder niveau** (bij HCAI: startniveau, 1 of 2, met feedback in de toelichting) toont een **streepje** `–` in de kleur van dat peilmoment, met bij aanwijzen "Peilmoment 2 · geen niveau ingevuld (startniveau, 1 of 2) · datum · beoordelaar";
  - een peilmoment dat **nog niet** is geweest, toont een lege, grijze plek, zodat er altijd drie plekken zijn (vier als er een vierde peilmoment was);
  - een openstaande evaluatie (`?`) staat op de plek van het volgende peilmoment, in blauw.
  - *Acceptatie:* een student met op peilmoment 1 geen niveau en op peilmoment 2 niveau 3 bij PL toont bij PL: roze `–`, geel `3` en een lege derde plek.
- [x] **F5 – HCAI: welk peilmoment.** Per vaardigheid zijn de evaluaties in de semesterperiode, op volgorde van datum, de peilmomenten: de eerste is peilmoment 1, de tweede peilmoment 2, enzovoort (open vraag 1). Meer dan vier: alle worden getoond, de vijfde en verder in de kleur van het vierde.
- [x] **F6 – Wat er meetelt.** Het kleurschema verandert alleen de **weergave**. Wat meetelt voor "semester behaald", de signalen en de filters blijft zoals in [voortgangsregels.md](../../docs/voortgangsregels.md#welke-evaluaties-tellen): een evaluatie zonder niveau telt niet mee, ook niet bij het schema HCAI.

### Buiten scope

- Een eigen kleur per peilmoment kiezen (de vier kleuren liggen vast).
- Een ander kleurschema per pagina of per tabel.
- De grafiek "Evaluaties per week" en de tijdlijn van bewijsstukken: die houden hun kleuren.

## Schermen

Geen nieuw ontwerp. In Instellingen een kaart met vier keuzerondjes en per keuze een voorbeeldlabel. Bij HCAI bestaat een cel uit drie (of vier) kleine vakjes naast elkaar, in de vorm van een niveaulabel; de breedte blijft gelijk voor alle rijen, zodat de kolommen netjes onder elkaar staan.

Kleuren (achtergrond / tekst, in de stijl van de bestaande labels; de definitieve waarden komen in [design-system.md](../../docs/design-system.md#niveaulabels)):

| Peilmoment | Kleur | Achtergrond | Tekst |
|---|---|---|---|
| 1e | roze | `#F6D9E6` | `#8A3B62` |
| 2e | geel | `#F2EAC1` | `#837031` |
| 3e | groen | `#DAE9DD` | `#406B52` |
| 4e | oranje | `#F8DFC8` | `#8A4F1C` |

## Data

- **Bron:** de evaluaties die al worden opgehaald ([spec 005](../005-gegevens-ophalen/spec.md)); er komen geen nieuwe aanroepen naar Portflow bij. Evaluaties zonder niveau worden al bewaard.
- **Bewaard:** de keuze, in de lokale database (instelling).
- **Privacy:** niets nieuws.

## Technische eisen

- De keuze welke kleur een waarde krijgt, en bij HCAI welk peilmoment een evaluatie is, staat op één plek (`progress.py`, naast de weergaveregels) en heeft tests.
- De weergaveregel voor HCAI komt in [voortgangsregels.md](../../docs/voortgangsregels.md#weergave-per-vaardigheid), de kleuren in [design-system.md](../../docs/design-system.md#niveaulabels).
- De kleuren via CSS-klassen per schema, zodat de vinkjes van spec 001, F23 blijven werken.

## Open vragen

- [x] **1. Welk peilmoment (F5)?** *Gekozen 2026-11-25: a, de volgorde.* Hoe weet het dashboard bij welk peilmoment een evaluatie hoort?
  - *a. Volgorde (voorstel):* per vaardigheid de eerste evaluatie in de semesterperiode is peilmoment 1, de tweede peilmoment 2, enzovoort. Geen instellingen nodig; gaat mis als een student tussendoor een losse evaluatie aanvraagt.
  - *b. Datums:* in Instellingen per peilmoment een periode (van–tot); een evaluatie hoort bij het peilmoment waarin de datum valt. Klopt altijd, maar moet elk semester worden ingevuld.
  - *c. Per verzoek:* een evaluatieverzoek met alle tien de vaardigheden is een peilmoment; losse verzoeken tellen niet als peilmoment.
- [x] **2. Lege plekken (F4):** *Gekozen 2026-11-25: altijd drie plekken, een vierde alleen als die er is.* wil HCAI voor een peilmoment dat nog niet is geweest een lege plek zien (dus altijd drie plekken), of alleen de peilmomenten die er al zijn? *Voorstel:* altijd drie lege plekken, een vierde alleen als die er is.
- [x] **3. Evaluatie zonder niveau (F6):** *Gekozen 2026-11-25: alleen zichtbaar.* bij HCAI betekent een leeg niveau "startniveau, 1 of 2". Moet zo'n evaluatie bij het schema HCAI meetellen voor "semester behaald" en de signalen, of alleen zichtbaar zijn? *Voorstel:* alleen zichtbaar; de voortgangsregels blijven gelijk.
- [x] **4. Geldt de keuze per installatie of per opleiding?** *Gekozen 2026-11-25: per installatie.* Een gebruiker die bij Open-ICT én HCAI werkt, wil misschien per groep studenten een ander schema. *Voorstel:* per installatie (één keuze voor alles); per groep kan later.
- [x] **5. "Geen kleuren" (F1, keuze 1):** *Gekozen 2026-11-25: ja.* ook het blauw van een openstaande evaluatie weg, en alleen de `?` laten zien? *Voorstel:* ja, zoals beschreven.

## Logboek

- 2026-11-25 – spec aangemaakt op verzoek van de gebruiker, op basis van [issue #4](https://github.com/petersnoek-hu/portflow-coach-dashboard/issues/4) (vier keuzes, door de gebruiker opgegeven); open vragen over het bepalen van het peilmoment, lege plekken, meetellen, per installatie en "geen kleuren"
- 2026-11-25 – open vragen beantwoord door de gebruiker (alle voorstellen): peilmoment op volgorde, altijd drie plekken, een evaluatie zonder niveau alleen zichtbaar, één keuze per installatie, bij "Geen kleuren" ook geen blauw; status uitgewerkt
- 2026-11-25 – gebouwd: instelling `level_colour_scheme` (`overview.level_scheme`, `SCHEMES`), keuze in Instellingen (`/instellingen/kleuren`), de klasse `scheme-…` op de pagina voor de kleuren, `Cell.moments` en `Cell.slots` in `progress.py` (een peilmoment telt als `_counts` zonder de eis van een niveau), vakjes per peilmoment in `_level_cell.html` met uitleg bij aanwijzen, legenda per schema met de vinkjes van spec 001, F23 (de keuze per schema blijft bewaard). Weergaveregel in [voortgangsregels.md](../../docs/voortgangsregels.md#peilmomenten), kleuren in [design-system.md](../../docs/design-system.md#niveaulabels), begrip in [begrippen.md](../../docs/begrippen.md). Tests in `tests/test_colour_scheme.py`; in de ontwikkelversie bekeken met alle vier de schema's (daarna terug op Open-ICT)
