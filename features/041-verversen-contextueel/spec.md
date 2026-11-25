# 041 – Verversen haalt alleen de studenten van het scherm op

**Status:** in bouw <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-23

## Doel

Als **coach** of **gildemeester** wil ik dat **Verversen** alleen de evaluaties ophaalt van de studenten die ik op dat moment bekijk, zodat het snel klaar is en het scherm meteen de nieuwe stand laat zien. Kijk ik op Evaluaties naar "Mijn coachstudenten" (18 studenten), dan haalt Verversen die 18 op en verder niemand.

Dit wijzigt [spec 005](../005-gegevens-ophalen/spec.md), F6 ("een ophaalronde voor alle gevolgde studenten") en [spec 019](../019-eenvoudige-start/spec.md), F14 ("alle niet-verborgen studenten, de zichtbare eerst"). Die eisen krijgen een verwijzing naar deze spec.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Voor beide hetzelfde; welke studenten zichtbaar zijn, hangt af van het filter op wie ([spec 019](../019-eenvoudige-start/spec.md), F6).

## Betrokken begrippen

- Gevolgde en verborgen studenten ([gegevensmodel.md](../../docs/gegevensmodel.md)), het filter op wie, de lijst Te beoordelen ([spec 030](../030-te-beoordelen/spec.md)).

## Functionele eisen

### Welke studenten een ronde ophaalt

- [x] **F1 – Overzicht.** Verversen haalt alleen de studenten op die in de lijst staan: na het filter op wie, de andere filters en het zoeken, in de volgorde van de lijst. Een verborgen student die in de lijst staat (bijvoorbeeld bij "Alle studenten"), wordt ook opgehaald. Hetzelfde geldt voor de lijst op **Beheer › Studenten**.
  - *Acceptatie:* met 30 studenten en het filter "Mijn coachstudenten" (18 studenten) toont de knop tijdens de ronde "Ophalen… 3 van 18 studenten"; de andere 12 houden hun bewaarde gegevens.
- [x] **F2 – Evaluaties.** Verversen haalt alleen de studenten op uit de tabel bovenaan (na het filter op wie).
  - *Acceptatie:* zoals F1, op de pagina Evaluaties.
- [x] **F3 – Eén student.** Op de **pagina van een student** ([spec 032](../032-studentpagina/spec.md)) haalt Verversen alleen die student op. Op de **pagina van één evaluatie** ([spec 039](../039-evaluatie-voorbereiden/spec.md)) alleen de student van dat verzoek.
  - *Acceptatie:* op de evaluatiepagina van een verzoek van Lotte de Vries (verzonnen naam) toont de knop "Ophalen… 0 van 1 student" en daarna de nieuwe gegevens van Lotte de Vries; andere studenten worden niet opgehaald.
- [x] **F4 – Pagina's zonder studenten.** Op andere pagina's (Instellingen, Beheer behalve Studenten, Wat is er nieuw …) haalt Verversen alle studenten op die niet verborgen zijn, zoals nu (open vraag 2, beantwoord).
- [x] **F5 – Wat elke ronde blijft doen.** Elke ronde haalt, los van de studenten van het scherm, nog steeds op:
  - de lijst met gedeelde portfolio's, zodat nieuw gedeelde studenten worden toegevoegd ([spec 019](../019-eenvoudige-start/spec.md), F1, F3). Studenten die in deze ronde nieuw zijn toegevoegd, worden **ook opgehaald**, na de studenten van het scherm, ook als ze niet op het scherm staan (open vraag 3, beantwoord);
  - de lijst **Te beoordelen** (de evaluatieverzoeken aan jou, [spec 030](../030-te-beoordelen/spec.md)).

  Dat zijn twee verzoeken aan Portflow per ronde, ongeacht het aantal studenten.
- [x] **F6 – Eerste ronde.** De allereerste ronde na het verbinden ([spec 019](../019-eenvoudige-start/spec.md), F2) haalt nog steeds alle studenten op.

### Verzoeken in Te beoordelen (toegevoegd 2026-11-25)

