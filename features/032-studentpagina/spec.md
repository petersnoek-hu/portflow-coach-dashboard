# 032 – Overzicht van één student

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-18

## Doel

Als **coach** of **gildemeester** wil ik vanuit Overzicht of Evaluaties op een student klikken en op één pagina zien hoe die student ervoor staat: de voortgang op de tien vaardigheden, in welke weken hij welke vaardigheden en niveaus behaalde of indiende, en welke evaluaties nog openstaan. Zo kan ik een coachgesprek voorbereiden zonder in Portflow te zoeken.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- Voortgang per vaardigheid, openstaande evaluaties (`?`), eindassessment: [voortgangsregels.md](../../docs/voortgangsregels.md)
- De compacte voortgangstabel en de weekgrafiek van Evaluaties ([spec 029](../029-tijdlijn-evaluaties/spec.md)); Te beoordelen ([spec 030](../030-te-beoordelen/spec.md))

## Functionele eisen

- [x] **F1 – Naar de studentpagina.** Een klik op de naam van een student op **Overzicht** (de voortgangstabel) of op **Evaluaties** (de compacte tabel) opent de pagina van die student. Op **Studenten** blijft de naam naar **Student bewerken** gaan ([spec 022](../022-studentenlijst-inline/spec.md)); daar is geen link naar de studentpagina.
  - *Acceptatie:* een klik op een naam op Overzicht of Evaluaties opent de pagina van die student; op Studenten opent hij Student bewerken.
