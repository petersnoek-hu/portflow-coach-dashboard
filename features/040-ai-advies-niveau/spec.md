# 040 – AI-advies bij een evaluatie

**Status:** in bouw <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-24

## Doel

Als **coach** of **gildemeester** wil ik een evaluatieverzoek aan een AI kunnen voorleggen en per gevraagde vaardigheid een advies over het niveau krijgen. Dan heb ik een tweede blik als ik mijn eigen beoordeling maak. Het advies is hulp en geen oordeel: de beoordeling blijft van de coach of gildemeester, en die geeft hem in Portflow.

De AI draait **lokaal op de laptop** (Ollama). Er gaan dus geen studentgegevens van de laptop af.

Bouwt voort op de evaluatiepagina van [spec 039](../039-evaluatie-voorbereiden/spec.md); het advies staat onderaan die pagina.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil. Het advies gaat over **alle** gevraagde vaardigheden, en bij elke staat wie hem beoordeelt ([vaardigheden-openict.md](../../docs/vaardigheden-openict.md)).

## Betrokken begrippen

- Vaardigheden en niveaus: [vaardigheden-niveaus-LEF.md](../../docs/vaardigheden-niveaus-LEF.md). De LEF-teksten zijn de maatstaf voor het advies.
- Evaluatieverzoek, zelfevaluatie, bewijsstuk: [begrippen.md](../../docs/begrippen.md)
- Namen verbergen: [spec 033](../033-namen-verbergen/spec.md)

## Functionele eisen

- [x] **F1 – Advies vragen.** Onderaan de evaluatiepagina ([spec 039](../039-evaluatie-voorbereiden/spec.md)) staat een blok **"Advies (AI)"** met de knop **"AI-advies vragen"**. Pas na die klik gaat er iets naar het model.
- [x] **F2 – Wat er meegaat.** Boven de knop staat wat er naar het model gaat. Een klik toont het overzicht met aantallen ("zelfevaluatie, 2 vaardigheden, 6 bewijsstukken waarvan 3 bestanden, 4 eerdere beoordelingen, 9 feedbackberichten"). Er gaat mee:
  - de toelichting en de zelfevaluatie per gevraagde vaardigheid, met het niveau dat de student aangeeft;
  - de LEF-teksten van alle niveaus van de gevraagde vaardigheden;
  - per gevraagde vaardigheid de bewijsstukken in de semesterperiode: de tekst van tekst-bewijsstukken en de inhoud van bestanden (zie F7);
  - eerdere beoordelingen van die vaardigheden: niveau, datum en tekst;
  - de feedbackvragen en reacties op die bewijsstukken.
- [x] **F3 – Namen vervangen.** Vóór het versturen worden de naam van de student en andere bekende namen vervangen, zoals bij Namen verbergen ([spec 033](../033-namen-verbergen/spec.md)): "Student", "Coach", "Medestudent 1" enzovoort. Namen in afbeeldingen kunnen niet worden vervangen, en in tekst uit bestanden alleen als ze precies zo geschreven zijn.
- [x] **F4 – Bezig.** Een lokaal model kan er een paar minuten over doen. Tijdens het maken staat er "Advies wordt gemaakt…", met wat er klaar is ("bestanden lezen 3 van 5", "advies schrijven") en een knop **"Stoppen"**. De rest van de pagina blijft bruikbaar. Verlaat je de pagina, dan gaat het maken door; kom je terug, dan zie je de voortgang of het resultaat.
- [x] **F5 – Advies per vaardigheid.** Per gevraagde vaardigheid, in de volgorde OC … RE:
  - wie hem beoordeelt (coach of gildemeester);
  - een **voorgesteld niveau** (`0` … `4`, zoals in de interface) naast het niveau dat de student zelf aangeeft;
  - een korte **onderbouwing**, met verwijzing naar de LEF-tekst van dat niveau en naar de bewijsstukken bij naam;
  - wat er nog **ontbreekt** of wat de student kan doen om verder te komen.

  Het advies is in het Nederlands en ontwikkelingsgericht geformuleerd, niet beoordelend ([design-system.md](../../docs/design-system.md)).
  - *Acceptatie:* bij een verzoek voor OC en KO staan twee adviezen, elk met een niveau, een onderbouwing die minstens één bewijsstuk noemt, en een ontwikkelpunt.
- [x] **F6 – Duidelijk een advies.** Het blok zegt dat het advies door een AI-model is gemaakt, kan kloppen of niet kloppen, en dat de coach of gildemeester beslist. Daarbij staan het model en de datum. Het voorgestelde niveau valt minder op dan het echte niveau, dus het lijkt niet op een beoordeling.
- [x] **F7 – Inhoud van bestanden.**
  - Word, PowerPoint en Excel: de tekst uit het origineel, zonder extra pakket (zip met XML, zoals de Excel-import van [spec 013](../013-excel-importeren/spec.md)).
  - Pdf: de tekst met het pakket `pypdf`.
  - Afbeeldingen: als afbeelding naar het model, als dat model afbeeldingen kan lezen. Kan het dat niet, dan gaat alleen de naam mee.
  - Video en andere soorten: alleen de naam.
  - Een bestand dat niet te lezen is, gaat mee met de naam en de opmerking "inhoud niet gelezen".
  - Het overzicht van F2 noemt welke bestanden alleen met hun naam meegaan.
