# 043 – Opmerkingen bij bewijsstukken

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-25

## Doel

Als **coach** of **gildemeester** wil ik in het dashboard alle feedback bij een bewijsstuk zien, ook de gewone **opmerkingen** die ik of een ander in Portflow heeft geplaatst, zodat ik niet in Portflow hoef te kijken om te weten wat er al over het werk is gezegd.

Aanleiding (gevonden door de gebruiker, 2026-11-25): bij het bewijsstuk "J4S1 Semesterroadmap" stonden in Portflow een opmerking van de coach (bij V1) en een opmerking van de student (bij V2). Het dashboard toonde ze niet. Oorzaak: [spec 035](../035-feedbackvragen/spec.md) toont alleen **feedbackvragen** van de student met hun reacties. Gewone opmerkingen (`comment_type: comment`, in Portflow "Opmerking toevoegen") worden wel opgehaald en bewaard (tabel `evidence_comments`), maar nergens getoond: niet in het zijpaneel (daar staat "Geen feedbackvragen bij dit bewijsstuk"), niet in de tijdlijn, niet op de evaluatiepagina en niet in het materiaal voor het AI-advies. In de geïnstalleerde app van de gebruiker ging het om 79 opmerkingen, waarvan 9 van coaches en docenten.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- Bewijsstuk, feedbackvraag, reactie: [begrippen.md](../../docs/begrippen.md), [spec 034](../034-bewijsstukken-tijdlijn/spec.md), [spec 035](../035-feedbackvragen/spec.md)
- **Opmerking:** een bericht bij een bewijsstuk dat geen feedbackvraag is (Portflow: `comment_type: comment`); iedereen met toegang kan er een plaatsen, en er kunnen reacties onder staan. Wordt bij het bouwen toegevoegd aan [begrippen.md](../../docs/begrippen.md).
- Rollen (medestudent, coach, gildemeester, overig): zoals in spec 035, F3

## Functionele eisen

- [x] **F1 – Versie bewaren.** Bij het ophalen ([spec 035](../035-feedbackvragen/spec.md), F1) bewaart het dashboard per opmerking en feedbackvraag ook bij welke **versie** van het bewijsstuk die hoort (Portflow: `evidence_version.version_number`, [API §4.10](../../docs/portflow-API-reverse-engineer.md)). Reacties nemen de versie van hun opmerking over als Portflow er zelf geen geeft.
- [x] **F2 – Zijpaneel.** In het zijpaneel van een bewijsstuk ([spec 037](../037-evaluaties-lezen/spec.md), F3) en van een feedbackvraag (spec 035, F4) staat onder de feedbackvragen een kopje **"Opmerkingen"** met alle opmerkingen bij dat bewijsstuk en hun reacties, oudste eerst. Per bericht: wie, rol, datum, **"bij V1"** (de versie, F1) en de tekst, als gesprek zoals bij de feedbackvragen. Ook bij de feedbackvragen komt de versie erbij. Het zijpaneel toont **alles** wat bij het bewijsstuk hoort, ook van buiten de semesterperiode. Zonder feedbackvragen én zonder opmerkingen staat er "Nog geen feedback bij dit bewijsstuk."
  - *Acceptatie:* een bewijsstuk met alleen een opmerking van de coach (bij V1) en een van de student (bij V2) toont beide onder "Opmerkingen", met rol, datum en versie; de tekst "Geen feedbackvragen bij dit bewijsstuk" staat er niet meer.
- [x] **F3 – Tijdlijn.** In de rij **"Reactie"** van de tijdlijn (spec 035, F3) komen ook de opmerkingen van **anderen dan de student zelf** (coach, gildemeester, medestudent, overig), als rondje op de dag van de opmerking, in de kleur van de rol; reacties onder een opmerking ook. Alleen uit de semesterperiode, zoals de feedbackvragen. Opmerkingen van de student bij zijn eigen werk krijgen geen rondje (zoals zijn eigen reacties nu). Een klik opent het zijpaneel van dat bewijsstuk (F2). De samenvatting bij aanwijzen zegt "Opmerking van *rol* bij *naam bewijsstuk*".
- [x] **F4 – Evaluatiepagina.** Op de pagina van één evaluatie ([spec 039](../039-evaluatie-voorbereiden/spec.md), F12) staan per gevraagde vaardigheid naast de feedbackvragen ook de opmerkingen bij de bewijsstukken van die vaardigheid, met het aantal ("2 feedbackvragen · 3 opmerkingen"); een klik opent het zijpaneel.
- [x] **F5 – AI-advies.** Het materiaal voor het AI-advies ([spec 040](../040-ai-advies-niveau/spec.md), F2) bevat ook de opmerkingen en hun reacties bij de bewijsstukken van de gevraagde vaardigheden, met de rol en de versie, en met vervangen namen (spec 040, F3). Het overzicht "Wat gaat er naar het model?" telt ze mee ("9 feedbackberichten en 4 opmerkingen").
- [x] **F6 – Kerncijfers.** De regel "N feedbackvragen · N beantwoord · N reacties · van N mensen · …" (spec 035, F2) blijft over het **vragen** om feedback gaan. Erachter komt **"· N opmerkingen van coaches en gildemeesters"** als dat er in de periode meer dan 0 zijn (opmerkingen met de rol coach, gildemeester of overig-docent; zie open vraag 2).