- [x] **F2 – Kop en tabel.** Het kruimelpad toont de naam van de student (bijvoorbeeld "Overzicht › Anna Appel"). Bovenaan staat de compacte voortgangstabel van Evaluaties ([spec 029](../029-tijdlijn-evaluaties/spec.md), F7–F11) met alleen deze student: dezelfde kolommen, cellen en details bij hover.
- [x] **F3 – Tijdlijn per vaardigheid.** Daaronder een staafgrafiek met **één staaf per week** van de semesterperiode, zoals de weekgrafiek op Evaluaties, maar opgebouwd uit **blokjes**: één blokje per evaluatie, met de code van de vaardigheid en het niveau erin ("OC 1", "PL 2"), of "?" bij een ingediende, nog niet beoordeelde evaluatie ("BD ?").
  - Behaalde blokjes onderaan, in de kleur van de categorie van de vaardigheid (product, sociaal, persoonsvormend; [design-system.md](../../docs/design-system.md#vaardigheidscategorieën-uit-lef)); ingediende blokjes erbovenop, blauw. Binnen elke groep in de volgorde OC … RE.
  - Dezelfde regels als op Evaluaties ([spec 029](../029-tijdlijn-evaluaties/spec.md), F3 en F3a): de week van indienen, startniveau telt mee, een eindassessment telt niet als tien openstaande evaluaties.
  - Bij hover over een blokje: de naam van de vaardigheid, het niveau of "ingediend", de datum en de beoordelaar of de titel van het verzoek.
  - Onder de grafiek de weeknummers met de maandag, en een legenda van de kleuren.
  - *Acceptatie:* een student met OC niveau 1 (ingediend in week 4) en een openstaand verzoek voor BD (ingediend in week 6) heeft bij W4 een blokje "OC 1" en bij W6 een blauw blokje "BD ?".
- [x] **F4 – Openstaande evaluaties.** Onderaan alle openstaande evaluaties van de student (de `?` in de tabel), per verzoek: de titel, de vaardigheden, de datum van indienen en de wachttijd. Een verzoek dat aan de gebruiker gericht is ([spec 030](../030-te-beoordelen/spec.md)), krijgt het label **"aan jou"**. Een eindassessment staat als één regel met "Assessment ingeleverd".
  - *Acceptatie:* een openstaand verzoek aan de gebruiker en een aan een andere beoordelaar staan er allebei; alleen het eerste heeft "aan jou".
- [x] **F5 – Periode.** De tabel, de tijdlijn en de openstaande evaluaties gaan over de **semesterperiode**, zoals Overzicht en Evaluaties.
- [x] **F6 – Lege toestand.** Zonder evaluaties in de periode staat er "Nog geen evaluaties in deze semesterperiode." in plaats van de tijdlijn; zonder openstaande evaluaties "Er staan geen evaluaties open." Een student die niet (meer) bestaat geeft een melding met een link naar Overzicht.
- [x] **F7 – Beoordeelde evaluaties** *(toegevoegd 2026-11-25 op verzoek van de gebruiker)*. Onder "Openstaande evaluaties" een kaart **"Beoordeelde evaluaties"** met alle evaluatieverzoeken van de student die in de semesterperiode zijn beoordeeld, de nieuwste bovenaan. Per verzoek: de titel, per vaardigheid het gegeven niveau in een neutraal label (`0` … `4`; niet in de kleuren van de niveaulabels, want die staan voor het aantal evaluaties; een beoordeling zonder niveau als "zonder niveau"), wie beoordeelde, de datum van de beoordeling en de datum van indienen. Een beoordeling door de gebruiker zelf krijgt het label **"door jou"**. Een klik opent de pagina van dat verzoek ([spec 039](../039-evaluatie-voorbereiden/spec.md)), zoals bij de openstaande evaluaties. Een eindassessment staat als één regel met "Assessment" en de niveaus. Zonder beoordelingen in de periode: "Nog geen beoordeelde evaluaties in deze semesterperiode."
  - Welke beoordelingen: alle beoordelingen (rol niet `self`) die aan een evaluatieverzoek hangen en in de periode vallen, volgens [voortgangsregels.md](../../docs/voortgangsregels.md#welke-evaluaties-tellen): elke beoordelaar telt, behalve een **uitgesloten** beoordelaar, wiens beoordelingen hier ook verborgen blijven. Een beoordeling die om een andere reden niet meetelt (geen niveau, of het verzoek is nog niet als geheel beoordeeld) staat er met **"telt niet mee"**.
  - *Acceptatie:* een student met in de periode twee beoordeelde verzoeken (PL 2 door de gebruiker op 20-11; OC 1 en KO 1 door een gildemeester op 10-11) toont twee regels, de nieuwste eerst, met de niveaulabels, de namen, de datums en bij de eerste "door jou".

### Buiten scope

- Gegevens van de student bewerken op deze pagina (dat kan bij Student bewerken, [spec 011](../011-student-bewerken/spec.md)).
- Beroepstaken (HBO-i); die staan nog niet in de lokale gegevens.
- Beoordelen; dat gebeurt in Portflow.
- Een link vanuit Te beoordelen of Studenten (niet gekozen; op Studenten opent de naam Student bewerken).
- De hele geschiedenis van eerdere semesters (niet gekozen).

## Schermen

Geen eigen ontwerp. Dezelfde onderdelen als de pagina Evaluaties ([design-system.md](../../docs/design-system.md)).

## Data

- **Bron:** alleen de lokale database (evaluaties uit [spec 005](../005-gegevens-ophalen/spec.md), verzoeken uit [spec 030](../030-te-beoordelen/spec.md)); geen Portflow-verzoeken.
- **Privacy:** alleen voor de gebruiker, lokaal.

## Technische eisen

- De voortgang en de weekindeling komen uit dezelfde code als Overzicht en Evaluaties (`progress.py`, `timeline.py`).
- Tests voor F1–F5.

## Open vragen

- [x] F7: beoordelingen door iemand die niet in de lijsten staat? Beantwoord 2026-11-25: de voortgangsregels gelden al (elke beoordelaar telt, alleen uitgesloten beoordelaars zijn verborgen); "telt niet mee" alleen bij geen niveau of een nog niet beoordeeld verzoek. De gebruiker koos "tonen met telt niet mee"; dat is zo toegepast op wat volgens de regels niet meetelt

- [x] Vorm van de tijdlijn: staven per week, opgebouwd uit blokjes per vaardigheid met het niveau (F3).
- [x] Openstaande evaluaties: alle, met het label "aan jou" (F4).
- [x] Links vanaf Overzicht en Evaluaties (F1); niet vanaf Studenten.
- [x] Periode: de semesterperiode (F5).

## Logboek

- 2026-11-18 – spec aangemaakt op verzoek van de gebruiker, met een voorstel en open vragen
- 2026-11-18 – open vragen beantwoord door de gebruiker; status uitgewerkt
- 2026-11-18 – op Studenten gaat de naam naar de studentpagina en een potlood naar Student bewerken (keuze van de gebruiker); status in bouw
- 2026-11-18 – gebouwd: route `/studenten/<id>` (`routes.student_page`), template `student.html`, gedeelde tabel `_compact_table.html`, blokjes in `timeline.student_weeks`, openstaande verzoeken in `timeline.student_open_requests` (de voortgang onthoudt nu per openstaande evaluatie het verzoek); links op Overzicht, Evaluaties en Studenten (met potlood naar Bewerken). Tests in `tests/test_student_page.py`; in de browser bekeken met echte gegevens. Status klaar
- 2026-11-18 – op verzoek van de gebruiker teruggedraaid: op Studenten opent de naam weer Student bewerken, zonder potlood en zonder link naar de studentpagina (F1)
- 2026-11-18 – uitgebreid met de tijdlijn van bewijsstukken onder de tijdlijn met evaluaties ([spec 034](../034-bewijsstukken-tijdlijn/spec.md))
- 2026-11-25 – F7 toegevoegd op verzoek van de gebruiker: een lijst met de beoordeelde evaluaties van de semesterperiode, onder de openstaande evaluaties
- 2026-11-25 – F7 gebouwd: `timeline.student_assessed_requests` (dezelfde regel `progress._counts` voor "telt niet mee"), kaart in `student.html` met `data-live`, zodat Verversen hem bijwerkt. Tests in `tests/test_student_page.py` (TestAssessed); in de ontwikkelversie bekeken met een echte student (6 beoordeelde verzoeken)