- [x] **F8 – Te veel.** Past niet alles in wat het model aankan, dan gaat de inhoud van bewijsstukken mee tot de grens: per vaardigheid evenveel, de nieuwste eerst. De rest gaat mee met alleen de naam, en het blok zegt dat.
- [x] **F9 – Bewaren.** Het laatste advies per verzoek blijft lokaal bewaard, met het model en de datum. Als je de pagina opnieuw opent, staat het er meteen. **"Opnieuw vragen"** maakt een nieuw advies en vervangt het oude. **Alles verwijderen** ([spec 014](../014-alles-verwijderen/spec.md)) wist de adviezen.
- [x] **F10 – Ollama niet klaar.** Draait Ollama niet, of is het gekozen model niet geïnstalleerd, dan staat er in plaats van de knop wat er ontbreekt en een knop **"AI-advies instellen"** naar de wizard (F12).
- [x] **F12 – Wizard "AI-advies instellen".** Een pagina die de gebruiker stap voor stap helpt, met na elke stap een controle door het dashboard. Elke stap toont ✓ (klaar), de uitleg en een knop **"Controleren"**; de eerste stap die nog niet klaar is, staat open. De stappen:
  1. **Je laptop.** Het dashboard toont het werkgeheugen en het besturingssysteem. Met minder dan 16 GB staat er een waarschuwing dat het model traag kan zijn of niet past. *Controle:* het geheugen uitlezen.
  2. **Ollama installeren en starten.** De downloadlink van Ollama (ollama.com/download) en de stappen voor macOS of Windows (het systeem van de gebruiker eerst), met hoe je Ollama start. *Controle:* Ollama antwoordt op het adres op de laptop, met zijn versie.
  3. **Model downloaden.** Het voorgestelde model met zijn grootte. Een knop **"Model downloaden"** laat Ollama het model ophalen, met een voortgangsbalk; de opdracht `ollama pull …` staat erbij als alternatief. *Controle:* het model staat in de lijst van Ollama.
  4. **Proefvraag.** Een knop **"Proefvraag stellen"** stuurt een kleine, verzonnen evaluatie naar het model. *Controle:* er komt een geldig antwoord; de wizard toont hoe lang het duurde en waarschuwt boven 2 minuten.
  5. **Klaar.** Het model is opgeslagen als het model voor AI-advies, met een link naar Evaluaties.
  - *Acceptatie:* zonder Ollama staat stap 2 open met de uitleg; na installeren en "Controleren" staat er ✓ met de versie en gaat stap 3 open.
- [x] **F11 – Instellingen.** In Instellingen staat een sectie **"AI-advies"** met:
  - de status ("Ollama draait, model gemma3:12b geïnstalleerd");
  - een keuzelijst met de geïnstalleerde modellen, met als voorstel **`gemma4:12b-it-qat`** (7,2 GB, Nederlands, leest afbeeldingen; voor laptops met 16 GB geheugen of meer), voor iedereen hetzelfde (gekozen 2026-11-22, zie Onderzoek);
  - een knop **"AI-advies instellen"** naar de wizard (F12);
  - het adres van Ollama, standaard `http://127.0.0.1:11434` en alleen een adres op de laptop zelf.

### Claude via de API (toegevoegd 2026-11-22)

Op verzoek van de gebruiker kan het advies ook door **Claude** (Anthropic) worden gemaakt, via internet. Dat is een bewuste keuze per advies; het lokale model blijft de standaard.

- [x] **F13 – Claude instellen.** De wizard heeft een tweede deel **"Claude (via internet)"**:
  - eerst de waarschuwing: *gebruik alleen AI-diensten die door de HU zijn goedgekeurd voor werk van studenten*, met wat er naar Anthropic gaat (het materiaal met vervangen namen, ook afbeeldingen);
  - een verplicht vinkje: **"Ik heb gecontroleerd dat de HU het gebruik van Claude hiervoor toestaat."** Zonder vinkje kan de sleutel niet worden opgeslagen. Het vinkje wordt met datum bewaard; de waarschuwing komt alleen bij het instellen (gekozen 2026-11-22);
  - een veld voor de **API-sleutel**. *Controle:* het dashboard vraagt bij Anthropic of de sleutel geldig is (zonder kosten) en toont ✓ of de fout;
  - daarna staat de sleutel er afgekort ("sk-ant-…1234"), met een knop **"Sleutel verwijderen"**.
- [x] ~~**F14 – Twee knoppen.**~~ *(vervangen door de keuzelijst hieronder)* Op de evaluatiepagina staan, voor elke ingestelde dienst, de knoppen **"Advies met lokaal model"** en **"Advies met Claude"**. Bij de Claude-knop staat kort "via internet, naar Anthropic". Het bewaarde advies toont welke dienst en welk model het maakte.
- [x] **F15 – Inhoud.** Naar Claude gaat hetzelfde als naar het lokale model, ook de afbeeldingen (gekozen 2026-11-22), met dezelfde vervanging van namen (F3).
- [x] **F16 – Model.** `claude-opus-5-5`, met effort `high`, een vast JSON-antwoord en de automatische uitwijkmogelijkheid van Anthropic als het model een verzoek weigert. Weigert ook die, dan staat er een melding.
- [x] **F17 – De sleutel.** Alleen in de lokale database, zoals het Portflow-token: niet in de repository, niet in reservekopieën, niet in logs en nooit in de browser. "Alles verwijderen" laat hem staan, net als de Portflow-koppeling.

### Keuzelijst en eigen opdracht (gewijzigd 2026-11-22)

