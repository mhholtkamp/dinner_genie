# Contributing

Bedankt dat je wilt bijdragen aan Dinner Genie voor Home Assistant.

## Lokale structuur

De integratie staat in:

```text
custom_components/dinner_genie/
```

## Controleren vóór commit

Voer lokaal minimaal uit:

```bash
python -m compileall custom_components/dinner_genie
```

Na een push draaien GitHub Actions automatisch:

- Hassfest validation
- HACS validation
- Python syntax check

## Versies

Gebruik bij voorkeur Git tags en GitHub Releases, bijvoorbeeld:

```text
v2.1.1
v2.2.0
v3.0.0
```

Zorg dat `version` in `custom_components/dinner_genie/manifest.json` overeenkomt met de release.
