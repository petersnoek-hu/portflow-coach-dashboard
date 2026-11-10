# 018 – Beroepsrol als onderdeel van het gilde

**Status:** klaar <!-- idee | uitgewerkt | in bouw | klaar -->
**Laatst bijgewerkt:** 2026-11-10

> Vervangt de beheerpagina's van [spec 008 – Beroepsrollen](../008-beroepsrollen/spec.md) en wijzigt [spec 006](../006-gildemeesters/spec.md) (F12–F19) en [spec 016](../016-gildes-van-een-student/spec.md).

## Doel

Als **coach** of **gildemeester** wil ik gildes en beroepsrollen op één plek beheren, zodat ik bij het inrichten niet twee keer dezelfde lijst hoef toe te voegen en een student nooit een beroepsrol zonder gilde kan hebben.

Bij Open-ICT heeft **elke beroepsrol precies één gilde** (bevestigd door de gebruiker, 2026-11-10). Beroepsrollen en gildes waren tot nu toe twee lijsten met elk een eigen pagina, één-op-één gekoppeld. Het begrip beroepsrol blijft bestaan ([begrippen.md](../../docs/begrippen.md)), maar is voortaan een veld van het gilde, en niet meer een eigen lijst.

## Gebruikers

- [x] Coach
- [x] Gildemeester
- Geen verschil.

## Betrokken begrippen

