# Dinner Genie Home Assistant integration

![Dinner Genie](images/banner.png)

[![Hassfest](https://github.com/mhholtkamp/dinner_genie/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/mhholtkamp/dinner_genie/actions/workflows/hassfest.yaml)
[![HACS](https://github.com/mhholtkamp/dinner_genie/actions/workflows/hacs.yaml/badge.svg)](https://github.com/mhholtkamp/dinner_genie/actions/workflows/hacs.yaml)
[![Python checks](https://github.com/mhholtkamp/dinner_genie/actions/workflows/python.yaml/badge.svg)](https://github.com/mhholtkamp/dinner_genie/actions/workflows/python.yaml)

Custom integration voor Dinner Genie.

## Installatie via HACS custom repository

1. Voeg deze repository toe in HACS als type `Integration`.
2. Installeer Dinner Genie.
3. Herstart Home Assistant.
4. Ga naar **Instellingen > Apparaten & diensten > Integratie toevoegen**.
5. Kies **Dinner Genie**.
6. Vul in:
   - API basis-URL, bijvoorbeeld `https://dinner-genie.vercel.app/api`
   - Groeps-ID
   - API key

## Entiteiten

De integratie maakt automatisch deze entiteiten aan:

- `number.dinner_genie_aantal_dagen` maximaal 7
- `number.dinner_genie_aantal_personen`
- `button.dinner_genie_genereer_weekmenu`
- `button.dinner_genie_kies_willekeurig_gerecht`
- `sensor.dinner_genie_aantal_recepten`
- `sensor.dinner_genie_willekeurig_gerecht`
- `sensor.dinner_genie_weekmenu`
- `sensor.dinner_genie_dag_1`
- `sensor.dinner_genie_dag_2`
- `sensor.dinner_genie_dag_3`
- `sensor.dinner_genie_dag_4`
- `sensor.dinner_genie_dag_5`
- `sensor.dinner_genie_dag_6`
- `sensor.dinner_genie_dag_7`
- `todo.dinner_genie_boodschappen`
- `select.dinner_genie_dieet`
- `select.dinner_genie_recepttype`

## Gebruik

Stel het aantal dagen en personen in met de number-entiteiten. Druk daarna op **Genereer weekmenu**.

De integratie roept dan aan:

```text
/api/groups/{groupId}/week-plan?days=5&servings=4
```

met de waarden uit Home Assistant.

## Maaltijden bekijken

Naast de overzichtssensor `sensor.dinner_genie_weekmenu` maakt de integratie nu ook per dag een sensor aan.

Bijvoorbeeld:

```text
sensor.dinner_genie_dag_1
```

De state is de naam van het gerecht. In de attributes staan onder andere:

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

Je kunt dus op de dagsensor klikken om de bereiding en ingrediënten te bekijken.
