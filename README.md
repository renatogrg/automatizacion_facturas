# Sistema Inteligente para la Gestión Automática de Facturas por Consorcio

Ver `docs/plan_trabajo_sistema_facturas.md` para el plan de trabajo completo.

## Estructura

- `config/` — archivos editables (consorcios, ajustes, .env). No requieren tocar código.
- `src/` — código fuente.
- `tests/` — pruebas y facturas de ejemplo (no se suben a git).
- `build/` — script de empaquetado a .exe.

## Puesta en marcha (desarrollo)

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy config\.env.example config\.env
```

Luego edita `config\.env` y coloca tu API key real de Anthropic.