*Op verzoek van de gebruiker: in de instellingen stel je elke AI apart in, en op de evaluatiepagina kies je in een keuzelijst welke AI het advies maakt. Dit vervangt de twee knoppen van F14.*

- [x] **F14 (gewijzigd) – Keuzelijst.** Op de evaluatiepagina staat een keuzelijst met de AI's die zijn ingesteld (bijvoorbeeld "Lokaal model · gemma4:12b-it-qat" en "Claude · claude-opus-5-5 (via internet)"), met daarnaast **"Advies vragen"**. Bij een AI buiten de laptop staat "via internet". Het bewaarde advies toont welke AI het maakte.
- [x] **F18 – Algemene opdracht.** In de AI-instellingen staat het blok **"Opdracht aan de AI"** met de algemene opdracht. Die is vooringevuld met de standaardtekst en kan worden aangepast; de knop **"Standaardtekst terugzetten"** zet de standaardtekst terug. Hij geldt voor elke AI.
- [x] **F19 – Aanvulling per vaardigheid.** In hetzelfde blok per vaardigheid (OC … RE) een veld voor een **aanvulling**: waar de AI bij die vaardigheid op moet letten. Een aanvulling gaat alleen mee als die vaardigheid in het verzoek zit, bij die vaardigheid.
  - *Acceptatie:* met een aanvulling bij PL en een verzoek voor PL en BD staat de aanvulling bij PL in de vraag aan de AI, en niet bij BD.

- [x] **F22 – Claude alleen voor één gebruiker.** De keuze **Claude** verschijnt alleen als de in Portflow ingelogde gebruiker **Peter Snoek** is (hoofdletters en spaties maken niet uit): in de keuzelijst op de evaluatiepagina, en het hele Claude-deel van de wizard. Voor andere gebruikers is alleen het lokale model er; de routes om Claude in te stellen of met Claude advies te vragen weigeren dan. De naam staat op één plek in de code (`claude_ai.ALLOWED_USERS`), zodat hij makkelijk te wijzigen is.
  - *Acceptatie:* ingelogd als Peter Snoek staat Claude in de keuzelijst; als een andere naam niet, en `/instellingen/ai-advies/claude` geeft 403.

### Duur en vervolgvragen (toegevoegd 2026-11-22)

- [x] **F20 – Duur.** Bij een advies staat hoe lang het model erover deed ("het model deed er 1 min 12 s over"); bij elk antwoord op een vervolgvraag ook. Gemeten van het versturen naar het model tot het antwoord binnen is (het verzamelen van het materiaal telt niet mee).
- [x] **F23 – Namen terugzetten.** Het dashboard onthoudt welke namen het vóór het versturen heeft vervangen (F3), en zet ze in het getoonde advies en in de antwoorden op vervolgvragen weer terug naar de echte namen. Wat naar de AI gaat (ook het advies en het gesprek bij een vervolgvraag) houdt de vervangen namen, zodat er nooit een echte naam naar de AI gaat. Een algemeen woord als "de student" blijft staan; alleen de ingevoegde naam-plekken worden teruggezet.
  - *Acceptatie:* een advies waarin de AI "Student" en "Coach 1" schreef, toont de echte naam van de student en van de coach; in wat naar de AI ging staat "Student" en "Coach 1".
- [x] **F21 – Vervolgvragen.** Onder het advies staat een tekstvak met de knop **"Vraag stellen"**. De vraag gaat naar **dezelfde AI** die het advies maakte, met hetzelfde materiaal, het advies en het gesprek tot nu toe; namen in de vraag worden ook vervangen (F3). Het antwoord verschijnt onder de vraag, als gewone tekst. Tijdens het wachten staat er "Antwoord wordt gemaakt…" met de knop Stoppen, zoals bij F4.
  - Het gesprek wordt lokaal bewaard bij het advies (gekozen 2026-11-22). **"Opnieuw vragen"** begint een nieuw advies en wist het gesprek; Alles verwijderen wist alles.
  - Afbeeldingen gaan alleen mee met het advies zelf, niet opnieuw met elke vervolgvraag; het materiaal als tekst wel (het wordt daarvoor lokaal bewaard bij het advies).
  - *Acceptatie:* na een advies typ je "Waarom niet niveau 3 bij PL?"; het antwoord staat eronder met de duur, en het staat er nog als je de pagina opnieuw opent.

### Eerst je eigen oordeel, en een model kiezen (toegevoegd 2026-11-24)

*Op verzoek van de gebruiker: de beoordelaar vult eerst zelf een oordeel in, pas daarna kan het AI-advies worden gevraagd. En het lokale model is te kiezen, in Instellingen als standaard en op de evaluatiepagina per advies.*

- [x] **F24 – Eerst je eigen oordeel.** Boven de keuzelijst van F14 staat het blok **"Jouw oordeel"**, met per gevraagde vaardigheid (OC … RE) een keuze voor het **niveau** (`0` … `4`) en een tekstvak voor de **toelichting**. De knop **"Advies vragen"** (of "Opnieuw vragen") is pas actief als bij elke gevraagde vaardigheid een niveau én een toelichting staan; tot dan staat er bij de knop "Vul eerst je eigen oordeel in". Het dashboard weigert ook zelf een verzoek zonder volledig oordeel.
  - *Acceptatie:* bij een verzoek voor OC en KO is de knop uit zolang bij KO de toelichting leeg is; met beide ingevuld is hij aan.