- Gilde, beroepsrol, gildemeester ([begrippen.md](../../docs/begrippen.md), [gegevensmodel.md](../../docs/gegevensmodel.md#gilde))

## Functionele eisen

- [x] **F1 – Geen pagina Beroepsrollen meer.** Het menu-item Beroepsrollen (onder Beheer) en de pagina's om beroepsrollen te bekijken, toe te voegen, te bewerken en te verwijderen verdwijnen. Een oude link naar `/beroepsrollen` gaat naar Gildes.
  - *Acceptatie:* het menu Beheer toont Semesters, Gildes, Gildemeesters, Coaches, Projecten en Kolommen; `/beroepsrollen` opent Gildes.
- [x] **F2 – Velden van een gilde.** Een gilde heeft: **code** (2 of 3 letters, uniek), **naam** (verplicht, bijvoorbeeld "Front-end gilde"), **beroepsrol** (verplicht, bijvoorbeeld "Front-end developer"), **beschrijving** van de beroepsrol (niet verplicht) en **kleur**. Het formulier Gilde aanmaken en Gilde bewerken heeft deze velden; de keuzelijst met beroepsrollen en de melding "Voeg eerst beroepsrollen toe" verdwijnen.
  - *Acceptatie:* een gilde aanmaken met code "fe", naam "Front-end gilde" en beroepsrol "Front-end developer" lukt zonder dat er beroepsrollen bestaan; zonder beroepsrol weigert de app met "Vul een beroepsrol in.".
- [x] **F3 – Kaart.** De gildekaart toont de code in een vlak met de kleur van het gilde, de naam, de beroepsrol, het aantal gildemeesters en studenten, de avatars van de gildemeesters en de knoppen Bewerken en Verwijderen (zoals [spec 006, F13](../006-gildemeesters/spec.md)).
- [x] **F4 – Open-ICT-gildes.** De knop "Open-ICT-gildes toevoegen" voegt de negen gildes toe met hun naam én beroepsrol uit één tabel in [`docs/gildes-openict.md`](../../docs/gildes-openict.md) (`| Code | Gilde | Beroepsrol |`). Een code die al bestaat, wordt overgeslagen. De Open-ICT-gildemeesters ([spec 006, F11](../006-gildemeesters/spec.md)) voegen ontbrekende gildes op dezelfde manier toe.
  - *Acceptatie:* een leeg dashboard + de knop → 9 gildes, onder wie FE "Front-end gilde" met beroepsrol "Front-end developer"; nog een keer → 0.
- [x] **F5 – Verwijderen.** Na bevestiging verdwijnt het gilde, **ook bij de studenten** die het hadden; wie daarna geen gilde meer heeft, komt bij "Nog in te delen". Gildemeesters houden hun rol, zonder dit gilde. De bevestiging noemt het aantal studenten en gildemeesters ("Bij 3 studenten verdwijnt dit gilde; 1 van hen heeft geen ander gilde en komt bij Nog in te delen. Het gilde heeft 2 gildemeesters; zij houden hun rol, maar niet meer dit gilde.").
  - *Acceptatie:* een student met alleen gilde FE staat na het verwijderen van FE onder "Nog in te delen".
- [x] **F6 – Gilde kiezen bij een student.** Bij Student bewerken en Student toevoegen kies je per regel een **gilde** ("FE · Front-end gilde") en een gildemeester ([spec 016](../016-gildes-van-een-student/spec.md), F4).
- [x] **F7 – Filter Gilde.** Het filter "Beroepsrol" in de werkbalk van Overzicht en Studenten heet voortaan **Gilde** en toont de gildes ("FE · Front-end gilde").
- [x] **F8 – Excel-import.** Een gildekolom ([spec 013](../013-excel-importeren/spec.md)) herkent een gilde aan zijn code, naam of beroepsrol.
  - *Acceptatie:* "FE", "Front-end gilde" en "Front-end developer" worden alle drie het gilde FE.
- [x] **F9 – Omzetten van bestaande gegevens.** Bij het starten:
  - een bestaand gilde krijgt de naam en beschrijving van zijn beroepsrol;
  - een beroepsrol **zonder** gilde wordt een gilde met de code en kleur van de rol, de naam uit de Open-ICT-lijst (F4) of anders de naam van de rol, en de rol als beroepsrol;
  - de gildes van studenten (met hun gildemeester) blijven behouden, nu gekoppeld aan het gilde;
  - de lijst met beroepsrollen verdwijnt.
  - *Acceptatie:* een student met beroepsrol FE (gilde FE) en gildemeester X heeft daarna gilde FE met gildemeester X; een rol GD zonder gilde wordt het gilde GD "Game development gilde" met beroepsrol "Game developer".
- [x] **F10 – Demodata.** De demodata voegen alleen nog gildes toe (met beroepsrol, beschrijving en kleur); de telling bij Instellingen noemt geen beroepsrollen meer.

### Buiten scope

- Een gilde met meer beroepsrollen, of een beroepsrol zonder gilde: bij Open-ICT komt dat niet voor.
- De koppeling van beroepsrollen met HBO-i-beroepstaken (open vraag in [beroepsrollen.md](../../docs/beroepsrollen.md)).

## Schermen

Geen nieuw ontwerp; de pagina Gildes en het gildeformulier krijgen de velden van F2.

## Data

- **Bron:** eigen opslag.
- **Benodigde velden:** per gilde code, naam, beroepsrol, beschrijving, kleur. Per student nul of meer gildes, elk met een gildemeester.
- **Privacy:** geen nieuwe gegevens.

## Technische eisen

- De tabel `guilds` krijgt `role_name` en `description`; de koppeling `student_guilds` verwijst naar `guilds` in plaats van naar `professional_roles`; de tabel `professional_roles` en `guilds.role_id` vervallen. Migratie bij het starten (F9).
- Tests voor F2 (controle), F4, F5, F8 en F9.

## Open vragen

- [x] **Heeft elke beroepsrol precies één gilde?** Ja (gebruiker, 2026-11-10).
- [x] **Wat gebeurt er met de beschrijving van een beroepsrol?** Die verhuist naar het gilde (veld *beschrijving*), zodat er bij het omzetten niets verloren gaat. *Keuze bij het bouwen, ter controle.*
- [x] **Gilde verwijderen:** het gilde verdwijnt bij de studenten, zoals eerder bij het verwijderen van een beroepsrol (spec 008, F8). Eerder bleven studenten bij het verwijderen van een gilde ongewijzigd, omdat hun beroepsrol bleef staan; dat kan niet meer. *Keuze bij het bouwen, ter controle.*

## Logboek

- 2026-11-10 – spec aangemaakt op verzoek van de gebruiker, na advies: beroepsrol wordt een veld van het gilde, de pagina's Beroepsrollen verdwijnen
- 2026-11-10 – gebouwd en getest; status klaar
