# Releases maken

Een nieuwe versie van het dashboard publiceren, zodat gebruikers hem kunnen installeren en de app een melding toont ([spec 020](../features/020-installatie/spec.md)). Met Claude Code gaat dit met **`/release`**; die skill volgt dit document. Zonder Claude Code volg je de stappen hieronder zelf.

## Wat er gebeurt

Een tag `vX.Y.Z` pushen start de workflow [`.github/workflows/release.yml`](../.github/workflows/release.yml):

1. de tests op macOS en Windows; de versie in de code moet gelijk zijn aan de tag, en de releasenote `releases/vX.Y.Z.md` moet bestaan;
2. een zip van de code met de SHA-256-controlesom;
3. de installatiescripts proberen op een schone Mac en een schone Windows-machine: installeren, starten, versie controleren, afsluiten, verwijderen;
4. de release op GitHub met de bijlagen `portflow-coach-dashboard.zip`, `portflow-coach-dashboard.zip.sha256`, `install-macos.sh` en `install-windows.ps1`, en als tekst de releasenote met daaronder de installatieregels uit [`install/release-installatie.md`](../install/release-installatie.md). De app toont bij "Wat is er nieuw" alleen de releasenote.

Faalt een stap, dan komt er geen release. Herstel de fout, verwijder de tag (`git tag -d vX.Y.Z` en `git push origin :refs/tags/vX.Y.Z`) en begin opnieuw.

Gebruikers installeren altijd de nieuwste release via de vaste adressen `https://github.com/petersnoek-hu/portflow-coach-dashboard/releases/latest/download/<bestand>` (R3). Het dashboard controleert bij het starten en dagelijks op een nieuwe versie (U1).

## Stappenplan

1. **Klaar om te releasen?** De werkmap is schoon (`git status`), je staat op `main`, `main` is gelijk aan GitHub (`git pull`), en alle tests slagen (`python -m unittest`). Kijk ook of de workflow **Tests** voor de laatste commit groen is (`gh run list --workflow tests.yml --limit 1`): die draait de tests bij elke push naar `main` op macOS en Windows, zodat een fout die alleen op Windows optreedt niet pas bij de release opvalt.
2. **Wat is er veranderd?** Bekijk de commits sinds de vorige release (`git log --oneline vVORIGE..HEAD`) en de nieuwe regels in de logboeken van de specs (`git diff vVORIGE..HEAD -- features/`). Bij de eerste release is er geen vorige tag: neem dan alles.
3. **Welk versienummer?** `MAJOR.MINOR.PATCH`:
   - **patch** (1.2.0 → 1.2.1): alleen fouten opgelost, niets nieuws;
   - **minor** (1.2.1 → 1.3.0): iets nieuws of merkbaar verbeterd, en alles werkt zoals de gebruiker gewend is;
   - **major** (1.3.0 → 2.0.0): de gebruiker moet iets anders doen dan hij gewend is, of gegevens veranderen ingrijpend.
4. **Releasenote schrijven** in `releases/vX.Y.Z.md`, met het sjabloon hieronder. Met `/release` zet Claude een voorstel in dat bestand klaar; de beheerder bekijkt en bewerkt het zelf en geeft akkoord. Pas daarna gaat de tekst (zoals hij dan in het bestand staat) mee in de release.
5. **Versienummer zetten** op drie plekken: `VERSION` in [`dashboard/version.py`](../dashboard/version.py), `version` in [`pyproject.toml`](../pyproject.toml) en het blok `name = "portflow-coach-dashboard"` in [`uv.lock`](../uv.lock) (met uv: `uv lock`; zonder uv: pas die ene regel `version = …` met de hand aan). Een test controleert dat ze gelijk zijn.
6. **Commit en tag:** `git commit -am "Versie X.Y.Z"` (met `dashboard/version.py`, `pyproject.toml` en `uv.lock`) (met de nieuwe releasenote erbij: `git add releases/vX.Y.Z.md`), `git tag vX.Y.Z`.
7. **Publiceren:** `git push origin main vX.Y.Z`.
8. **Volgen:** op GitHub onder *Actions* (of `gh run watch`). Dat duurt meestal ongeveer 5 minuten (geslaagde runs: 4 à 6,5 minuut). Als alles groen is, staat de release onder *Releases*.

## Releasenote

De releasenote is voor **gebruikers zonder technische kennis**: coaches en gildemeesters. De app toont hem bij "Wat is er nieuw" in de updatebalk.

- Schrijf in gewone taal wat de gebruiker merkt, niet hoe het gebouwd is. Geen code-, bestands- of functienamen, geen specnummers, geen Engelse vaktermen als er een gewoon woord voor is.
- Gebruik de woorden van de interface ("Overzicht", "Evaluaties", "Verversen") en van [begrippen.md](begrippen.md).
- Geen studentgegevens: geen namen, ook niet als voorbeeld.
- Ontwikkelingsgericht en vriendelijk, zoals de interface ([design-system.md](design-system.md)).
- Kort: per punt één zin, hoogstens twee. Laat lege kopjes weg.
- Moet de gebruiker iets doen (opnieuw inloggen, een instelling controleren)? Zet dat bovenaan onder "Let op".

Sjabloon (Markdown; de app toont kopjes, opsommingen en **vet**):

```markdown
## Let op
- Wat de gebruiker na het bijwerken zelf moet doen. Laat dit kopje weg als er niets te doen is.

## Nieuw
- Wat er nu kan dat eerst niet kon, en waar je het vindt.

## Verbeterd
- Wat beter, sneller of duidelijker werkt.

## Opgelost
- Welk probleem niet meer voorkomt, beschreven zoals de gebruiker het merkte.
```

Voorbeeld:

```markdown
## Nieuw
- Op de pagina **Evaluaties** zie je per week hoeveel evaluaties je studenten hebben gekregen en hoeveel er nog op beoordeling wachten.
- Onder **Te beoordelen** staan de evaluatieverzoeken die op jou wachten, het langst wachtende bovenaan.

## Opgelost
- Evaluaties van vaardigheden waarvan de naam in Portflow anders gespeld is, tellen nu ook mee.
```