- [x] **F25 – Het oordeel gaat mee naar de AI.** Het oordeel gaat mee in de vraag aan de AI, met dezelfde vervanging van namen (F3). De opdracht vraagt de AI om eerst zelf, op basis van het materiaal en de LEF-teksten, tot een advies te komen en niet zomaar mee te gaan met het oordeel. Per vaardigheid geeft de AI daarna aan **waar en waarom het advies afwijkt** van het oordeel van de beoordelaar (of dat het overeenkomt). Bij het advies staat per vaardigheid jouw niveau naast het voorgestelde niveau. Het overzicht van F2 noemt ook "jouw oordeel".
- [x] **F26 – Het oordeel bewaren.** Het oordeel wordt lokaal bewaard bij het verzoek zodra je het advies vraagt, en staat er weer als je de pagina opnieuw opent. Bij "Opnieuw vragen" gaat het (eventueel aangepaste) oordeel mee. Vervolgvragen (F21) krijgen het oordeel ook mee. **Alles verwijderen** wist het.
- [x] **F27 – Standaardmodel in Instellingen.** In Instellingen, sectie AI-advies (F11), staat een keuzelijst met de modellen die in Ollama staan, en een knop **"Opslaan"**. Het voorgestelde model (`gemma4:12b-it-qat`, zie Onderzoek) heeft de vermelding **"(aangeraden)"**. Het gekozen model is het standaardmodel; het is hetzelfde als het model in stap 3 van de wizard (F12). Draait Ollama niet, dan staat er alleen de status, zoals nu.
- [x] **F28 – Modellen downloaden in Instellingen.** In Instellingen, sectie AI-advies, staat een lijst met **geteste modellen**: naam, grootte, wat het geheugen vraagt en een korte uitleg uit het onderzoek (bijvoorbeeld "aangeraden" of "lichter: sneller, minder goed advies"). Bij een model dat nog niet in Ollama staat, staat een knop **"Downloaden"**; bij een model dat er al staat, "✓ geïnstalleerd". Daaronder een veld om **zelf een modelnaam** te typen (zoals bij `ollama pull`), met dezelfde knop. Het downloaden laat Ollama het model ophalen, met een voortgangsbalk, zoals stap 3 van de wizard (F12); er loopt één download tegelijk en je kunt de pagina intussen verlaten. Na het downloaden staat het model in de keuzelijst van F27. De lijst met geteste modellen staat op één plek in de code.
  - *Acceptatie:* met Ollama draaiend en `gemma4:e4b` niet geïnstalleerd: klik op Downloaden, de voortgang loopt, en daarna staat `gemma4:e4b` met ✓ in de lijst en in de keuzelijst van F27. Een niet-bestaande naam geeft de melding van Ollama.
- [x] **F14 (gewijzigd 2026-11-24) – Model kiezen bij het advies.** De keuzelijst op de evaluatiepagina toont **elk model dat in Ollama staat apart** ("Lokaal model · qwen3.5:9b", "Lokaal model · gemma4:12b-it-qat (aangeraden)"), plus Claude als die is ingesteld (F22). Voorgeselecteerd is het standaardmodel uit Instellingen; staat er al een advies, dan de AI en het model van dat advies. Vervolgvragen gaan naar hetzelfde model dat het advies maakte.
  - *Acceptatie:* met twee modellen in Ollama staan er twee lokale keuzes; kies je het niet-standaardmodel, dan toont het advies dat model.

### De laptop ontlasten (toegevoegd 2026-11-24)

*Op verzoek van de gebruiker: een lokaal model kan de hele laptop in beslag nemen (op een laptop met 16 GB en een Intel-processor draait het model op de processor). In Instellingen kun je begrenzen hoeveel het model mag gebruiken. Dit geldt voor alle lokale modellen samen, want het gaat om wat de laptop aankan; Claude heeft er niets mee te maken.*

- [x] **F29 – Processorkernen.** In Instellingen, sectie AI-advies, een schuifje **"Processorkernen voor het model"**, van 1 tot het aantal kernen van de laptop, met het gekozen aantal erbij ("4 van 8"). Standaard: alle kernen min één, zodat de laptop blijft reageren. Het dashboard stuurt dit mee met elke vraag aan Ollama (Ollama-optie `num_thread`): het advies, vervolgvragen en de proefvraag. Erbij staat: "Minder kernen: de laptop blijft beter bruikbaar, het advies duurt langer. Op een Mac rekent het model vooral op de grafische chip; daar maakt dit weinig uit."
  - *Acceptatie:* met het schuifje op 2 gaat `num_thread: 2` mee in de vraag aan Ollama.
- [x] **F30 – Hoeveel materiaal per advies.** Een keuze met drie mogelijkheden, die het geheugengebruik bepaalt (Ollama-optie `num_ctx`, en de grens van F8 schaalt mee):
  - **Weinig** (8.192 tokens, ongeveer 20.000 tekens materiaal): het minste geheugen; bij een groot verzoek gaan veel bewijsstukken mee met alleen hun naam.
  - **Normaal** (16.384 tokens, ongeveer 40.000 tekens).
  - **Veel** (32.768 tokens, ongeveer 80.000 tekens): zoals tot nu toe; het meeste geheugen, enkele GB extra bovenop het model.
  Erbij staat dat het model zelf altijd in het geheugen moet passen (ongeveer de grootte van het bestand) en dat deze keuze alleen het extra geheugen bepaalt. Het overzicht van F2 en de melding van F8 werken zoals nu.
