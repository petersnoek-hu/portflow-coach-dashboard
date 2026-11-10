# Beroepsrollen

Een student heeft nul of meer gildes (en daarmee beroepsrollen), zonder volgorde of "primair", elk met een eigen gildemeester ([spec 016](../features/016-gildes-van-een-student/spec.md)). Bij elke beroepsrol hoort precies één **gilde** ([gildes-openict.md](gildes-openict.md), [gegevensmodel.md](gegevensmodel.md#gilde)), waarin de gildemeester de productvaardigheden (OC, KO, JKO, KPM) beoordeelt. Zie ook [begrippen](begrippen.md).

In LEF staan per beroepsrol voorbeelden van producten die bij die rol passen (zie [KPM in vaardigheden-niveaus-LEF.md](vaardigheden-niveaus-LEF.md#kpm)).

De codes en namen van de beroepsrollen staan, samen met hun gilde, in [gildes-openict.md](gildes-openict.md). In het dashboard is de beroepsrol een veld van het gilde ([spec 018](../features/018-beroepsrol-in-gilde/spec.md)); er is geen aparte lijst met beroepsrollen. Gebruik deze codes en namen; de afwijkende namen in het ontwerp (zoals "BIT engineer") zijn niet bindend. In de tabellen heet de kolom met de gildes van een student "Gilde" ([spec 016](../features/016-gildes-van-een-student/spec.md)).

## Open vragen

- [ ] Hangen de beroepsrollen samen met de [HBO-i-beroepstaken](HBOi-beroepstaken.md), en zo ja, hoe? (Beroepstaken komen later in het dashboard.)
- [x] Verwijderen van een gilde (en daarmee de beroepsrol): het verdwijnt bij de studenten; wie daarna geen gilde meer heeft, komt bij "Nog in te delen" (zie [gegevensmodel.md](gegevensmodel.md#gilde)).