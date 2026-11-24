# Gildes van Open-ICT

De gildes van Open-ICT, elk met zijn beroepsrol. Bij elke beroepsrol ([beroepsrollen.md](beroepsrollen.md)) hoort precies één gilde, met dezelfde code; in het dashboard is de beroepsrol daarom een veld van het gilde ([spec 018](../features/018-beroepsrol-in-gilde/spec.md)). Het dashboard leest deze tabel voor de knop "Open-ICT-gildes toevoegen" op de pagina Gilde toevoegen ([spec 006](../features/006-gildemeesters/spec.md), F14; spec 018, F4). Eén gilde per regel, in de vorm `| **CODE** | Gilde | Beroepsrol | Kleur |`. De kleuren zijn die van [LEF](https://lef.hu.nl/beroepsproducten) (CSS-variabelen `--guild-…-color`, overgenomen op 2026-11-23; LEF noemt UX `UI/UX`). Dit is de enige lijst met codes en namen van gildes en beroepsrollen.

| Code | Gilde | Beroepsrol | Kleur |
|---|---|---|---|
| **UX** | UI/UX gilde | UI/UX designer | `#880E4F` |
| **BIT** | Business IT gilde | Business IT engineer | `#9A7300` |
| **CS** | Cybersecurity gilde | Cybersecurity engineer | `#085308` |
| **CI** | Cloud & Infra gilde | Cloud & Infra engineer | `#59C759` |
| **FE** | Front-end gilde | Front-end developer | `#D35400` |
| **BE** | Back-end gilde | Back-end developer | `#B71C1C` |
| **AI** | AI gilde | AI engineer | `#4B0082` |
| **GD** | Game development gilde | Game developer | `#8950C7` |
| **TI** | Embedded technologie gilde | Embedded technologie engineer | `#001F3F` |