- [x] **F31 – Model na het advies uit het geheugen.** Een vinkje **"Model na het advies uit het geheugen halen"** (Ollama-optie `keep_alive: 0`). Standaard uit: dan blijft het model zoals nu nog 5 minuten geladen, zodat een vervolgvraag sneller gaat. Aan: het geheugen is direct na het advies weer vrij, maar een vervolgvraag laadt het model opnieuw (dat kan een minuut duren).
- [x] **F32 – Opslaan.** De drie instellingen staan samen met **"Opslaan"**, en gelden vanaf het volgende advies. Een advies dat al loopt, gaat door met de oude instellingen.
- Grenzen gelden alleen voor vragen van het dashboard; wie Ollama ook voor iets anders gebruikt, merkt er daar niets van.

### Buiten scope

- Beoordelen of het advies in Portflow zetten.
- Advies zonder evaluatieverzoek, bijvoorbeeld voor een hele student.
- Oudere adviezen bewaren: alleen het laatste blijft.
- De student informeren. Dat is de afweging van de coach of gildemeester; het dashboard toont er niets over (gekozen 2026-11-22).

## Onderzoek: welk model (2026-11-22)

Proef op de Mac van de gebruiker (24 GB) met één verzonnen evaluatie (PL en BD, met LEF-teksten, zelfevaluatie, twee bewijsstukken en een eerdere beoordeling), dezelfde opdracht en een JSON-schema:

| Model | Grootte | Tijd | Bevinding |
|---|---|---|---|
| llama3.2 | 2 GB | 7 s | Onbruikbaar: alleen de titel van het niveau; BD 2 zonder bewijs |
| gemma4:e4b | 9,6 GB | 19 s | Redelijk; plakt materiaal letterlijk over |
| qwen3.5:9b | 6,6 GB | 26 s | Goede verwijzingen, maar verzon bij BD iets wat niet in het materiaal stond |
| gemma4:12b-it-qat | 7,2 GB | 34 s | Beste balans: verwijst naar de vorige beoordeling, benoemt eerlijk wat ontbreekt, ontwikkelpunt naar het volgende niveau |
| gemma4:26b | 18 GB | 56 s | Zorgvuldigst, maar vraagt 18 GB werkgeheugen |

Gekozen: `gemma4:12b-it-qat` als voorstel voor iedereen.

**Aanvullende proef (2026-11-24)**, voor laptops met 16 GB waarop het voorgestelde model zwaar is: een nieuwe verzonnen evaluatie (PL met twee bewijsstukken en een eerdere beoordeling; BD zonder bewijsstukken), dezelfde opdracht en hetzelfde JSON-schema, op dezelfde Mac:

| Model | Grootte | Tijd | Bevinding |
|---|---|---|---|
| gemma4:e2b | 4,6 GB | 14 s | Niet geschikt: gaf bij BD zonder één bewijsstuk toch het gevraagde niveau 2 |
| gemma4:e4b | 9,6 GB | 17 s | Bruikbaar als lichter alternatief: BD terecht 0, PL goed onderbouwd met citaten; liet bij PL het ontwikkelpunt leeg |
| gemma4:12b-it-qat | 7,2 GB | 30 s | Zoals eerder het best: BD 0, PL met een concreet ontwikkelpunt |

Gevolg: `gemma4:e4b` is het lichtere alternatief (minder rekenwerk per woord, wel een groter bestand); `gemma4:e2b` wordt niet aangeraden.

**Proef met een Europese maker (2026-11-24)**, op verzoek van de gebruiker: Ministral 3 van Mistral (Frankrijk), beide lezen afbeeldingen. Dezelfde verzonnen evaluatie, nu met de juiste naam van BD (Boodschap delen; in de vorige proef stond per ongeluk "Bouwen en ontwikkelen") en een zelfevaluatie over een presentatie in de sprintreview, zonder bewijsstukken:

| Model | Grootte | Tijd | Bevinding |
|---|---|---|---|
| ministral-3:8b | 6,0 GB | 30 s | Niet aangeraden: PL goed, maar bij BD trok het een conclusie "die niet expliciet in het materiaal staat"; schrijft opmaaktekens (`**vet**`) die het dashboard als tekst toont |
| ministral-3:14b | 9,1 GB | 87 s | Niet aangeraden: traag, zeer lang en vol opmaak, en noemde bij PL dingen die niet in het materiaal stonden ("learning stories, DevOps-taken") |
| gemma4:e4b | 9,6 GB | 18 s | Bruikbaar, maar gaf bij BD zonder bewijs nu niveau 1 (vorige proef 0) |
| gemma4:12b-it-qat | 7,2 GB | 30 s | Weer het best: BD 0, korte en concrete onderbouwing en ontwikkelpunt |

Gevolg: de Ministral-modellen komen niet in de lijst met geteste modellen (F28); `gemma4:12b-it-qat` blijft het voorstel.

## Onderzoek: Microsoft 365 Copilot (2026-11-22)

Uit de documentatie van Microsoft (Microsoft 365 Copilot Chat API, Microsoft Learn):

