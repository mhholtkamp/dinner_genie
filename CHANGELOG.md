## 3.0.10

- Maakt de Savelio card robuuster na het verwijderen van de dagsensoren.
- De card zoekt de weekmenu-sensor nu automatisch als `sensor.dinner_genie_weekmenu` niet bestaat.
- Ondersteunt handmatige override via `weekmenu_entity`.
- Introduceert `custom:savelio-card-v3010` om oude browser-registraties te omzeilen.

## 3.0.9

- Voegt een knop toe om de Savelio boodschappenregels naar de officiele Home Assistant shopping list te sturen.
- De knop gebruikt `todo.shopping_list` via de officiele `todo.add_item` service.

## 3.0.8

- Verwijdert de aparte `Dag 1` t/m `Dag 7` sensors uit de apparaat-eigenschappen.
- Ruimt oude dag-sensors en oude vervang-dag buttons automatisch op uit de Home Assistant entity registry.
- Laat de Savelio card weekmenu-data rechtstreeks uit `sensor.dinner_genie_weekmenu` lezen.
- Werkt de voorbeeld-dashboards bij zodat ze geen losse dagsensoren meer gebruiken.

## 3.0.7

- Introduceert `custom:savelio-card-v307` als nieuwe frontend-tag om oude browser-registraties van `custom:savelio-card` te omzeilen.
- Registreert in de kaartkiezer nog steeds maar één zichtbare `Savelio Card`.
- Werkt de voorbeelden bij zodat de vandaag-kaart altijd de nieuwe renderer gebruikt.

## 3.0.6

- Maakt de dagtegel robuuster door alle dagsensoren op datum te scannen, los van `days_entity`.
- Ondersteunt `mode: today`, `mode: day`, `mode: vandaag` en `mode: dag` voor dezelfde dagtegel.
- Toont in de preview van de dagtegel ook direct de datum van vandaag.

## 3.0.5

- Geeft `days_entity` voorrang bij het aantal zichtbare weekmenu-kaarten.
- Voegt `mode: today` toe voor een kaart met alleen het gerecht van vandaag.
- Laat `title: ""` en `title: false` de kaarttitel echt verbergen.
- Registreert de Savelio card in-place in de Home Assistant kaartkiezer, zodat de preview beter zichtbaar blijft.

## 3.0.4

- Maakt de kaartkiezer-registratie robuuster zodat `Savelio Card` weer als enige custom card zichtbaar is.
- Gebruikt een expliciete preview/stub-config op `custom:savelio-card`.

## 3.0.3

- Verwijdert de `Vernieuwen` knop uit de kop van de weekmenu-card.
- Gebruikt een nieuw Savelio-placeholderpad om oude Dinner Genie placeholder-cache te omzeilen.

## 3.0.2

- Verrijkt opgeslagen weekmenu-maaltijden met volledige receptdetails uit `/recipes`, zodat afbeeldingen, bereiding en ingrediënten beschikbaar blijven.
- Toont daglabels als echte dag met datum, bijvoorbeeld `maandag 13 juli`.
- Verwijdert de lokale vervang/verversknoppen per dag en vervangt de placeholder-afbeelding door Savelio branding.

## 3.0.1

- Leest de actuele weekplanning uit `GET /api/groups/{groupId}/week-menus?limit=1` volgens de API-handleiding.
- Ondersteunt `weekMenus[0]`, `shopping_lines`, `plannedDate` en `dayIndex` uit de opgeslagen weekmenu-response.

## 3.0.0

- Hernoemt de zichtbare integratie en Lovelace card naar Savelio.
- Haalt de actuele weekplanning op via de Savelio API in plaats van deze lokaal in Home Assistant te genereren of te muteren.
- Gebruikt datum- en dagmetadata uit de API voor de dagsensoren en weekplanningkaart.
- Introduceert `custom:savelio-card` als nieuwe kaartnaam, met backwards compatibility voor bestaande Dinner Genie card types.

## 2.4.3

- Ruimt oude Dinner Genie card-picker registraties defensief op, ook als oudere gecachete card-scripts later nog laden.
- Laat de Lovelace card-preview ook renderen zonder Home Assistant entity-data.

## 2.4.2

- Plaatst Dinner Genie icon/logo ook op de repo-root en integratie-root zodat Home Assistant/HACS update-overzichten een afbeelding kunnen tonen.

## 2.4.1

- Toont nog maar één Dinner Genie card in de Home Assistant kaartkiezer.
- Voegt `getStubConfig()` en `preview: true` toe zodat Home Assistant een kaartpreview kan renderen.

## 2.4.0

- Introduceert `custom:dinner-genie-card-v2` als permanente kaartnaam voor de nieuwe frontend-code.
- Houdt `custom:dinner-genie-card` beschikbaar voor backwards compatibility.
- Maakt de weekmenu vernieuwen-knop robuuster als Home Assistant de generate-button entity anders noemt.

