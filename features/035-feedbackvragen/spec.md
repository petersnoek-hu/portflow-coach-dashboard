# 035 – Feedbackvragen en reacties

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-18

## Doel

Als **coach** of **gildemeester** wil ik op de pagina van één student zien hoeveel feedback hij bij zijn bewijsstukken heeft gevraagd, hoeveel reacties hij kreeg en van hoeveel verschillende mensen, en wil ik de vragen en reacties zelf kunnen lezen. Zo zie ik of de student actief feedback zoekt en wat hij ermee krijgt.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- Bewijsstuk, collectie ([spec 034](../034-bewijsstukken-tijdlijn/spec.md)); feedbackvraag (Portflow: een opmerking van het soort `feedback_request` bij een bewijsstuk) en reactie (een opmerking onder die vraag)

## Onderzoek (2026-11-18, alleen lezend)

- `GET /portfolios/{portfolio_id}/evidence/{evidence_id}/comments`: de opmerkingen op het hoogste niveau bij een bewijsstuk, met onder andere `id`, `comment_type` (`feedback_request` of `comment`), `text`, `created_at`, `created_by` (`id`, `name`, …), `created_by_role`, `child_count`.
- `GET /portfolios/{portfolio_id}/comments/{comment_id}/children`: de reacties op een opmerking, met dezelfde velden. **Niet gepagineerd:** pagina 2 geeft dezelfde reacties als pagina 1; één verzoek per vraag.
- Steekproef bij één student (60 bewijsstukken): 16 feedbackvragen, 14 beantwoord, 18 reacties van 10 verschillende mensen (allemaal met de rol student), 2 gewone opmerkingen.

## Functionele eisen

- [x] **F1 – Ophalen.** Samen met de bewijsstukken ([spec 034](../034-bewijsstukken-tijdlijn/spec.md), F1), bij het openen van de studentpagina, haalt het dashboard per bewijsstuk de feedbackvragen en hun reacties op, en bewaart lokaal per vraag en per reactie: de datum, de tekst, wie (Portflow-id en naam) en de rol. Om het aantal verzoeken te beperken, worden alleen bewijsstukken bekeken die in de semesterperiode zijn toegevoegd of bijgewerkt.
- [x] **F2 – Kerncijfers.** Bovenaan het blok "Bewijsstukken per vaardigheid" een regel: **"N feedbackvragen · N beantwoord · N reacties · van N mensen · eerste reactie gemiddeld na N dagen"**, over de vragen die in de semesterperiode zijn **gesteld** (met al hun reacties).
  - *Acceptatie:* met 3 vragen in de periode, waarvan 2 beantwoord met samen 3 reacties van 2 mensen, staat er "3 feedbackvragen · 2 beantwoord · 3 reacties · van 2 mensen".
- [x] **F3 – Twee rijen in de tijdlijn.** Onder de rijen van de vaardigheden en Overig in "Bewijsstukken per vaardigheid" komen twee rijen, zoals in The Markers:
  - **Feedbackvraag:** een ruit op de dag dat de vraag is gesteld; beantwoorde en nog niet beantwoorde vragen zijn te onderscheiden.
  - **Reactie:** een rondje op de dag van de reactie, gekleurd **naar rol**: medestudent, coach, gildemeester, overig (de rol uit Portflow, aangevuld met de lijsten Coaches en Gildemeesters).
  - Meerdere op dezelfde dag: één teken met het aantal, zoals bij de bewijsstukken. Bij hover een korte samenvatting ("Feedbackvraag bij *naam bewijsstuk* · 2 reacties").
- [x] **F4 – Zijpaneel.** Een klik op een ruit of een reactie opent rechts een **zijpaneel** met het bewijsstuk (naam, soort, vaardigheden), de feedbackvraag (wie, datum, tekst) en daaronder alle reacties als gesprek (wie, rol, datum, tekst). Sluiten met een kruisje of Esc; de grafiek blijft zichtbaar. Bij een teken met meer vragen toont het paneel ze onder elkaar.
  - *Acceptatie:* een klik op de ruit van een beantwoorde vraag toont de vraag en de reacties, in volgorde van datum.
- [x] **F5 – Namen verbergen.** Met Namen verbergen ([spec 033](../033-namen-verbergen/spec.md)) aan worden ook de namen van wie een vraag stelde of reageerde vervangen door "Student N", ook als het geen gevolgde student is; namen van coaches, gildemeesters en de gebruiker zelf blijven zichtbaar. Teksten blijven staan (een naam die alleen in een tekst voorkomt, wordt alleen vervangen als het een volledige bekende naam is).
- [x] **F6 – Lege toestand.** Zonder feedbackvragen in de periode: "Nog geen feedbackvragen in deze semesterperiode." in plaats van de kerncijfers; de twee rijen blijven dan leeg.

### Buiten scope

- Zelf reageren of feedback geven (alleen lezen).
- Gewone opmerkingen (geen feedbackvraag) in de tijdlijn; ze staan wel in het zijpaneel als ze bij het bewijsstuk horen.
- Feedbackvragen bij bewijsstukken die in de periode niet zijn toegevoegd of bijgewerkt (zie F1).

## Schermen

Geen eigen ontwerp. Rijen zoals in The Markers (getoond in de chat, 2026-11-18); het zijpaneel in de stijl van de kaarten ([design-system.md](../../docs/design-system.md)).

## Data

- **Bron:** de twee endpoints hierboven, alleen lezen; alleen bij het openen van de studentpagina.
- **Bewaard:** per vraag en reactie de datum, de **tekst** (gekozen door de gebruiker), de naam en het Portflow-id van wie en de rol.
- **Privacy:** teksten en namen staan alleen in de lokale database; "Alles verwijderen" wist ze; reservekopieën volgen de bestaande regels.

## Technische eisen

- De endpoints komen in `docs/portflow-API-reverse-engineer.md` (met de waarschuwing over de ontbrekende paginering) en `docs/architectuur.md`.
- Tests met een nep-Portflow.

## Open vragen

- [x] Teksten bewaren: ja (F1).
- [x] Namen van wie reageert ook verbergen: ja, behalve docenten en de gebruiker (F5).
- [x] Periode: vragen die in de semesterperiode zijn gesteld (F2).
- [x] Kleur van reacties: naar rol (F3).

## Logboek

- 2026-11-18 – spec aangemaakt op verzoek van de gebruiker (opties B1, B2 en A1: kerncijfers, twee rijen in de tijdlijn, zijpaneel); vragen beantwoord; status uitgewerkt
- 2026-11-18 – gebouwd: API-aanroepen met een stop als Portflow een pagina herhaalt (`portflow_api._pages_until_repeat`), tabel `evidence_comments`, ophalen samen met de bewijsstukken (zes verzoeken tegelijk), `dashboard/feedback.py` (kerncijfers, rijen, rollen, gesprekken), zijpaneel (`_feedback_panel.html`, ook als pagina zonder JavaScript), Namen verbergen voor schrijvers van vragen en reacties. Keuze bij het bouwen: reacties van de student zelf staan in het gesprek, maar tellen niet mee in de kerncijfers en heten in de grafiek "overig". Tests in `tests/test_feedback.py`; in de browser met echte gegevens: 12 feedbackvragen, 10 beantwoord, 11 reacties van 6 mensen; ophalen van één student kostte ongeveer 5 seconden. Status klaar
- 2026-11-25 – uitgebreid door [spec 043](../043-opmerkingen-bewijsstukken/spec.md): ook gewone opmerkingen bij bewijsstukken worden getoond (zijpaneel, rij Reactie, kerncijfers), met de versie van het bewijsstuk