*Gevonden door de gebruiker: in Te beoordelen stonden verzoeken zonder vaardigheden ("–"). Bij één verzoek was de student na het indienen niet meer opgehaald: hij stond niet in de tabel op Evaluaties, dus Verversen sloeg hem over (F2). Bij drie andere verzoeken was de student wel opgehaald, maar gaf Portflow bij het verzoek geen enkele zelfevaluatie terug.*

- [x] **F9 – Studenten met een nieuw verzoek ook ophalen.** Elke ronde haalt, na de studenten van het scherm, ook de studenten op die een **openstaand verzoek aan jou** hebben dat is ingediend **na** hun laatste ophaalmoment, ook als ze niet op het scherm staan en ook als ze verborgen zijn. Dat geldt ook voor verzoeken die in deze ronde nieuw binnenkomen (de lijst Te beoordelen wordt daarvoor eerst opgehaald). Op elke pagina, niet alleen op Evaluaties. Studenten die niet in het dashboard staan, kunnen niet worden opgehaald (zoals nu, [spec 030](../030-te-beoordelen/spec.md), F3).
  - *Acceptatie:* een student die niet in de tabel op Evaluaties staat, dient na zijn laatste ophaalmoment een verzoek aan jou in; na Verversen op Evaluaties staan bij dat verzoek in Te beoordelen de vaardigheden. Een volgende Verversen haalt die student niet opnieuw op (hij is dan bij).
- [x] **F10 – Waarom er geen vaardigheden staan.** In Te beoordelen staat bij een verzoek zonder vaardigheden in plaats van alleen "–" waarom:
  - **"nog niet opgehaald"**: de student staat in het dashboard, maar is sinds het indienen nog niet opgehaald (Verversen helpt);
  - **"geen zelfevaluatie"**: de student is na het indienen opgehaald, maar Portflow gaf bij dit verzoek geen zelfevaluatie per vaardigheid; met als uitleg bij aanwijzen: "De student heeft bij dit verzoek in Portflow geen zelfevaluatie per vaardigheid ingevuld. Open het verzoek in Portflow om te zien wat er wel in staat.";
  - **"–"**: de student staat niet in het dashboard (zoals nu, spec 030, F3).
  Dezelfde tekst staat op de pagina van één evaluatie ([spec 039](../039-evaluatie-voorbereiden/spec.md)) waar nu de vaardigheden zouden staan.
  - *Acceptatie:* een verzoek van een opgehaalde student zonder zelfevaluaties toont "geen zelfevaluatie"; na een nieuw verzoek en vóór Verversen toont het "nog niet opgehaald".

### Het scherm bijwerken

- [x] **F7 – Bijwerken zonder herladen.** Elke keer dat een student van het scherm is opgehaald, werkt de pagina **zonder herladen** de gegevens van die student bij: de nieuwe getallen verschijnen op hun plek, en de rest van de pagina blijft staan. De scrollpositie, een open zijpaneel, opengeklapte onderdelen en tekst die de gebruiker aan het typen is (bijvoorbeeld een vraag aan de AI) blijven zoals ze zijn. Is de ronde klaar, dan worden ook de onderdelen bijgewerkt die over meer studenten gaan (de lijst Te beoordelen, de teller "Evaluaties" in de zijbalk, de tellers onder de tabel).
  - Overzicht: de rij van de student in de tabel.
  - Evaluaties: de rij in de tabel bovenaan, de grafiek met evaluaties per week en de lijst Te beoordelen.
  - Pagina van een student: de stand van zaken, de grafiek per week en de openstaande evaluaties. Pagina van één evaluatie: de kop (wacht sinds, aan jou, vorige/volgende), de stand van zaken, de grafiek, de toelichting en per vaardigheid de niveaus, de zelfevaluatie en de eerdere evaluaties. Bewijsstukken en feedbackvragen niet: een ronde haalt die niet op (ze worden per student opgehaald, [spec 034](../034-bewijsstukken-tijdlijn/spec.md)). Het AI-advies en wat de gebruiker daar typt, blijven ongemoeid.
  - Ook de klik op Verversen herlaadt de pagina niet: een zoekopdracht in de tabel, de scrollpositie en opengeklapte onderdelen blijven staan.
  - Lukt bijwerken zonder herladen niet, dan herlaadt de pagina na afloop één keer. Zonder JavaScript werkt Verversen als formulier, zoals voorheen; de gebruiker herlaadt dan zelf.
  - Een student die in deze ronde nieuw is toegevoegd en op het scherm komt, verschijnt na afloop met één keer herladen (een nieuwe rij kan niet in de tabel worden geschoven zonder het sorteren en filteren te verstoren).
  - *Acceptatie:* op Evaluaties met 18 studenten verandert tijdens de ronde de rij van elke opgehaalde student, zonder dat de pagina verspringt; na afloop staan de nieuwe verzoeken in Te beoordelen.
