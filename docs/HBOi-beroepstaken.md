# HBO-i-beroepstaken

Het HBO-i-beroepsprofiel beschrijft ICT-beroepstaken als een combinatie van een **architectuurlaag** en een **activiteit**: 5 lagen × 5 activiteiten = 25 beroepstaken. Elke beroepstaak heeft een code `LAAG-ACTIVITEIT`, bijvoorbeeld `SW-RE` voor *Software Realiseren*.

In LEF geven de beroepstaken houvast bij het bepalen van producten op het juiste niveau (zie [KPM in vaardigheden-niveaus-LEF.md](vaardigheden-niveaus-LEF.md#kpm)).

## Matrix

| Architectuurlaag | Analyseren | Adviseren | Ontwerpen | Realiseren | Manage & Control |
|---|---|---|---|---|---|
| **Gebruikersinteractie** (GI) | GI-AN | GI-AD | GI-ON | GI-RE | GI-MC |
| **Organisatieprocessen** (OP) | OP-AN | OP-AD | OP-ON | OP-RE | OP-MC |
| **Infrastructuur** (IN) | IN-AN | IN-AD | IN-ON | IN-RE | IN-MC |
| **Software** (SW) | SW-AN | SW-AD | SW-ON | SW-RE | SW-MC |
| **Hardware interfacing** (HI) | HI-AN | HI-AD | HI-ON | HI-RE | HI-MC |

## Codes

| Code | Betekenis |
|---|---|
| **GI** | Gebruikersinteractie |
| **OP** | Organisatieprocessen |
| **IN** | Infrastructuur |
| **SW** | Software |
| **HI** | Hardware interfacing |
| **AN** | Analyseren |
| **AD** | Adviseren |
| **ON** | Ontwerpen |
| **RE** | Realiseren |
| **MC** | Manage & Control |

> **Let op dubbele afkortingen:** `SW` is hier de laag *Software*, maar ook de vaardigheid *Samenwerken*. `RE` is hier de activiteit *Realiseren*, maar ook de vaardigheid *Reflecteren*. Gebruik in het dashboard bij beroepstaken altijd de volledige code (`SW-RE`) en bij vaardigheden de losse code (`SW`, `RE`), zodat ze niet verward worden.

## Open vragen

- [x] Worden beroepstaken in het dashboard getoond? Ja, later; bijvoorbeeld op de detailpagina van een student. Hoe precies, volgt nog.
- [x] Komen beroepstaken uit Portflow? Ja: als doel of als subcriterium onder een doel (meestal KPM). De namen zijn rommelig gespeld ("Software Analyzeren", "SW-AN", …); de console-app herkent ze met een ruime naamvergelijking en telt ze per evaluatieverzoek (bijvoorbeeld `3x2, 1x1`). Beroepstaken tellen **niet** mee voor "semester behaald" ([voortgangsregels.md](voortgangsregels.md#welke-evaluaties-tellen)).
