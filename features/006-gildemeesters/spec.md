# 006 – Gildemeesters en gildes

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-10

> **Bouwvolgorde:** na [spec 005 – Gegevens ophalen](../005-gegevens-ophalen/spec.md), want de keuzelijst van F5 gebruikt de opgehaalde evaluaties. [Spec 007 – Coaches](../007-coaches/spec.md) werkt op dezelfde manier en kan in één keer mee.

## Doel

Als **coach** of **gildemeester** wil ik de gildemeesters beheren waarvan de evaluaties meetellen, zodat de productvaardigheden van mijn studenten kloppen en ik bij een student de juiste gildemeester kan kiezen.

Daarnaast wil ik de **gildes** zelf beheren (aanmaken, bewerken, verwijderen), zodat gildemeesters en studenten bij het juiste gilde horen (F12–F19).

Alleen evaluaties van beoordelaars die als coach of gildemeester bekend zijn, tellen mee ([voortgangsregels.md](../../docs/voortgangsregels.md#welke-evaluaties-tellen)). Tot nu toe stond die lijst in Instellingen en bevatte hij alleen de naam van de gebruiker; evaluaties door andere gildemeesters bleven daardoor verborgen. Deze spec geeft gildemeesters een eigen menu-item en pagina, met twee manieren om ze toe te voegen.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- Gildemeester, gilde, beoordelaar ([begrippen.md](../../docs/begrippen.md))
- Lijst met coaches en gildemeesters, filter "Mijn gildestudenten" ([gegevensmodel.md](../../docs/gegevensmodel.md#gebruiker))
- Welke evaluaties tellen ([voortgangsregels.md](../../docs/voortgangsregels.md#welke-evaluaties-tellen))

## Functionele eisen

### Menu en pagina

- [x] **F1 – Menu-item.** De zijbalk krijgt het menu-item **Gildemeesters**, na Projecten (volgorde: Overzicht, Studenten, Evaluaties, Projecten, Coaches, Gildemeesters, Kolommen, Beroepsrollen, Semesters, Instellingen). Paginakop: kopje "Beheer", titel "Gildemeesters", uitleg "Beheer de gildemeesters van wie de evaluaties meetellen." en rechts de primaire knop **"+ Gildemeester toevoegen"**.
  - *Acceptatie:* het menu-item opent de pagina met deze kop.
- [x] **F2 – Kaarten.** Per gildemeester een beheerkaart ([design-system.md](../../docs/design-system.md#componenten)): initialenavatar, naam, zijn gilde(s) als kleine labels met de code van de beroepsrol (bijvoorbeeld "FE"), subregel met het aantal studenten bij wie hij als gildemeester is ingevuld en het aantal meetellende evaluaties, avatars van die studenten, en de knoppen Bewerken en Verwijderen. Alfabetisch op naam. Bovenaan een samenvattingsbalk ("3 gildemeesters · 41 evaluaties tellen mee").
  - *Acceptatie:* een gildemeester bij 4 studenten toont "4 studenten" en vier avatars.
- [x] **F3 – Lege toestand.** Zonder gildemeesters toont de pagina uitleg ("Nog geen gildemeesters. Evaluaties van productvaardigheden tellen pas mee als hun beoordelaar hier staat.") en de knop "+ Gildemeester toevoegen".
  - *Acceptatie:* 0 gildemeesters → uitleg en knop, geen lege kaartenlijst.

### Toevoegen

- [x] **F4 – Keuze.** "+ Gildemeester toevoegen" opent een pagina met twee manieren: **"Uit Portflow kiezen"** (F5) en **"Namen typen of plakken"** (F6), als kaarten zoals bij Studenten toevoegen ([spec 004](../004-studenten-toevoegen/spec.md), F3).
  - *Acceptatie:* de pagina toont twee kaarten; elk opent zijn manier.
- [x] **F5 – Uit Portflow kiezen.** Een lijst met alle **beoordelaars** die voorkomen in de opgehaalde evaluaties van de gevolgde studenten ([spec 005](../005-gegevens-ophalen/spec.md), F2), behalve zelfevaluaties. Per beoordelaar: naam, aantal evaluaties en hoeveel daarvan productvaardigheden (OC … KPM) zijn, en de datum van de laatste. Gesorteerd op het aantal evaluaties van productvaardigheden, hoogste eerst. Met een zoekveld, "Selecteer alles" en "Selecteer niets", zoals [spec 004, F9](../004-studenten-toevoegen/spec.md). Wie al gildemeester is, staat uitgeschakeld met het label "Al gildemeester". Een knop **"X gildemeesters toevoegen"** voegt de aangevinkte namen toe en gaat terug naar Gildemeesters met een bevestiging.
  - *Acceptatie:* evaluaties van "A. Gilde" (5 product, 0 coach) en "B. Coach" (0 product, 7 coach) → "A. Gilde" staat bovenaan; na aanvinken en toevoegen staat "A. Gilde" op de pagina Gildemeesters.
  - Zijn er nog geen gegevens opgehaald, dan staat er uitleg met een verwijzing naar "Verversen" (spec 005) in plaats van een lege lijst.
- [x] **F6 – Namen typen of plakken.** Een tekstveld met één naam per regel. Lege regels en dubbele namen (zonder onderscheid tussen hoofd- en kleine letters en extra spaties) worden overgeslagen. Komt een naam niet voor als beoordelaar in de opgehaalde evaluaties, dan toont de app vóór het opslaan een waarschuwing per naam ("Nog geen evaluaties van deze naam gevonden; controleer of de naam precies zo in Portflow staat.") en kan de gebruiker toch doorgaan.
  - *Acceptatie:* drie regels "A. Gilde", "a. gilde " en een lege regel → één gildemeester toegevoegd.

- [x] **F11 – Open-ICT-gildemeesters (sept 2026).** De pagina van F4 krijgt een derde kaart **"Open-ICT-gildemeesters toevoegen"** (de lijst is die van september 2026). Die voegt in één keer de gildemeesters uit [`docs/gildemeesters-sept2026.md`](../../docs/gildemeesters-sept2026.md) toe, elk met het gilde tussen haakjes. *(Aangepast met F14:)* bestaat het gilde nog niet, dan voegt de knop eerst de ontbrekende Open-ICT-gildes uit F14 toe en koppelt daarna de gildemeesters; een code die ook geen Open-ICT-gilde is, wordt overgeslagen. Wie al in de lijst staat (ook als coach), krijgt de rol gildemeester en het gilde erbij; bestaande gildes blijven staan (F10). Een gildecode die niet (meer) als beroepsrol bestaat, wordt overgeslagen. Daarna gaat de gebruiker terug naar Gildemeesters met de bevestiging hoeveel er zijn toegevoegd. Twee keer klikken levert geen dubbele personen of gildes op.
  - *Acceptatie:* een lege lijst + de knop → 16 gildemeesters, onder wie "Peter Snoek" met gilde FE en "Rosa van Ree" met gilde AI. Is "Peter Snoek" al coach, dan staat hij daarna op beide pagina's.

### Bewerken en verwijderen

- [x] **F7 – Bewerken.** In een formulier zijn te wijzigen: de **naam** en de **gilde(s)**, nul of meer, gekozen uit de beroepsrollen ([gegevensmodel.md](../../docs/gegevensmodel.md#beroepsrol)). Na toevoegen (F5, F6) zijn de gildes leeg; de gebruiker vult ze hier in. Een gewijzigde naam geldt overal waar de persoon is ingevuld, ook als coach. Bestaat de nieuwe naam al, dan weigert de app met uitleg.
  - *Acceptatie:* "A Gilde" wijzigen in "A. Gilde" → de evaluaties van "A. Gilde" tellen mee en bij de studenten staat "A. Gilde". Gilde Frontend aanvinken → de kaart toont het label van Frontend.
  - Wordt een beroepsrol verwijderd, dan verdwijnt die ook als gilde bij de gildemeesters.
- [x] **F8 – Verwijderen.** Na bevestiging ("A. Gilde is bij 4 studenten ingevuld als gildemeester. Daar wordt het veld leeg. Zijn of haar evaluaties tellen niet meer mee, tenzij A. Gilde ook coach is.") verliest de persoon de rol gildemeester en zijn gildes. Bij de studenten wordt het veld gildemeester leeg; de studenten zelf blijven bestaan. Is de persoon ook coach, dan blijft hij op de pagina Coaches staan ([spec 007](../007-coaches/spec.md)).
  - *Acceptatie:* na verwijderen hebben de 4 studenten geen gildemeester meer en tonen hun productcellen de evaluaties van A. Gilde niet meer.

### Gebruiker en lijst

- [x] **F9 – De gebruiker zelf.** De gebruiker staat **niet** automatisch op de pagina Gildemeesters; alleen op Coaches ([spec 007](../007-coaches/spec.md), F2). Is de gebruiker ook gildemeester, dan voegt hij zichzelf toe zoals ieder ander. Op zijn eigen kaart staat dan het label "Jij".
  - *Acceptatie:* na de eerste keer verbinden is de pagina Gildemeesters leeg; na het toevoegen van de eigen naam toont die kaart het label "Jij".
- [x] **F10 – Eén persoon, twee rollen.** Een persoon staat één keer opgeslagen, met de rol coach, gildemeester of beide. Wordt een naam toegevoegd die al als coach bestaat, dan krijgt die persoon er de rol gildemeester bij; er ontstaat geen tweede persoon met dezelfde naam. Wie beide rollen heeft, toont op de kaart het label "Ook coach".
  - *Acceptatie:* "A. de Vries" is coach; toevoegen als gildemeester → één persoon met beide rollen, op beide pagina's zichtbaar, met op de pagina Gildemeesters het label "Ook coach".

### Gildes (F12–F19)

Een **gilde** heeft een korte **code** (2 of 3 hoofdletters, bijvoorbeeld BIT of TI), een **naam** (bijvoorbeeld "Front-end gilde") en een **kleur**. Bij elke beroepsrol hoort **hoogstens één gilde** en elk gilde hoort bij **precies één beroepsrol** ([gegevensmodel.md](../../docs/gegevensmodel.md#gilde)). Het gilde van een student volgt uit zijn primaire beroepsrol.

- [x] **F12 – Menu-item Gildes.** De zijbalk krijgt het menu-item **Gildes**, direct na Gildemeesters. Paginakop: kopje "Beheer", titel "Gildes", uitleg "Beheer de gildes en zie welke gildemeesters en studenten erbij horen." en de primaire knop **"+ Gilde toevoegen"**.
  - *Acceptatie:* het menu-item staat tussen Gildemeesters en Kolommen en opent de pagina met deze kop.
- [x] **F13 – Kaarten en lege toestand.** Per gilde een beheerkaart ([design-system.md](../../docs/design-system.md#componenten)): de code in een vlak met de kleur van het gilde, de naam, de beroepsrol ("Front-end developer"), de gildemeesters van dit gilde (avatars en aantal), het aantal studenten met deze primaire beroepsrol, en de knoppen Bewerken en Verwijderen. Gesorteerd op code. Zonder gildes: uitleg ("Nog geen gildes.") en de knop "+ Gilde toevoegen". **Het dashboard start zonder gildes.**
  - *Acceptatie:* een nieuw dashboard toont "Nog geen gildes."; een gilde FE met 2 gildemeesters en 5 studenten met primaire rol FE toont "2 gildemeesters" en "5 studenten".
- [x] **F14 – Toevoegen.** "+ Gilde toevoegen" opent een pagina met twee kaarten:
  - **"Zelf een gilde aanmaken"**: een formulier met code, naam, beroepsrol (keuze uit de beroepsrollen die nog geen gilde hebben; bij een code die gelijk is aan die van een beroepsrol is die rol vooringevuld) en kleur (een kleurkiezer, vooringevuld met `#909DB9`);
  - **"Open-ICT-gildes toevoegen"**: voegt in één keer de negen gildes uit [`docs/gildes-openict.md`](../../docs/gildes-openict.md) toe, elk bij de beroepsrol met dezelfde code en met de standaardkleur `#909DB9`; de kleur is daarna per gilde aan te passen (F16). Een gilde waarvan de code of beroepsrol al in gebruik is, en een code zonder bijbehorende beroepsrol, worden overgeslagen. Daarna terug naar Gildes met de bevestiging hoeveel er zijn toegevoegd.
  - *Acceptatie:* een lege lijst + "Open-ICT-gildes toevoegen" → 9 gildes, onder wie "FE · Front-end gilde" bij Front-end developer; nog een keer klikken voegt er 0 toe.
- [x] **F15 – Controle.** De code bestaat uit 2 of 3 letters en wordt als hoofdletters opgeslagen ("fe" → "FE"); hij is uniek. De naam is verplicht. Per beroepsrol hoogstens één gilde. Bij een fout blijft het formulier ingevuld en staat de uitleg erbij.
  - *Acceptatie:* code "F", "FRON" of "F1" wordt geweigerd; een tweede gilde met code FE of bij Front-end developer wordt geweigerd.
- [x] **F16 – Bewerken.** Code, naam, beroepsrol en kleur zijn te wijzigen, met dezelfde controle als F15. De gildemeesters van het gilde blijven gekoppeld.
  - *Acceptatie:* de naam van FE wijzigen in "Gilde front-end" → de kaart en de gildemeesterkaarten tonen het gewijzigde gilde.
- [x] **F17 – Verwijderen.** Na bevestiging ("Het Front-end gilde heeft 2 gildemeesters. Zij houden hun rol, maar niet meer dit gilde.") verdwijnt het gilde. Gildemeesters blijven gildemeester; alleen hun koppeling met dit gilde vervalt. Studenten en beroepsrollen blijven ongewijzigd. Wordt een beroepsrol verwijderd, dan verdwijnt ook het gilde van die rol.
  - *Acceptatie:* na verwijderen van FE staan de 2 gildemeesters nog op de pagina Gildemeesters, zonder FE.
- [x] **F18 – Gildes van een gildemeester.** De gildes van een gildemeester (F2, F7) worden gekozen uit de **gildes**, niet meer uit de beroepsrollen. De kaart toont de code van het gilde, met de naam bij hover.
  - *Acceptatie:* bij Bewerken van een gildemeester staan de gildes als keuze, met code en naam.
- [x] **F19 – Groeperen op gilde.** In het studentenoverzicht groepeert "Groeperen: Gilde" ([spec 001](../001-studentenoverzicht/spec.md), F16) op het gilde van de primaire beroepsrol, met de naam van het gilde in de groepskop. Studenten wier beroepsrol (nog) geen gilde heeft, komen onder **"Zonder gilde"**, vóór "Nog in te delen".
  - *Acceptatie:* met gilde FE bij Front-end developer staan studenten met primaire rol FE onder "FE · Front-end gilde"; zonder gildes staan ze allemaal onder "Zonder gilde".

### Voornaam en achternaam (F20–F22)

- [x] **F20 – Voornaam en achternaam.** Een persoon (gildemeester of coach, het is één persoon, F10) heeft de velden **Voornaam** en **Achternaam** in plaats van één veld Naam. Een tussenvoegsel hoort bij de achternaam ("Rosa" + "van Ree"). De volledige naam is voornaam + spatie + achternaam; die moet precies zo in Portflow staan en wordt gebruikt om beoordelaars te herkennen. Het formulier Bewerken (F7) heeft beide velden; de voornaam is verplicht. Bij toevoegen (F5, F6, F11 voor zover het bestand geen splitsing geeft) en bij de migratie van bestaande personen splitst de app de naam bij de **eerste spatie**: eerste woord = voornaam, de rest = achternaam. Daarna is dat bij Bewerken aan te passen. Kaarten en keuzelijsten tonen de volledige naam.
  - *Acceptatie:* "Rosa van Ree" toevoegen → voornaam "Rosa", achternaam "van Ree"; voornaam wijzigen in "Ros" → de volledige naam is "Ros van Ree" en alleen evaluaties van "Ros van Ree" tellen nog mee.
- [x] **F21 – Voornaam in de tabellen.** De kolommen Gildemeester en Coach in het studentenoverzicht ([spec 001](../001-studentenoverzicht/spec.md), kolomkeuze) en in de studentenlijst ([spec 010](../010-studentenlijst/spec.md), F5) heten **"Gildemeester (voornaam)"** en **"Coach (voornaam)"** en tonen alleen de voornaam. Daarnaast zijn er de kolommen **"Gildemeester (volledige naam)"** en **"Coach (volledige naam)"**, die standaard uit staan. Heeft een student meer gildemeesters, dan staan ze met komma's gescheiden en mag de cel **over meer regels lopen** (wrappen), zoals "Roland Middelweerd, Laura Rademaker".
  - *Acceptatie:* een student met gildemeesters Roland Middelweerd en Laura Rademaker toont "Roland, Laura"; na het aanzetten van "Gildemeester (volledige naam)" ook "Roland Middelweerd, Laura Rademaker", over twee regels als de kolom te smal is.
- [x] **F22 – Bestand met Open-ICT-gildemeesters.** [`docs/gildemeesters-sept2026.md`](../../docs/gildemeesters-sept2026.md) is een tabel `| Voornaam | Achternaam | Gilde |`. F11 neemt voornaam en achternaam uit het bestand over.
  - *Acceptatie:* na F11 heeft Rosa van Ree voornaam "Rosa" en achternaam "van Ree".

### Buiten scope

- De gildes van de **gebruiker** voor het filter "Mijn gildestudenten": die worden apart ingesteld (kandidaat-spec *Eerste start en instellingen*), los van de gildes op deze pagina
- Op basis van gildes een gildemeester voorstellen bij een student
- Een gildemeester bij een student invullen: spec *Studenten beheren*
- Coaches: [spec 007](../007-coaches/spec.md)

## Schermen

Geen eigen ontwerp. Volgt het patroon van de beheerschermen Projecten en Beroepsrollen ([design-system.md](../../docs/design-system.md#projecten), [`screenshots/projecten-CRUD-met-studenten.png`](../../screenshots/projecten-CRUD-met-studenten.png), bevat echte namen, in `.gitignore`). De keuzelijst van F5 volgt de lijst van [spec 004](../004-studenten-toevoegen/spec.md).

## Data

- **Bron:** eigen opslag. De namen voor F5 komen uit de lokaal bewaarde evaluaties ([spec 005](../005-gegevens-ophalen/spec.md)); deze functie roept Portflow niet zelf aan.
- **Benodigde velden:** naam (precies zoals in Portflow), of de persoon coach en/of gildemeester is, en de gildes van een gildemeester. Per gilde: code, naam en beroepsrol.
- **Privacy:** namen van medewerkers; lokaal.

## Technische eisen

- Coaches en gildemeesters staan in één tabel met personen (de bestaande tabel `staff`), met per persoon de rollen coach en gildemeester, en een koppeltabel voor de gildes. Bestaande namen in `staff` worden bij de migratie coach. Migratie bij het starten.
- De regel "bekende beoordelaar" ([voortgangsregels.md](../../docs/voortgangsregels.md#welke-evaluaties-tellen)) leest uit deze tabel, op één plek in de code.
- Namen vergelijken zonder onderscheid tussen hoofd- en kleine letters en extra spaties.
- Tests voor F5 (keuzelijst en sortering), F6 (dubbele namen), F8 (veld leeg bij studenten, rol coach blijft) en F10.
- Gildes krijgen een eigen tabel (code uniek, beroepsrol uniek, kleur). De koppeltabel `staff_guilds` verwijst voortaan naar een gilde in plaats van naar een beroepsrol; bij de migratie vervallen de bestaande koppelingen (zie *Open vragen*).
- Tests voor F14 (twee keer toevoegen), F15 (controle), F17 (gildemeesters blijven) en F19.

## Open vragen

- [x] **Eén lijst of twee:** één persoon met twee mogelijke rollen (F10). Verwijderen op een pagina haalt alleen die rol weg. De filters "Mijn coachstudenten" en "Mijn gildestudenten" in het studentenoverzicht blijven los van elkaar ([spec 001](../001-studentenoverzicht/spec.md), F14).
- [x] **Gildes:** ja, een gildemeester krijgt nu al zijn gilde(s), gekozen uit de beroepsrollen (F2, F7).
- [x] **De gebruiker zelf:** automatisch alleen op Coaches, niet op Gildemeesters (F9).
- [x] **Gildes van de gebruiker:** apart van deze pagina; ze worden ingesteld bij de *Eerste start* (zie *Buiten scope*).
- [x] **Meetellen per soort vaardigheid:** ongewijzigd. Een evaluatie van iemand op een van de twee lijsten telt mee voor alle tien vaardigheden.

- [x] **Gilde en beroepsrol:** één gilde per beroepsrol; het gilde van een student volgt uit zijn primaire beroepsrol.
- [x] **Startset:** het dashboard start zonder gildes; de negen Open-ICT-gildes zijn met één knop toe te voegen (F14).
- [x] **Bestaande koppelingen:** vervallen bij de migratie. Gildemeesters houden hun rol, maar de gebruiker kent hun gildes opnieuw toe (of gebruikt F11 opnieuw).
- [x] **Open-ICT-gildemeesters (F11) zonder gildes:** de knop voegt eerst de ontbrekende Open-ICT-gildes toe, dan de gildemeesters met hun gilde.
- [x] **Kleur van een gilde:** de gebruiker kiest die (F14, F16).
- [x] **Voornaam en achternaam (F20–F22):** geldt ook voor coaches (één persoon); de kolom Coach toont ook standaard de voornaam. Een tussenvoegsel hoort bij de achternaam. Naast de voornaamkolommen zijn er kolommen met de volledige naam, standaard uit. Bestaande en nieuwe namen worden gesplitst bij de eerste spatie. Het bestand met Open-ICT-gildemeesters krijgt aparte kolommen voor voornaam en achternaam.

## Logboek

- 2026-11-09 – spec aangemaakt op verzoek van de gebruiker
- 2026-11-09 – antwoorden verwerkt: één persoon met twee rollen, gildes per gildemeester, gebruiker alleen automatisch coach; status uitgewerkt
- 2026-11-09 – gebouwd en getest; status klaar
- 2026-11-09 – F11 toegevoegd op verzoek van de gebruiker: de Open-ICT-gildemeesters van september 2026 in één keer toevoegen
- 2026-11-09 – F11 gebouwd en getest; status klaar
- 2026-11-09 – uitgebreid met gildes (F12–F19) op verzoek van de gebruiker; status idee tot de open vragen beantwoord zijn
- 2026-11-09 – antwoorden verwerkt: bestaande koppelingen vervallen, F11 voegt ontbrekende gildes eerst toe, kleur kiest de gebruiker; status uitgewerkt (F12–F19 en de aanpassing van F11 nog te bouwen)
- 2026-11-09 – gildes (F12–F19) en de aanpassing van F11 gebouwd en getest; status klaar
- 2026-11-09 – titel van de kaart in F11 ingekort tot "Open-ICT-gildemeesters toevoegen" op verzoek van de gebruiker
- 2026-11-09 – de menu-items Gildemeesters en Gildes staan nu onder Beheer ([spec 002](../002-app-schil/spec.md), F17); de volgorde in F1 en F12 is daarmee vervangen
- 2026-11-10 – aangepast door [spec 016](../016-gildes-van-een-student/spec.md): een gildemeester hoort per gilde bij een student; de kaart telt die studenten en de rol verwijderen maakt die gildemeester bij de gildes leeg
- 2026-11-10 – F20–F22 toegevoegd op verzoek van de gebruiker: voornaam en achternaam, voornaam in de tabellen, bestand met gescheiden namen
- 2026-11-10 – F20–F22 gebouwd en getest; status klaar
- 2026-11-10 – aangepast door [spec 018](../018-beroepsrol-in-gilde/spec.md): een gilde heeft zelf een beroepsrol (naam en beschrijving) in plaats van een keuze uit de beroepsrollen (F13–F16); de Open-ICT-gildes nemen de beroepsrol mee (F14); verwijderen haalt het gilde ook bij de studenten weg (F17)
