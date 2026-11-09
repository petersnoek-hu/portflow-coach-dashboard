# Gegevensmodel

Welke gegevens het dashboard bijhoudt, waar ze vandaan komen en wie ze invult. Begrippen staan in [begrippen.md](begrippen.md). Hoe de gegevens worden opgeslagen, staat in [architectuur.md](architectuur.md).

## Uitgangspunt: wie is de bron?

| Gegevens | Bron |
|---|---|
| Evaluaties (vaardigheid, niveau, datum, beoordelaar), openstaande evaluatieverzoeken, lijst met gedeelde portfolio's | **Portflow** (alleen lezen; lokaal bewaard als kopie, zie [architectuur.md](architectuur.md#verversen)) |
| Studenten, hun indeling (semester, squad, invulling, beroepsrol), coach en gildemeester | **Het dashboard zelf**: de gebruiker voegt ze toe en beheert ze |
| Squads (in de interface: projecten), beroepsrollen, eigen kolommen | **Het dashboard zelf** |
| Gebruiker (naam, gildes) | **Het dashboard zelf**, ingevuld bij de eerste start |

Elke coach heeft **eigen gegevens**: er is geen gedeelde database tussen coaches.

## Gebruiker

Bij de **eerste start** vult de gebruiker in:

| Veld | Toelichting |
|---|---|
| Naam | Wordt vergeleken met de velden *coach* en *gildemeester* van elke student |
| Gildes | De gildes waarvan de gebruiker gildemeester is; mag leeg zijn (niet elke gebruiker is gildemeester) |

In **Instellingen** beheert de gebruiker daarnaast:

| Instelling | Toelichting |
|---|---|
| **Lijst met coaches en gildemeesters** | Namen. Alleen namen uit die lijst zijn te kiezen in de velden *coach* en *gildemeester* van een student. De naam van de gebruiker staat er automatisch in. Dezelfde lijst bepaalt welke beoordelaars meetellen: evaluaties van beoordelaars die er niet in staan, worden verborgen ([voortgangsregels.md](voortgangsregels.md#welke-evaluaties-tellen)). De namen moeten dus overeenkomen met de namen in Portflow |
| **Semesterperiode** | Begin- en einddatum van het huidige semester, bijvoorbeeld 01-09-2026 t/m 31-01-2027. Alleen evaluaties in deze periode tellen |
| **Drempel "zonder recente update"** | Aantal dagen, standaard 14 |
| **Portflow-verbinding** | Verbinden en opnieuw verbinden; zie [architectuur.md](architectuur.md#portflow-api) |

Daarmee bepaalt de app de filters:

- **Mijn coachstudenten:** studenten bij wie het veld *coach* gelijk is aan de naam van de gebruiker.
- **Mijn gildestudenten:** studenten bij wie het veld *gildemeester* gelijk is aan de naam van de gebruiker, **of** wier gilde (primaire beroepsrol) bij de gildes van de gebruiker hoort.
- **Alle gevolgde studenten:** alle studenten in het dashboard.

Nieuwe studenten krijgen **niet** automatisch de naam van de gebruiker als coach of gildemeester.

## Student

| Veld | Verplicht | Toelichting |
|---|---|---|
| Naam | ja | |
| Studentnummer | nee | Het **OV-nummer** (onderwijsovereenkomstnummer) |
| Semester | ja, maar mag tijdelijk ontbreken | Precies één semester (1–8) per student |
| Squad | nee | In de interface "project"; zonder squad valt de student onder "Zonder project" |
| Invulling | nee | Open projecten (jaar 2), open innovatieproject (jaar 3), stage, minor of afstuderen |
| Rol in de squad | nee | PO, SM, 2ePO of 2eSM (product owner, scrum master, tweede PO, tweede SM) |
| Startdatum | nee | Eigen begin van de semesterperiode voor deze student (bijvoorbeeld bij een latere instroom); anders geldt het begin uit Instellingen |
| Primaire beroepsrol | ja, maar mag tijdelijk ontbreken | Precies één; bepaalt het **gilde** |
| Secundaire beroepsrollen | nee | Nul of meer |
| Coach | nee | Keuze uit de beheerde lijst met coaches en gildemeesters |
| Gildemeester | nee | Keuze uit de beheerde lijst met coaches en gildemeesters |
| Portflow-koppeling | nee | De Portflow-gebruiker (id en naam) en zijn portfolio-id's; een student kan meer dan één portfolio hebben. Zonder koppeling komen er geen evaluaties binnen |
| Waarden eigen kolommen | nee | Per eigen kolom een percentage of tekst, ingevuld door de gebruiker in de tabel |

- Een tribe (bijvoorbeeld "Tribe Peter/David") wordt **niet** bijgehouden.
- Een student blijft bestaan als zijn squad wordt verwijderd; hij komt dan onder "Zonder project".
- Een student zonder semester of zonder primaire beroepsrol (bijvoorbeeld na toevoegen op naam, of nadat zijn beroepsrol is verwijderd) komt in de groep **Nog in te delen**, tot de gegevens zijn ingevuld.

## Studenten toevoegen

Bij de eerste start zijn er **0 studenten**. De gebruiker kan studenten op vier manieren toevoegen:

1. **Uit Portflow kiezen:** inloggen bij Portflow, en in de lijst met alle studentportfolio's die met de gebruiker **gedeeld** zijn de studenten aanvinken die de gebruiker wil volgen.
2. **Excelbestand uploaden:** de app leest het bestand, haalt de studenten eruit en toont een lijst om aan te vinken, met "selecteer alles" en "selecteer niets". De console-app kent drie bestandsvormen; het dashboard herkent die in elk geval (kolomkoppen ongevoelig voor hoofdletters, spaties, `-` en `_`; de kopregel hoeft niet op rij 1 te staan):

   | Bestand | Kolommen | Bijzonderheden |
   |---|---|---|
   | Studentenlijst | Nummer, Naam, Email, Semester, Project, Coach, Gilde voorkeur | *Project* levert de squad (bijvoorbeeld "(08) Commerciële economie - …"); *Gilde voorkeur* kan meerdere gildes bevatten, gescheiden door `/` |
   | Aanwezigheidsbestand gilde | Student, Coach, Semester, Gildemeester | Gilde soms af te leiden uit kolommen als *Frontend* en *UX-UI* |
   | Coachstudenten (één coach) | Nummer, Naam, Project, Gilde, Sem | Geen kolom coach; de app vraagt welke coach |

3. **Namen typen of plakken:** een tekstveld met één studentnaam per regel.
4. **CSV of Excel-cellen plakken:** een tekstveld waarin de gebruiker CSV of uit Excel gekopieerde cellen plakt. De app zoekt naar bruikbare velden: naam, studentnummer, semester, squad (projectgroep), invulling, gilde, coach en gildemeester.

### Koppelen aan Portflow

Studenten die niet via Portflow zijn toegevoegd (manier 2 tot en met 4), koppelt de app **automatisch** aan een portfolio uit de lijst met gedeelde portfolio's: **op naam** (ongevoelig voor hoofdletters en extra spaties). Portflow levert voor zover bekend geen studentnummer. Twijfelgevallen en studenten die niet gevonden worden, legt de app ter controle aan de gebruiker voor.

## Squad (project)

| Veld | Toelichting |
|---|---|
| Naam | Bijvoorbeeld "Cuimed" |
| Volledige naam | Bijvoorbeeld "19 Cuimed" (squadnummer en naam) |
| Kleur en initialen | Voor de weergave |

De gebruiker kan squads toevoegen, bewerken en verwijderen.

## Beroepsrol

De negen beroepsrollen uit [beroepsrollen.md](beroepsrollen.md) zijn de **standaard**. De gebruiker kan rollen toevoegen, bewerken en verwijderen. Velden: code, naam, korte beschrijving.

Wordt een rol verwijderd, dan verdwijnt die bij alle studenten. Studenten voor wie het de primaire rol was, komen bij **Nog in te delen**.

## Kolommen

De kolommen van het studentenoverzicht:

- De **tien vaardigheden** (OC … RE) staan altijd vast, in de vaste volgorde. Ze zijn niet te bewerken of te verwijderen. Hun beschrijving is letterlijk de LEF-tekst ([vaardigheden-niveaus-LEF.md](vaardigheden-niveaus-LEF.md)). De waarde komt uit de evaluaties in Portflow.
- **Eigen kolommen** kan de gebruiker toevoegen, bewerken en verwijderen. Velden: code, naam, beschrijving, type (**percentage** of **vrije tekst**). De gebruiker vult de waarde per student in de tabel in.

## Open vragen

- [x] Keuzelijst coach en gildemeester: een beheerde lijst in Instellingen.
- [x] Student zonder semester of primaire rol: mag tijdelijk, in de groep "Nog in te delen".
- [x] De naam van de gebruiker staat automatisch in de lijst met coaches en gildemeesters.
- [x] Excelbestand: in elk geval de drie vormen uit de console-app (zie hierboven).
- [x] Wat Portflow levert: zie [architectuur.md](architectuur.md#portflow-api).
- [x] Koppelen gaat op naam; Portflow levert voor zover bekend geen studentnummer.
- [ ] Herkent de app bij manier 2 ook andere Excelbestanden, net als bij manier 4?
