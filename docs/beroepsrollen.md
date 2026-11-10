# Beroepsrollen

Een student heeft nul of meer beroepsrollen, zonder volgorde of "primair", elk met een eigen gildemeester ([spec 016](../features/016-gildes-van-een-student/spec.md)). Bij elke beroepsrol hoort hoogstens één **gilde** ([gildes-openict.md](gildes-openict.md), [gegevensmodel.md](gegevensmodel.md#gilde)), waarin de gildemeester de productvaardigheden (OC, KO, JKO, KPM) beoordeelt; het gilde van een student volgt uit zijn primaire beroepsrol. Zie ook [begrippen](begrippen.md).

In LEF staan per beroepsrol voorbeelden van producten die bij die rol passen (zie [KPM in vaardigheden-niveaus-LEF.md](vaardigheden-niveaus-LEF.md#kpm)).

| Code | Beroepsrol |
|---|---|
| **UX** | UI/UX designer |
| **BIT** | Business IT engineer |
| **CS** | Cybersecurity engineer |
| **CI** | Cloud & Infra engineer |
| **FE** | Front-end developer |
| **BE** | Back-end developer |
| **AI** | AI engineer |
| **GD** | Game developer |
| **TI** | Embedded technologie engineer |

Het dashboard start zonder beroepsrollen; deze negen zijn met de knop "Open-ICT-beroepsrollen toevoegen" in één keer toe te voegen. Het dashboard leest ze uit de tabel hierboven (vorm `| **CODE** | Naam |`). De gebruiker kan rollen toevoegen, bewerken en verwijderen (zie [gegevensmodel.md](gegevensmodel.md#beroepsrol) en [spec 008](../features/008-beroepsrollen/spec.md)). Gebruik deze codes en namen; de afwijkende namen in het ontwerp (zoals "BIT engineer") zijn niet bindend. In de tabellen heet de kolom met de beroepsrollen van een student "Gilde" ([spec 016](../features/016-gildes-van-een-student/spec.md)).

## Open vragen

- [ ] Hangen de beroepsrollen samen met de [HBO-i-beroepstaken](HBOi-beroepstaken.md), en zo ja, hoe? (Beroepstaken komen later in het dashboard.)
- [x] Verwijderen van een rol: die verdwijnt bij de studenten; wie daarna geen gilde meer heeft, komt bij "Nog in te delen" (zie [gegevensmodel.md](gegevensmodel.md#beroepsrol)).