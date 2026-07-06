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
