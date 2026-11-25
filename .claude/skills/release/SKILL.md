---
name: release
description: Publiceer een nieuwe versie van het Portflow coach dashboard op GitHub (spec 020, R4). Controleert of alles klaar is, stelt de versie voor, schrijft samen met de beheerder een Nederlandse releasenote voor gebruikers zonder technische kennis, en pusht pas na een uitdrukkelijk "ja". Gebruik bij "/release", "maak een release", "nieuwe versie publiceren".
---

# /release

Je helpt de beheerder een release te maken. Het stappenplan, de regels voor het versienummer en het sjabloon van de releasenote staan in `docs/releases.md`: **lees dat document eerst** en volg het. Communiceer in het Nederlands.

Belangrijk:
- **Push niets zonder een uitdrukkelijk "ja" van de beheerder op de vraag of je mag publiceren.** Een akkoord op de releasenote is nog geen akkoord op publiceren. Zegt de beheerder iets anders dan ja, dan push je niet.
- Geen studentgegevens en geen tokens in de releasenote of de commit.
- Wijzig geen code buiten het versienummer en de releasenote. Is er iets te herstellen, stop dan en meld het.

## 1. Klaar om te releasen?

Controleer en meld de uitkomst kort:
- `git status --short` is leeg (anders: stop en vraag of de wijzigingen eerst gecommit moeten worden);
- de huidige branch is `main`, en `git fetch` gevolgd door `git status -sb` laat zien dat `main` niet achterloopt op `origin/main` (loopt hij voor, dan gaan die commits mee met de release: noem ze);
- alle tests slagen: `.venv/bin/python -m unittest` (of `python -m unittest`). Faalt er een, stop dan.
- de workflow **Tests** voor de laatste commit op `main` is geslaagd op macOS en Windows: `gh run list --workflow tests.yml --branch main --limit 1`. Loopt hij nog, wacht dan; is hij mislukt, stop dan en meld welke test op welk systeem faalde.

## 2. Wat is er veranderd, en welke versie?

- Vind de vorige release: `git describe --tags --abbrev=0` (geen tag: dit is de eerste release, neem alle geschiedenis).
- Verzamel de veranderingen: `git log --oneline <vorige>..HEAD` en de nieuwe logboekregels in de specs (`git diff <vorige>..HEAD -- features/`), plus `features/README.md` voor de status van de specs.
- De huidige versie staat in `dashboard/version.py`.
- Stel met **AskUserQuestion** de vraag "Welke versie wordt het?" met de opties patch, minor en major (met het nieuwe nummer erbij, bijvoorbeeld "Minor: 1.3.0"), jouw voorstel als eerste optie met "(Recommended)", en een korte reden volgens de regels in `docs/releases.md`. Bij de eerste release is het voorstel het nummer dat al in `dashboard/version.py` staat.

## 3. Releasenote schrijven

Schrijf de releasenote volgens het sjabloon en de schrijfregels in `docs/releases.md`. Denk vanuit de gebruiker: een coach of gildemeester zonder technische kennis. Vertaal elke technische verandering naar wat die gebruiker merkt; laat interne verbeteringen (tests, opruimen, documentatie, specs) weg, tenzij de gebruiker er iets van merkt. Bundel kleine dingen. Kijk bij twijfel in de spec van de functie wat het voor de gebruiker betekent.

Schrijf de tekst naar `releases/vX.Y.Z.md`. Zet hem daar klaar zodat de beheerder hem zelf kan bekijken en bewerken: open het bestand in de bestandsweergave (in de desktop-app met `mcp__ccd_view__show_pane`, anders als klikbare link [releases/vX.Y.Z.md](releases/vX.Y.Z.md)) en laat de tekst ook in de chat zien.

## 4. Akkoord op de tekst

Zeg dat de beheerder de tekst in `releases/vX.Y.Z.md` zelf mag aanpassen en een seintje geeft als hij goed is. Vraag dan met **AskUserQuestion** of de releasenote klaar is, met de opties "Akkoord, tekst is goed" en "Pas jij hem aan". Ga verder pas na een uitdrukkelijk akkoord.

- **Lees het bestand na het akkoord altijd opnieuw** van schijf: de beheerder kan het intussen zelf hebben bewerkt. Werk vanaf dan met die tekst; overschrijf zijn wijzigingen niet. Laat kort zien wat er ten opzichte van jouw versie veranderd is (of dat er niets veranderd is).
- Controleer de bewerkte tekst op studentgegevens en tokens; staat er iets in, meld het en vraag opnieuw.
- Bij "Pas jij hem aan": verwerk de wensen in het bestand (lees het eerst opnieuw, zodat je zijn eigen bewerkingen niet weggooit) en vraag opnieuw, tot de beheerder akkoord is.

## 5. Publiceren, alleen na "ja"

1. Zet het versienummer in `dashboard/version.py` (`VERSION`), `pyproject.toml` (`version`) en `uv.lock` (de regel `version = …` in het blok `name = "portflow-coach-dashboard"`; met uv kan dat met `uv lock`).
2. Draai de tests nog een keer (een test controleert dat de drie nummers gelijk zijn).
3. Laat zien wat er gaat gebeuren: de commit "Versie X.Y.Z" met de drie nummers en de releasenote, de tag `vX.Y.Z`, en `git push origin main vX.Y.Z`. Vraag dan met **AskUserQuestion**: "Versie X.Y.Z publiceren op GitHub?" met de opties "Ja, publiceren" en "Nee, nog niet".
4. Alleen bij "Ja, publiceren": `git add dashboard/version.py pyproject.toml uv.lock releases/vX.Y.Z.md`, `git commit -m "Versie X.Y.Z"` (met de attributieregels die voor commits gelden), `git tag vX.Y.Z`, `git push origin main vX.Y.Z`.
   Bij "Nee": laat de wijzigingen staan, commit niet, en zeg hoe de beheerder later verder kan (`/release` opnieuw, of de stappen in `docs/releases.md`).

## 6. Volgen

Volg de workflow met `gh run list --workflow release.yml --limit 1` en `gh run watch <id> --exit-status` (op de achtergrond). Zeg daarbij hoe lang het normaal duurt: **ongeveer 5 minuten** (geslaagde runs duurden 4 à 6,5 minuut; een run die faalt stopt vaak eerder, na 3 à 5 minuten). Bijvoorbeeld: "Ik volg hem en meld de uitkomst zodra hij klaar is; dat duurt meestal ongeveer 5 minuten." Meld daarna:
- gelukt: het adres van de release (`gh release view vX.Y.Z --json url -q .url`) en dat gebruikers de melding binnen een dag krijgen (of direct, als ze de app opnieuw starten);
- mislukt: welke stap faalde en de relevante regels uit `gh run view <id> --log-failed`, en het herstel uit `docs/releases.md` (fout herstellen, tag verwijderen, opnieuw). Verwijder de tag niet zelf zonder te vragen.
