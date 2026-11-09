# portflow-coach-dashboard

Een dashboard voor coaches en gildemeesters van Open-ICT (Hogeschool Utrecht). Het toont per groep studenten de voortgang op de tien LEF-vaardigheden. De evaluaties komen uit de onofficiële Portflow API; studenten en hun indeling beheert de gebruiker in het dashboard zelf. Het draait lokaal op de laptop van de gebruiker.

*A custom-built Portflow dashboard that shows Portflow progress for different groups of students, using the unofficial Portflow API.*

## Werkwijze

Elke functie wordt eerst beschreven en daarna gebouwd. Zie [`features/README.md`](features/README.md).

## Mappen

| Map | Inhoud |
|---|---|
| [`features/`](features/) | Eén map per functie met spec (eisen) en ontwerpen; sjabloon in `features/_sjabloon/` |
| [`docs/`](docs/) | Gedeelde documentatie: begrippen, vaardigheden, voortgangsregels, gegevensmodel, beroepsrollen, beroepstaken, design system, architectuur |
| [`screenshots/`](screenshots/) | Ontwerpen en referentiebeelden die meerdere functies betreffen |
| [`CLAUDE.md`](CLAUDE.md) | Werkafspraken voor Claude Code |

## Documentatie

- [Begrippen](docs/begrippen.md): domeintaal van Open-ICT
- [Vaardigheden (overzicht)](docs/vaardigheden-openict.md) en [vaardigheden per niveau (LEF)](docs/vaardigheden-niveaus-LEF.md)
- [Voortgangsregels](docs/voortgangsregels.md): evaluaties, semester behaald en weergave van niveaus
- [Beroepsrollen](docs/beroepsrollen.md) en [HBO-i-beroepstaken](docs/HBOi-beroepstaken.md)
- [Gegevensmodel](docs/gegevensmodel.md): welke gegevens uit Portflow komen en welke het dashboard zelf bijhoudt
- [Design system](docs/design-system.md): schermen uit de ontwerpen, kleuren en componenten
- [Architectuur](docs/architectuur.md): techstack, Portflow-gebruik, privacy, beslissingen
- [Portflow API](docs/portflow-API-reverse-engineer.md) (onofficieel) en de bestaande [console-app](docs/portflow-console-app.py)
