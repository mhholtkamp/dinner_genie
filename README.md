# Savelio Home Assistant integration

![Savelio](images/banner.png)

[![Hassfest](https://github.com/mhholtkamp/dinner_genie/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/mhholtkamp/dinner_genie/actions/workflows/hassfest.yaml)
[![HACS](https://github.com/mhholtkamp/dinner_genie/actions/workflows/hacs.yaml/badge.svg)](https://github.com/mhholtkamp/dinner_genie/actions/workflows/hacs.yaml)
[![Python checks](https://github.com/mhholtkamp/dinner_genie/actions/workflows/python.yaml/badge.svg)](https://github.com/mhholtkamp/dinner_genie/actions/workflows/python.yaml)

Custom integration voor Savelio.

## Installatie via HACS custom repository

1. Voeg deze repository toe in HACS als type `Integration`.
2. Installeer Savelio.
3. Herstart Home Assistant.
4. Ga naar **Instellingen > Apparaten & diensten > Integratie toevoegen**.
5. Kies **Savelio**.
6. Vul in:
   - API basis-URL, bijvoorbeeld `https://savelio.vercel.app/api`
   - Groeps-ID
   - API key

## Entiteiten

De integratie maakt automatisch deze entiteiten aan:

- `number.dinner_genie_aantal_dagen` maximaal 7
- `number.dinner_genie_aantal_personen`
- `button.dinner_genie_genereer_weekmenu` haalt de actuele Savelio weekplanning opnieuw op
- `button.dinner_genie_kies_willekeurig_gerecht`
- `button.dinner_genie_stuur_boodschappen_naar_ha_lijst`
- `button.dinner_genie_leeg_savelio_boodschappenlijst`
- `button.dinner_genie_stuur_boodschappen_naar_ha_en_leeg_savelio`
- `sensor.dinner_genie_aantal_recepten`
- `sensor.dinner_genie_willekeurig_gerecht`
- `sensor.dinner_genie_weekmenu`
- `todo.dinner_genie_boodschappen`
- `select.dinner_genie_dieet`
- `select.dinner_genie_recepttype`

## Gebruik

De weekplanning wordt in de Savelio webinterface gemaakt. Home Assistant haalt de actuele planning op via de API.

Gebruik **Stuur boodschappen naar HA lijst** om de Savelio boodschappenregels toe te voegen aan de officiele Home Assistant shopping list (`todo.shopping_list`).

Gebruik **Leeg Savelio boodschappenlijst** om de lokale Savelio boodschappenlijst leeg te maken. Voeg in Lovelace een `confirmation` toe als je eerst een ja/nee-vraag wilt tonen.

Gebruik **Stuur boodschappen naar HA en leeg Savelio** als je in een keer de boodschappen naar `todo.shopping_list` wilt sturen en daarna de Savelio boodschappenlijst wilt legen. Dit is de aanbevolen knop voor dashboards.

De integratie roept dan aan:

```text
/api/groups/{groupId}/week-menus?limit=1
```

met de waarden uit Home Assistant.

## Maaltijden bekijken

De actuele planning staat in `sensor.dinner_genie_weekmenu`. In de attributes staan onder andere:

- `description`
- `prep_time`
- `category`
- `diet_type`
- `servings`
- `ingredients`
- `ingredients_v2`
- `instructions`
- `image_url`
- `recipe_id`
- `days`
- `meals`

De Savelio Lovelace card leest deze data rechtstreeks uit `sensor.dinner_genie_weekmenu`.


## Afbeeldingen

Als een recept geen `imageUrl` heeft, gebruikt de integratie automatisch de meegeleverde placeholder. Gebruik in dashboards bij voorkeur het attribuut `display_image` of `image_url`.


## Voorbeeld dashboards

Deze repository bevat voorbeeld dashboards:

```text
examples/dashboard_sections.yaml
examples/dashboard_minimal.yaml
examples/dashboard_mobile.yaml
```

Dezelfde voorbeelden staan ook in:

```text
custom_components/dinner_genie/examples/
```

De voorbeelden gebruiken de meegeleverde Savelio Lovelace card.

## Weekplanning beheren

Vanaf v3.0.0 beheert Savelio de weekplanning in de webinterface. Home Assistant vervangt of genereert dagen niet meer lokaal, maar leest de actuele planning en boodschappenlijst uit de API.

## Lovelace card

Vanaf v2.3.0 bevat Savelio een eigen Lovelace card. Voeg deze resource toe in Home Assistant:

```text
/api/dinner_genie/www/dinner-genie-card.js
```

Type: JavaScript module.

Als Home Assistant een oude versie blijft laden, voeg tijdelijk een versie-query toe, bijvoorbeeld:

```text
/api/dinner_genie/www/dinner-genie-card.js?v=3.0.19
```

Gebruik voor nieuwe dashboards de v2-kaart. Die omzeilt oude frontend-registraties van eerdere card-versies:

```yaml
type: custom:savelio-card-v3017
mode: week
title: Savelio weekplanning
days_entity: number.dinner_genie_aantal_dagen
weekmenu_entity: sensor.dinner_genie_weekmenu
# Tijdelijk aanzetten bij frontend-cache of entity-problemen:
# debug: true
```

Voorbeeld weekmenu:

```yaml
type: custom:savelio-card-v3017
mode: week
title: Savelio weekplanning
days_entity: number.dinner_genie_aantal_dagen
# Tijdelijk aanzetten bij frontend-cache of entity-problemen:
# debug: true
```

Voorbeeld zonder kaarttitel:

```yaml
type: custom:savelio-card-v3017
mode: week
title: ""
days_entity: number.dinner_genie_aantal_dagen
```

Voorbeeld gerecht van vandaag:

```yaml
type: custom:savelio-card-v3017
mode: today
title: Vandaag
days_entity: number.dinner_genie_aantal_dagen
```

`mode: day`, `mode: dag` en `mode: vandaag` werken als alias voor `mode: today`.

Voorbeeld receptenoverzicht:

```yaml
type: custom:savelio-card-v3017
mode: recipes
title: 📖 Recepten
recipes_entity: sensor.dinner_genie_recepten
```

Een compleet dashboard staat in:

```text
examples/dashboard_lovelace_card.yaml
custom_components/dinner_genie/examples/dashboard_lovelace_card.yaml
```