### Buiten scope

- Opmerkingen plaatsen of beantwoorden vanuit het dashboard.
- Opmerkingen bij iets anders dan een bewijsstuk (bijvoorbeeld bij een doel of een evaluatie).
- Bijlagen bij opmerkingen (`attachments`) openen.
- Verborgen opmerkingen (`hidden: true`) tonen.

## Schermen

Geen nieuw ontwerp: het zijpaneel, de tijdlijn en de evaluatiepagina in de stijl van spec 035 en 039. Het kopje "Opmerkingen" staat in het zijpaneel onder de feedbackvragen, met dezelfde gespreksopmaak; de versie staat als klein label ("V1") naast de datum, zoals in Portflow.

## Data

- **Bron:** de opmerkingen worden al opgehaald ([API §4.10, §4.11](../../docs/portflow-API-reverse-engineer.md)); er komen geen nieuwe aanroepen bij.
- **Nieuw bewaard:** per bericht het versienummer (kolom in `evidence_comments`). Een bestaande database krijgt de kolom bij het starten; de versie is er na de volgende keer dat de bewijsstukken van die student worden opgehaald.
- **Privacy:** niets nieuws; de teksten worden al bewaard. Namen verbergen ([spec 033](../033-namen-verbergen/spec.md)) geldt ook voor schrijvers van opmerkingen. Naar de AI gaan alleen vervangen namen (spec 040, F3).

## Technische eisen

- De keuze welke berichten waar getoond worden, staat op één plek (`feedback.py`) en heeft tests met verzonnen namen: opmerking zonder feedbackvraag, opmerking met reacties, opmerking van de student zelf, opmerking buiten de periode, verborgen opmerking.
- Een opmerking met `hidden: true` wordt niet bewaard of niet getoond (zie open vraag 3).

## Open vragen

- [x] **1. Periode.** *Gekozen 2026-11-25 (voorstel overgenomen):* in het zijpaneel altijd alles bij het bewijsstuk (ook van buiten de semesterperiode); in de tijdlijn, de kerncijfers, de evaluatiepagina en het AI-advies alleen uit de periode, zoals bij de feedbackvragen.
- [x] **2. Kerncijfers (F6).** Wil je de toevoeging "· N opmerkingen van coaches en gildemeesters", of de kerncijfers laten zoals ze zijn? *Gekozen 2026-11-25:* wel toevoegen, alleen als het er meer dan 0 zijn.
- [x] **3. Verborgen opmerkingen.** Portflow kent `hidden` bij een opmerking (waarschijnlijk alleen zichtbaar voor de schrijver). *Gekozen 2026-11-25:* niet bewaren, dus ook niet tonen en niet naar de AI sturen.

## Logboek

- 2026-11-25 – spec aangemaakt op verzoek van de gebruiker, na een gevonden fout: opmerkingen bij bewijsstukken worden opgehaald maar niet getoond. Onderzocht in de geïnstalleerde app (alleen lezend): de twee opmerkingen bij het bewijsstuk uit het voorbeeld staan in `evidence_comments` met `kind = comment`; `feedback._requests` neemt alleen `feedback_request` mee
- 2026-11-25 – voorstellen bij de open vragen overgenomen door de gebruiker; gebouwd: kolom `evidence_comments.version` (een reactie neemt de versie van haar opmerking over), verborgen opmerkingen niet bewaard (`evidence._comment`); in `feedback.py` één functie voor feedbackvragen en opmerkingen (`_threads`, `_remarks`), het zijpaneel van een bewijsstuk toont alles (ook buiten de periode) met de versie, de rij Reactie en het zijpaneel van een teken ook opmerkingen van anderen, de kerncijfers "· N opmerkingen van coaches en gildemeesters" (ook als er geen feedbackvragen zijn), de evaluatiepagina "Feedback · N feedbackvragen · N opmerkingen" en het AI-materiaal de opmerkingen met rol en versie. Tests in `tests/test_feedback.py` (TestRemarks) en `tests/test_evaluation_page.py`; in de ontwikkelversie bekeken met het bewijsstuk uit het voorbeeld: de twee opmerkingen staan in het zijpaneel met V1 en V2, en de opmerking van de coach als bolletje in de rij Reactie. De rol van de gebruiker zelf volgt de lijsten Coaches en Gildemeesters (spec 035, F3): wie in beide staat, heet daar gildemeester