- **Status:** preview, onder `https://graph.microsoft.com/beta`. Volgens Microsoft wordt gebruik in productie-apps niet ondersteund. Er is geen datum bekend waarop de API algemeen beschikbaar wordt.
- **Aanroepen:** eerst een gesprek aanmaken (`POST /beta/copilot/conversations`), dan een bericht sturen (`POST …/{id}/chat`, of `…/chatOverStream` om het antwoord in stukken te ontvangen). In het bericht gaan de tekst, een tijdzone en eventueel extra tekst als context (`additionalContext`) mee.
- **Inloggen:** alleen namens een ingelogde gebruiker met een HU-account (gedelegeerd); een app kan het niet op eigen titel. Er zijn zeven rechten tegelijk nodig: Sites.Read.All, Mail.Read, People.Read.All, OnlineMeetingTranscript.Read.All, Chat.Read, ChannelMessage.Read.All, ExternalItem.Read.All. Daarvoor is een app-registratie in Entra ID door HU-ICT nodig. Voor een aantal van die rechten moet een beheerder ook toestemming geven.
- **Licentie:** elke gebruiker heeft een **Microsoft 365 Copilot-licentie** nodig (de add-on). Zonder die licentie werkt de API niet.
- **Beperkingen:**
  - het antwoord is alleen tekst, zonder vast JSON-formaat, dus het dashboard moet de tekst controleren;
  - afbeeldingen en bestanden meesturen kan niet; bestanden alleen als link naar OneDrive of SharePoint;
  - zoeken op internet staat standaard aan en moet per bericht uit;
  - lange taken lopen vaak vast op een time-out;
  - een maximale lengte van een bericht staat niet in de documentatie.
- **Gegevens:** volgens Microsoft blijft alles binnen de vertrouwensgrens van Microsoft 365 van de HU. Copilot ziet alleen wat de gebruiker zelf mag zien.

Gevolg: bouwen kan pas als de vragen hierboven over licentie, app-registratie en preview zijn beantwoord. Voor het dashboard betekent het verder:
- een inlogvenster voor het HU-account (OAuth met PKCE, net als Portflow via de browser);
- geen afbeeldingen meesturen;
- het antwoord als tekst laten teruggeven en het daarna controleren.

## Schermen

Geen eigen ontwerp: een kaart onderaan de evaluatiepagina, in de stijl van het dashboard. Volgorde: kop "Advies (AI)" met model en datum → wat er meegaat (F2) → knop of voortgang → per vaardigheid het advies (F5).

## Data