- [x] **F8 – Wat de knop zegt.** *Gewijzigd 2026-11-23 op verzoek van de gebruiker; eerst stond het aantal studenten erin ("18 studenten bijgewerkt om 14:32").* Na afloop toont de knop zoals voorheen alleen de tijd: **"Bijgewerkt om 14:32"**. Tijdens de ronde staat er "Ophalen… 3 van 18 studenten" (bij één student "0 van 1 student"). Mislukte studenten worden gemeld zoals nu ([spec 005](../005-gegevens-ophalen/spec.md), F12).
- [x] **F9 – Ronde loopt al.** Tijdens een ronde blijft de knop uitgeschakeld (zoals nu). Gaat de gebruiker tijdens de ronde naar een andere pagina, dan loopt de ronde door voor de studenten waarmee hij begon.

### Buiten scope

- Automatisch verversen op de achtergrond of bij het openen van een pagina.
- Per student een eigen knop "Verversen".
- Bewijsstukken: die worden al per student opgehaald op de studentpagina ([spec 034](../034-bewijsstukken-tijdlijn/spec.md)); daar verandert niets aan.

## Schermen

Geen nieuwe schermen; alleen de knop Verversen in de bovenbalk ([design-system.md](../../docs/design-system.md)) krijgt een andere tekst na afloop (F8).

## Data

- **Bron:** Portflow API, zoals in [spec 005](../005-gegevens-ophalen/spec.md); geen nieuwe endpoints.
- **Verversen:** handmatig, per scherm.
- **Privacy:** geen verandering; er wordt minder opgehaald.

## Technische eisen

- **Bijwerken zonder herladen (F7):** app.js verstuurt Verversen op de achtergrond (de server antwoordt dan `204`) en volgt de ronde via de statuscontrole. Na elke opgehaalde student die op het scherm staat, haalt app.js dezelfde pagina op de achtergrond opnieuw op (`fetch`) en vervangt alleen de onderdelen met `data-live` (de vaardigheidscellen `cell-<student>-<code>`, `weeks`, `week-chart`, `to-review`, `student-open`, `nav-count`, de onderdelen `eval-…` van de evaluatiepagina) die anders zijn dan wat de server eerder stuurde. De HTML blijft dus op één plek gemaakt, door de server, met dezelfde voortgangsregels; JavaScript rekent niets zelf uit. Een onderdeel waarin de gebruiker typt, wordt overgeslagen; opengeklapte onderdelen blijven open. Wrappers hebben de klasse `live` (`display: contents`), zodat de opmaak niet verandert.
- De pagina stuurt de studenten van het scherm mee bij Verversen (dat doet app.js al voor Overzicht, Evaluaties, de studentpagina en de evaluatiepagina, via de rijen met `data-student-id`). De server haalt voortaan **alleen** die studenten op, plus wat F5 en F6 noemen; de rest van de lijst valt weg uit de ronde.
- Stuurt een pagina geen studenten mee, dan geldt F4.
- Tests in `tests/` voor F1–F6 en F8 (welke studenten een ronde ophaalt, de tekst na afloop).

## Open vragen

- [x] **1. Bewust terug naar "alleen zichtbaar"?** Beantwoord 2026-11-23: ja, alleen de studenten van het scherm. Studenten buiten het scherm houden hun oude gegevens tot de gebruiker ze bekijkt en ververst.
- [x] **2. Pagina's zonder studenten (F4).** Beantwoord 2026-11-23: iedereen ophalen die niet verborgen is, zoals nu.
- [x] **3. Nieuw gedeelde studenten (F5).** Beantwoord 2026-11-23: ja, hun evaluaties meteen ophalen.
- [x] **4. Bijwerken zonder herladen (F7).** Beantwoord 2026-11-23: ja, na elke opgehaalde student, zonder herladen; alleen de veranderde onderdelen worden vervangen.

