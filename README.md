# Dinner Genie Home Assistant custom integration

## Installatie

1. Kopieer de map `custom_components/dinner_genie` naar:

```text
/config/custom_components/dinner_genie
```

2. Herstart Home Assistant volledig.
3. Ga naar **Instellingen > Apparaten & diensten > Integratie toevoegen**.
4. Zoek **Dinner Genie**.
5. Vul in:

```text
API basis-URL: https://dinner-genie.vercel.app/api
Groeps-ID: jouw groeps-id
API key: jouw api key
```

## Helpers aanmaken

Maak deze twee helpers aan als `input_number` helpers:

```yaml
input_number:
  dinner_genie_aantal_dagen:
    name: Dinner Genie aantal dagen
    min: 1
    max: 14
    step: 1
    mode: box
    initial: 5

  dinner_genie_aantal_personen:
    name: Dinner Genie aantal personen
    min: 1
    max: 50
    step: 1
    mode: box
    initial: 4
```

Of maak ze via de UI:

```text
Instellingen > Apparaten & diensten > Helpers > Helper maken > Nummer
```

Gebruik exact deze entity IDs:

```text
input_number.dinner_genie_aantal_dagen
input_number.dinner_genie_aantal_personen
```

## Entiteiten

Deze integratie maakt onder andere:

```text
button.dinner_genie_genereer_weekmenu
sensor.dinner_genie_aantal_recepten
sensor.dinner_genie_willekeurig_gerecht
sensor.dinner_genie_weekmenu
todo.dinner_genie_boodschappenlijst
```

## Werking

De knop leest de helpers uit en roept daarna de API aan:

```text
/api/groups/{groupId}/week-plan?days=5&servings=4&recipeType=dinner
```

Het weekmenu wordt opgeslagen via Home Assistant storage, zodat het na een herstart behouden blijft.
De boodschappenregels worden als Home Assistant to-do/list entity aangeboden.

## Later uitbreiden

De maaltijden worden nu volledig opgeslagen in de attributen van `sensor.dinner_genie_weekmenu`.
Daar zitten onder andere `id`, `name`, `description`, `imageUrl`, `instructions` en ingrediënten in als de API die meestuurt.
Daarmee kun je later een dashboardkaart maken waarbij klikken op een maaltijd het recept toont.
