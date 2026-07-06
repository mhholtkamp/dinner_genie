# Dinner Genie Home Assistant integration

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

- `number.dinner_genie_aantal_dagen`
- `number.dinner_genie_aantal_personen`
- `button.dinner_genie_genereer_weekmenu`
- `button.dinner_genie_kies_willekeurig_gerecht`
- `sensor.dinner_genie_aantal_recepten`
- `sensor.dinner_genie_willekeurig_gerecht`
- `sensor.dinner_genie_weekmenu`
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
