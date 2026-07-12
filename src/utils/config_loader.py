import json
import os


def cargar_settings(ruta="config/settings.json") -> dict:
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def cargar_consorcios(ruta="config/consorcios.json") -> list:
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)["consorcios"]