## 2.3.9

- Registreert naast `custom:dinner-genie-card` ook `custom:dinner-genie-card-v239` om frontend-cache en oude custom-element registraties te omzeilen.

## 2.3.8

- Verbergt trailing `unavailable`/`unknown` dagen in het weekmenu als het aantal-dagen entity niet beschikbaar is.
- Voegt optionele `debug: true` weergave toe aan de Lovelace card om geladen card-versie en dagenwaarde te controleren.
- Voorkomt fouten bij dubbele custom-card registratie door Home Assistant frontend caching.

## 2.3.7

- Weekmenu-card gebruikt nu `number.dinner_genie_aantal_dagen` om alleen het ingestelde aantal dagen te tonen.
- Weekmenu- en receptenkaarten blijven even hoog als een recept geen categorie heeft.

## 2.3.6

- Serveert de Lovelace card JavaScript zonder statische cache zodat frontend-fixes sneller zichtbaar worden.
- Logt de geladen Dinner Genie card-versie in de browserconsole voor troubleshooting.

## 2.3.5

- Stelt automatische card-renders uit zolang zoek/filter focus actief is of de receptpopup openstaat.
- Blokkeert achtergrondscroll zolang de receptpopup open is.
- Haalt gemiste data-updates pas in nadat zoek/filter focus is verlaten.

## 2.3.4

- Rendert de Lovelace card in Shadow DOM om zoekfocus en popupscroll te isoleren van Lovelace.
- Popup-backdrop blokkeert alleen nog scroll-events die echt op de backdrop zelf plaatsvinden.

## 2.3.3

- Behoudt zoek- en popupstatus als Lovelace de kaartconfig opnieuw aanbiedt.
- Isoleert zoekveld- en filterevents zodat Lovelace de focus niet overneemt.
- Isoleert popup scroll- en touchevents en voorkomt late scroll-reset na openen.

## 2.3.2

- Voorkomt onnodige Lovelace card-renders tijdens zoeken en popupgebruik.
- Zoeken werkt de resultaten bij zonder het zoekveld opnieuw te renderen.
- Receptpopup houdt scrollpositie vast en voorkomt scrollen van de dashboardpagina erachter.

## 2.3.1

- Lovelace card behoudt focus en cursorpositie tijdens zoeken.
- Receptpopup behoudt scrollpositie en scrolt binnen de popup.

## 2.3.0

- Eigen Lovelace card toegevoegd: `custom:dinner-genie-card`.
- Receptenoverzicht toegevoegd via `sensor.dinner_genie_recepten`.
- Card ondersteunt weekmenu en receptenmodus.
- Receptdetails worden in de card getoond.
- Recepten kunnen worden gezocht en gefilterd.
- Voorbeelddashboard voor de Lovelace card toegevoegd.

## 2.2.0

- Knoppen toegevoegd om één dag uit het weekmenu te vervangen.
- Het vervangende gerecht wordt niet gekozen uit gerechten die al in het weekmenu staan.
- Boodschappenlijst wordt na vervanging opnieuw opgebouwd op basis van het actuele weekmenu.
- Bestaande afvinkstatus blijft behouden voor ongewijzigde boodschappenregels.

## 2.1.5

- Voorbeeld dashboards toegevoegd.
- Compleet sections dashboard toegevoegd.
- Minimal dashboard toegevoegd.
- Mobile dashboard toegevoegd.
- Voorbeelden staan in `examples/` en `custom_components/dinner_genie/examples/`.

# Changelog

## 2.1.4

- Boodschappenlijst is nu een echte bewerkbare to-do lijst.
- Items kunnen worden afgevinkt, toegevoegd, aangepast en verwijderd.
- Nieuwe weekmenu-generatie vervangt de boodschappenlijst met nieuwe items.

## 2.1.3

- Added bundled recipe placeholder image.
- Registered Dinner Genie static assets in Home Assistant.
- Day recipe sensors now expose `display_image`, fallback `image_url`, and `has_recipe_image`.


## v2.1.1

- GitHub Actions toegevoegd voor Hassfest, HACS-validatie en Python syntax checks.
- `CHANGELOG.md`, `CONTRIBUTING.md` en repository-afbeeldingen toegevoegd.

## v2.1.0

- Dagsensoren toegevoegd: `sensor.dinner_genie_dag_1` t/m `sensor.dinner_genie_dag_7`.
- Receptdetails toegevoegd aan de attributes van dagsensoren.

## v2.0.0

- Eigen `number` entities toegevoegd voor aantal dagen en personen.
- Knoppen toegevoegd voor weekmenu genereren en willekeurig gerecht kiezen.
- Select entities toegevoegd voor dieet en recepttype.
- Boodschappenlijst als `todo` entity toegevoegd.

## 2.1.2

- Added `ingredients_formatted` and `ingredients_markdown` attributes based on `ingredientsV2` for cleaner recipe popups.