- **Bron:** wat de evaluatiepagina al toont ([spec 039](../039-evaluatie-voorbereiden/spec.md)), plus de inhoud van bestanden. Voorbeelden haalt het dashboard uit de cache van [spec 038](../038-bestanden-bekijken/spec.md); Office-originalen haalt het live op en bewaart het niet.
- **Bewaard:** het laatste advies per verzoek in een nieuwe tabel: `review_request_id`, model, datum, per vaardigheid het voorgestelde niveau en de teksten, en de aantallen van F2.
- **Privacy:** alles blijft op de laptop. Ollama draait lokaal en het dashboard praat alleen met een adres op de laptop zelf. Namen worden toch vervangen (F3). [architectuur.md](../../docs/architectuur.md#privacy) wordt bijgewerkt.

## Technische eisen

- Ollama aanroepen met `urllib` (`POST /api/chat`, en `GET /api/tags` voor de modellen). Een JSON-schema in `format` geeft een vast antwoord per vaardigheid; het dashboard controleert dat antwoord voordat het iets toont.
- Alleen `127.0.0.1`, `localhost` of `[::1]` als adres van Ollama. Geen token en geen Portflow-gegevens naar andere adressen.
- **Nieuwe dependency `pypdf`** (zuiver Python), alleen voor tekst uit pdf's. De reden komt in de tabel in [architectuur.md](../../docs/architectuur.md): de standaardbibliotheek kan geen pdf lezen. Werkt de app ook zonder `pypdf`, dan gaat bij een pdf alleen de naam mee.
- Claude met de officiële SDK **`anthropic`** (nieuwe dependency, gekozen 2026-11-22: foutafhandeling en nieuwe API-versies zitten erin; reden in [architectuur.md](../../docs/architectuur.md)).
- De opdracht aan het model (rol, LEF als maatstaf, ontwikkelingsgericht, niet verzinnen, bewijsstukken bij naam noemen, Nederlands) staat op één plek in de code en is te testen.
- Het maken gebeurt in een achtergrondtaak, zoals Verversen, met voortgang en stoppen. Er loopt per verzoek één tegelijk.
- Tests met een nep-Ollama en verzonnen namen: wat er meegaat, het vervangen van namen, de grens (F8), een ongeldig antwoord van het model, en Ollama niet bereikbaar.

## Open vragen

- [x] AI-dienst: lokaal, met Ollama.
- [x] Model: een vast voorstel, te wijzigen in Instellingen. Eerst Gemma 3 12B; na de proef `gemma4:12b-it-qat` (2026-11-22).
- [x] Meesturen: zelfevaluatie, LEF-teksten, teksten van bewijsstukken, bestanden, eerdere beoordelingen, feedbackvragen en reacties.
- [x] Bestanden: tekst eruit halen; Office zonder pakket, pdf met `pypdf`, afbeeldingen als afbeelding.
- [x] Namen vervangen: ja.
- [x] Bewaren: het laatste advies per verzoek, lokaal.
- [x] Welke vaardigheden: alle gevraagde.
- [x] Student informeren: de afweging van de gebruiker; niets in het dashboard.
- [x] Welke AI van Microsoft: **Microsoft 365 Copilot** (gekozen door de gebruiker, 2026-11-22). Zie *Onderzoek: Microsoft 365 Copilot*.
- [ ] Heeft de gebruiker (en hebben collega's) een **Microsoft 365 Copilot-licentie** (de betaalde add-on)? De gratis Copilot Chat in Edge en Teams is niet genoeg.
- [ ] Wil HU-ICT een **app-registratie in Entra ID** maken voor het dashboard, met de zeven gedelegeerde rechten hieronder en toestemming van een beheerder?
- [ ] Mag een functie op een **preview-API** draaien, waarvan Microsoft zegt dat die niet bedoeld is voor gebruik in productie?
- [ ] Krijgt Microsoft ook een waarschuwing met vinkje bij het instellen, zoals Claude?
- [x] F30: welke keuze is de standaard? *Gekozen 2026-11-24: **Veel**, zoals nu, zodat het advies niet verandert; wie geheugen tekortkomt, kiest zelf Normaal of Weinig.*
- [x] `gemma4:e4b` liep met veel materiaal vast (zie logboek 2026-11-24). Een grens aan de lengte van het antwoord toevoegen? *Nee, gekozen door de gebruiker 2026-11-24.*
- [x] F24: moet de beoordelaar een oordeel geven over **alle** gevraagde vaardigheden, of alleen over de vaardigheden die hij zelf beoordeelt (een coach de sociale en persoonsvormende, een gildemeester de productvaardigheden)? *Gekozen 2026-11-24: alle gevraagde, omdat het advies ook over alle gaat.*

## Logboek

- 2026-11-22 – spec aangemaakt op verzoek van de gebruiker, als eerste schets naast spec 039
- 2026-11-22 – vragen beantwoord door de gebruiker: lokaal model met Ollama, Gemma 3 12B als voorstel, alles meesturen met tekst uit bestanden (`pypdf` voor pdf), namen vervangen, advies lokaal bewaren, alle gevraagde vaardigheden, niets over het informeren van de student; status uitgewerkt
- 2026-11-22 – bouwen gestart. Op verzoek van de gebruiker een wizard met controle per stap (F12). Proef met vijf lokale modellen (zie Onderzoek); voorstel wordt `gemma4:12b-it-qat` voor iedereen. `pypdf` geïnstalleerd met akkoord van de gebruiker. Status in bouw
- 2026-11-22 – gebouwd: `ollama.py` (alleen een adres op de laptop; versie, modellen, downloaden met voortgang, `chat` met JSON-schema, streamend zodat stoppen kan), `file_text.py` (Word, PowerPoint en Excel zonder pakket, pdf met `pypdf`), `ai_advice.py` (materiaal verzamelen, namen vervangen, budget, controle van het antwoord, tabel `ai_advice`, achtergrondtaak, proefvraag), `ai_routes.py` met de wizard (`/instellingen/ai-advies`, `ai_setup.html`) en het blok op de evaluatiepagina (`_ai_advice.html`); sectie AI-advies in Instellingen. Keuzes bij het bouwen: het model krijgt 32.768 tokens ruimte en ongeveer 80.000 tekens materiaal; hoogstens 6 afbeeldingen van elk hoogstens 4 MB; de voornaam van de student wordt ook vervangen; de gebruiker zelf heet "de beoordelaar". Alles verwijderen wist de adviezen en houdt de AI-instellingen. Tests in `tests/test_ai_advice.py` met een nep-Ollama; met echte gegevens en `gemma4:12b-it-qat` nagekeken: wizard met alle stappen ✓, proefvraag 11 s, advies voor drie vaardigheden met 24 bewijsstukken (waarvan 6 afbeeldingen) binnen een paar minuten. Status klaar
- 2026-11-22 – uitgebreid op verzoek van de gebruiker: advies ook met Claude via de API (F13–F17). Keuzes: per advies een knop, waarschuwing en vinkje alleen bij het instellen, ook afbeeldingen mee, officiële SDK `anthropic` (geïnstalleerd met akkoord). Model `claude-opus-5-5`. Status in bouw
- 2026-11-22 – op verzoek van de gebruiker: per AI een eigen instelling en een keuzelijst op de evaluatiepagina (F14 gewijzigd); een eigen algemene opdracht en een aanvulling per vaardigheid (F18, F19). Microsoft als derde AI: open vraag
- 2026-11-22 – gebouwd: `claude_ai.py` (officiële SDK, `claude-opus-5-5`, effort `high`, JSON-schema via `output_config`, automatische uitwijk bij een weigering met `fallbacks: "default"`, streamend zodat stoppen kan; sleutel controleren met het opvragen van het model), keuzelijst op de evaluatiepagina (`ai_advice.available`, kolom `service` in `ai_advice`), Claude-deel met waarschuwing en verplicht vinkje en het blok "Opdracht aan de AI" in de instellingen. Het JSON-schema gebruikt nu `enum` voor het niveau (Anthropic kent geen `minimum`/`maximum`). Tests met een nep-Claude; **niet met de echte API nagekeken** (geen sleutel). Het lokale model werkt nog zoals eerst. Status blijft in bouw: Microsoft is een open vraag
- 2026-11-22 – de gebruiker koos Microsoft 365 Copilot. De documentatie van de Copilot Chat API is uitgezocht (zie Onderzoek). Nog niet gebouwd: eerst zijn licentie, app-registratie door HU-ICT en het gebruik van een preview-API nodig
- 2026-11-22 – op verzoek van de gebruiker: de duur van een advies tonen (F20) en vervolgvragen stellen (F21). Keuzes: het gesprek wordt bewaard bij het advies, en dezelfde AI beantwoordt de vraag
- 2026-11-22 – gebouwd: de duur van het model bij het advies en bij elk antwoord (kolom `seconds`), vervolgvragen met tekstvak en gesprek (kolommen `prompt` en `conversation` in `ai_advice`, `Jobs.ask`, route `/evaluaties/<id>/advies/vraag`; Ollama en Claude kunnen nu ook vrije tekst en een gesprek). Een advies van vóór deze versie heeft geen bewaard materiaal; daar staat "Vraag eerst opnieuw een advies". Met echte gegevens en het lokale model nagekeken: het advies duurde 3 min 38 s, een vervolgvraag 2 min 28 s (het hele materiaal gaat opnieuw mee). Tests in `tests/test_ai_advice.py`
- 2026-11-22 – op verzoek van de gebruiker: Claude is alleen zichtbaar en bruikbaar voor de ingelogde Portflow-gebruiker Peter Snoek (F22, `claude_ai.allowed`, controle in de instellingen, de keuzelijst en de routes). Tests in `tests/test_ai_advice.py` (TestClaudeVisibility)
- 2026-11-23 – op verzoek van de gebruiker: de naamvervanging wordt onthouden (kolom `names` bij het advies) en in het getoonde advies en de antwoorden teruggezet naar de echte namen (`ai_advice.restore`). De naar de AI gestuurde tekst, het bewaarde advies en de gesprekshistorie blijven vervangen; onderweg bleek dat een vervolgvraag in de historie de echte naam meestuurde — nu gaat ook daar de vervangen naam mee (`question_anon`). Tests in `tests/test_ai_advice.py` (TestRestoreNames)
- 2026-11-23 – F11: de status van Ollama in Instellingen wordt apart geladen (`GET /instellingen/ollama`, door `app.js` na de pagina); een gestopte Ollama liet Instellingen 2 s wachten, nu 25 ms. Tot de status er is staat er "Ollama controleren…"
- 2026-11-24 – uitgebreid op verzoek van de gebruiker: eerst een eigen oordeel per vaardigheid (niveau en toelichting) voordat het advies kan worden gevraagd; het oordeel gaat mee naar de AI en wordt bewaard (F24–F26). Een standaardmodel kiezen in Instellingen, met "(aangeraden)" bij het voorgestelde model (F27), en elk lokaal model apart in de keuzelijst (F14 gewijzigd). Status in bouw
- 2026-11-24 – op verzoek van de gebruiker: modellen downloaden vanuit Instellingen, met een lijst geteste modellen en een vrij veld voor een modelnaam (F28)
- 2026-11-24 – aanvullende proef met gemma4:e2b, gemma4:e4b en gemma4:12b-it-qat (zie Onderzoek): e4b is het lichtere alternatief, e2b niet geschikt
- 2026-11-24 – gebouwd: F24–F28. Het eigen oordeel staat in de tabel `ai_judgment` (het concept) en bij het advies (kolom `judgment` in `ai_advice`, wat er werkelijk meeging); de AI krijgt het onder "Voorlopig oordeel van de beoordelaar" met de opdracht eerst zelf te oordelen, en geeft per vaardigheid een veld `verschil` (alleen gevraagd als er een oordeel meegaat; de proefvraag van de wizard vraagt het niet). Keuzelijst met elk Ollama-model apart (`lokaal:<model>`), standaardmodel en downloaden in Instellingen (`ollama.TESTED_MODELS`, `ollama.valid_name`). Tests in `tests/test_ai_advice.py` (TestOwnJudgment, TestModelChoice)
- 2026-11-24 – nagekeken met echte gegevens: met `gemma4:12b-it-qat` een advies met eigen oordeel en vergelijking in 1 min 56 s (19 bewijsstukken, 3 afbeeldingen). Met `gemma4:e4b` liep hetzelfde verzoek met alle bewijsstukken na ongeveer 10 minuten vast op "geen geldig antwoord"; zonder de inhoud van bewijsstukken gaf e4b wel binnen 21 s een goed advies met vergelijking. Het lichtere model lijkt bij veel materiaal niet te stoppen met schrijven; de gebruiker koos ervoor dit zo te laten
- 2026-11-24 – op verzoek van de gebruiker: de laptop ontlasten met instellingen voor processorkernen, hoeveel materiaal (geheugen) en het model na het advies uit het geheugen halen (F29–F32); voor alle lokale modellen samen
- 2026-11-24 – gebouwd: F29–F32. Instellingen `ai_threads`, `ai_context` en `ai_unload` (`ai_advice.laptop`, `ai_advice.model_options`); `ollama.chat` stuurt `num_thread` en `keep_alive` mee; de grens van F8 hangt nu af van de keuze bij F30 (Claude houdt de grens van Veel). Bij een ongeldige waarde in de database gelden de standaarden. Nagekeken: Ollama accepteert de opties, en met `keep_alive: 0` staat het model direct na het antwoord niet meer in het geheugen. Tests in `tests/test_ai_advice.py` (TestLaptopLimits)
- 2026-11-24 – proef met ministral-3:8b en ministral-3:14b (Mistral) op verzoek van de gebruiker (zie Onderzoek): geen van beide aangeraden. De regel over de grafische chip in Instellingen is op verzoek van de gebruiker niet gebouwd
- 2026-11-24 – samengevoegd met F11 (status apart laden): het standaardmodel, het downloaden en de laptopinstellingen (F27–F32) staan nu ook in het apart geladen deel (`_ai_status.html` via `GET /instellingen/ollama`); `?model=ok` en `?laptop=ok` gaan mee naar dat deel, en `app.js` koppelt de voortgangsbalk en de schuifregelaar na het laden en springt dan naar `#ai-laptop`