## Logboek

- 2026-11-23 – spec aangemaakt op verzoek van de gebruiker: Verversen haalt alleen de studenten van het scherm op (Overzicht, Evaluaties, de pagina van een student, de pagina van één evaluatie) en werkt het scherm daarna bij. Wijzigt spec 005, F6 en spec 019, F14. Open vragen voorgelegd
- 2026-11-23 – open vragen 1–3 beantwoord door de gebruiker (alleen het scherm; op pagina's zonder studenten iedereen; nieuw gedeelde studenten meteen ophalen). Op vraag 4 vroeg de gebruiker of bijwerken zonder herladen kan; F7 herschreven als voorstel: na elke student alleen zijn onderdelen vervangen, via de pagina op de achtergrond ophalen
- 2026-11-23 – open vraag 4 beantwoord: bijwerken zonder herladen, per student. Status uitgewerkt
- 2026-11-23 – gebouwd: `Fetcher.start(…, screen=True)` en de route `/portflow/verversen` (`scherm=1`, 204 bij een verzoek uit app.js) halen alleen de studenten van het scherm op, plus nieuw toegevoegde; zonder scherm iedereen (F4), de eerste ronde iedereen (F6). De knop toont "18 studenten bijgewerkt om …" (`S_LAST_FETCH_COUNT`) en tijdens de ronde "0 van 1 student". app.js verstuurt Verversen op de achtergrond en vervangt na elke student de veranderde `data-live`-onderdelen; de oude herlaad-markeringen (`data-reload-when-fetched`, `data-reload-after-fetch` op de tabel) zijn vervallen, alleen een lege Overzicht herlaadt nog. F7 aangepast op wat een ronde ophaalt (geen bewijsstukken) en wat er gebeurt bij een nieuwe rij. Tests in `tests/test_simple_start.py` en `tests/test_fetch.py`. In de ontwikkelversie gecontroleerd: Overzicht met "Mijn coachstudenten" en zoekterm "an" haalde 7 studenten op, zonder herladen (zoekterm bleef staan, 7 keer op de achtergrond bijgewerkt, daarna "7 studenten bijgewerkt om 15:11"); de evaluatiepagina haalde 1 student op. Niet zichtbaar gecontroleerd dat een veranderde cel wisselt, omdat de gegevens in Portflow niet veranderd waren; dat doen de tests ook niet (JavaScript wordt niet getest). Status in bouw tot de gebruiker het heeft gezien
- 2026-11-23 – F8 gewijzigd op verzoek van de gebruiker: de knop toont na afloop weer alleen "Bijgewerkt om 15:22", zonder het aantal studenten
- 2026-11-25 – op verzoek van de gebruiker uitgebreid na een fout in Te beoordelen: studenten met een nieuw verzoek aan jou worden in elke ronde ook opgehaald (F9), en bij een verzoek zonder vaardigheden staat waarom (F10). Onderzocht met de geïnstalleerde app: bij één verzoek was de student niet opnieuw opgehaald; bij drie verzoeken gaf Portflow in geen enkel doel een zelfevaluatie met dat verzoeknummer (de doelen zelf gaven gewoon antwoord)
- 2026-11-25 – gebouwd: F9 en F10. `requests_to_review.students_behind` (studenten met een openstaand verzoek aan de gebruiker dat nieuwer is dan hun `fetched_at`) en `no_skills_reason`; de ophaalronde haalt nu eerst de verzoeken op en zet die studenten achteraan in de ronde (ook verborgen studenten). Te beoordelen en de evaluatiepagina tonen "nog niet opgehaald" of "geen zelfevaluatie" met uitleg bij aanwijzen. Tests in `tests/test_to_review.py`; in de ontwikkelversie bekeken: de drie verzoeken zonder zelfevaluatie tonen "geen zelfevaluatie". F9 is alleen met tests nagekeken, niet met een echte ronde
