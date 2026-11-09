# Portflow Coach Dashboard

Dashboard voor Open-ICT-coaches (primaire gebruiker) en gildemeesters (secundaire gebruiker; iemand kan beide zijn). Het toont de voortgang van groepen studenten op de tien LEF-vaardigheden, op basis van de onofficiële Portflow API. Communiceer met de gebruiker in het Nederlands.

## Werkwijze: eerst de spec, dan de code

Volg dit bij **elke** functie, ook als de gebruiker alleen "bouw X" zegt:

1. **Elke functie heeft een spec** in `features/NNN-naam/spec.md`. Bestaat die nog niet? Maak hem eerst: kopieer `features/_sjabloon/`, neem het volgende vrije nummer, vul in wat bekend is en leg de spec voor aan de gebruiker voordat je bouwt.
2. **Lees voor het bouwen** de spec, de afbeeldingen in `design/` van die functie, de relevante delen van `screenshots/` en de gedeelde documenten in `docs/`.
3. **Bouw pas als de spec "uitgewerkt" is** (zie de checklist in `features/README.md`). Onduidelijk of tegenstrijdig? Vraag het na en zet de vraag onder *Open vragen* in de spec. Vul ontbrekende eisen niet zelf in.
4. **Tijdens en na het bouwen:** vink gerealiseerde eisen af, zet de **Status** bij, voeg een regel toe aan het **Logboek** en werk de tabel in `features/README.md` bij.
5. **Wijkt de bouw af van de spec?** Pas eerst de spec aan, na overleg met de gebruiker.

## Gedeelde documentatie (één bron per onderwerp)

| Onderwerp | Bron |
|---|---|
| Domeintaal (squad, tribe, gilde, coach, gildemeester, …) | `docs/begrippen.md` |
| Vaardigheden: codes, volgorde, categorieën | `docs/vaardigheden-openict.md` |
| Vaardigheden: volledige LEF-tekst per niveau | `docs/vaardigheden-niveaus-LEF.md` |
| Evaluaties, toetsprogramma per semester, semester behaald, weergave van niveaus | `docs/voortgangsregels.md` |
| Beroepsrollen en codes | `docs/beroepsrollen.md` |
| HBO-i-beroepstaken | `docs/HBOi-beroepstaken.md` |
| Gegevens: bron, studentvelden, studenten toevoegen, kolommen, gebruiker | `docs/gegevensmodel.md` |
| Schermen, kleuren, niveaulabels, componenten, toon | `docs/design-system.md` |
| Techstack, Portflow-gebruik (inloggen, endpoints, verversen), privacy, beslissingen | `docs/architectuur.md` |
| Portflow API, volledige gereverse-engineerde beschrijving | `docs/portflow-API-reverse-engineer.md` |
| Bestaande console-app (referentiecode, niet de webapp; bij verschil gelden de docs) | `docs/portflow-console-app.py` |
| Visuele richting (ontwerpen; "Kompas" is een werktitel) | `screenshots/*-CRUD-*.png`, `screenshots/kompas-dashboard-ontwerp.png`; beschreven in `docs/design-system.md` |

- Neem domeinfeiten over uit deze bronnen; herhaal ze niet in specs of code-commentaar, maar verwijs ernaar.
- Komt er een nieuwe gedeelde keuze of nieuw domeinfeit bij? Leg het vast in het juiste document in `docs/`, op één plek.
- Plaatst de gebruiker nieuwe bestanden, bekijk dan met `ls` of `find` wat er nieuw is. Nieuwe bestanden worden niet automatisch gemeld.

## Domeinregels

- Vaardigheden altijd in deze volgorde en met deze codes: OC, KO, JKO, KPM, PL, BD, SW, FO, PH, RE.
- Niveaus: startniveau, 1, 2, 3, 4 (in de interface `0`, `1` … `4`; startniveau = `0`).
- Productvaardigheden worden beoordeeld door de gildemeester, sociale en persoonsvormende vaardigheden door de coach.
- Regels voor voortgang (semester behaald, weergave `-/-`, `1`, `1/2`) staan alleen in `docs/voortgangsregels.md`. Implementeer ze op één plek in de code en test ze.
- `SW` en `RE` zijn vaardigheden (Samenwerken, Reflecteren) én onderdeel van HBO-i-codes (Software, Realiseren). Gebruik voor beroepstaken altijd de volledige code, bijvoorbeeld `SW-RE`.
- LEF-teksten letterlijk overnemen; niet herformuleren.
- Interface in het Nederlands, ontwikkelingsgericht geformuleerd (niet beoordelend).

## Regels

- Code staat niet in `features/`; die map bevat alleen specs en ontwerpen.
- Geheimen (Portflow-tokens, wachtwoorden) alleen in `.env`, nooit in code, specs of commits.
- Geen echte studentgegevens in testdata, screenshots of de repository. Gebruik verzonnen namen in testdata. De huidige ontwerpscreenshots bevatten echte namen en staan in `.gitignore`; haal ze daar pas uit als ze geanonimiseerd zijn.
- Waar ontwerp en docs verschillen, gelden de docs (bekende afwijkingen staan in `docs/design-system.md`).
