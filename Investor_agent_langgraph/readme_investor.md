# Fondo de Inversión AI

Este es un concepto de prueba para un fondo de inversión impulsado por IA. El objetivo de este proyecto es explorar el uso de la IA para tomar decisiones de trading. Este proyecto es solo para fines **educativos** y no está destinado para trading o inversión real.

Este sistema emplea varios agentes trabajando juntos:

1. Agente de Valoración - Calcula el valor intrínseco de una acción y genera señales de trading
2. Agente de Sentimiento - Analiza el sentimiento del mercado y genera señales de trading
3. Agente de Fundamentales - Analiza datos fundamentales y genera señales de trading
4. Analista Técnico - Analiza indicadores técnicos y genera señales de trading
5. Gestor de Riesgos - Calcula métricas de riesgo y establece límites de posición
6. Gestor de Portafolio - Toma las decisiones finales de trading y genera órdenes

<img width="1060" alt="Screenshot 2025-01-03 at 5 39 25 PM" src="https://github.com/user-attachments/assets/4611aace-27d0-43b2-9a70-385b40336e3f" />

Nota: el sistema simula decisiones de trading, no opera realmente.

## Descargo de responsabilidad

Este proyecto es **solo para fines educativos y de investigación**.

- No está destinado para trading o inversión real
- No se proporcionan garantías
- El rendimiento pasado no indica resultados futuros
- El creador no asume responsabilidad por pérdidas financieras
- Consulte a un asesor financiero para decisiones de inversión

Al usar este software, acepta utilizarlo únicamente con fines de aprendizaje.

## Tabla de Contenidos
- [Fondo de Inversión AI](#fondo-de-inversión-ai)
  - [Descargo de responsabilidad](#descargo-de-responsabilidad)
  - [Tabla de Contenidos](#tabla-de-contenidos)
  - [Configuración](#configuración)
  - [Uso](#uso)
    - [Ejecutando el Fondo de Inversión](#ejecutando-el-fondo-de-inversión)
      - [Usando GPT-4:](#usando-gpt-4)
      - [Usando DeepSeek:](#usando-deepseek)
    - [Ejecutando el Backtester](#ejecutando-el-backtester)
      - [Usando GPT-4:](#usando-gpt-4-1)
      - [Usando DeepSeek:](#usando-deepseek-1)
  - [Estructura del Proyecto](#estructura-del-proyecto)
  - [Contribuir](#contribuir)
  - [Licencia](#licencia)

## Configuración

Clone el repositorio:
```bash
git clone https://github.com/virattt/ai-hedge-fund.git
cd ai-hedge-fund
```

1. Instale Poetry (si aún no está instalado):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Instale las dependencias:
```bash
poetry install
```

3. Configure sus variables de entorno:
```bash
# Cree el archivo .env para sus claves API
cp .env.example .env
```

Configure las claves API en el archivo .env:
```
# Obtenga su clave API de OpenAI en https://platform.openai.com/
OPENAI_API_KEY=su-clave-api-openai

# Obtenga su clave API de DeepSeek en https://platform.deepseek.ai/
DEEPSEEK_API_KEY=su-clave-api-deepseek

# Obtenga su clave API de Financial Datasets en https://financialdatasets.ai/
FINANCIAL_DATASETS_API_KEY=su-clave-api-financial-datasets
```

**Importante**: Debe configurar la clave API correspondiente según el modelo que vaya a utilizar (OpenAI o DeepSeek).

Los datos financieros para AAPL, GOOGL, MSFT, NVDA y TSLA son gratuitos y no requieren una clave API.

Para cualquier otro ticker, necesitará configurar el `FINANCIAL_DATASETS_API_KEY` en el archivo .env.

## Uso

### Ejecutando el Fondo de Inversión

El fondo de inversión puede ejecutarse con dos modelos diferentes:

#### Usando GPT-4:
```bash
poetry run python src/main.py --ticker AAPL --model 4o
```

#### Usando DeepSeek:
```bash
poetry run python src/main.py --ticker AAPL --model deepseek
```

**Ejemplo de Salida:**
<img width="992" alt="Screenshot 2025-01-06 at 5 50 17 PM" src="https://github.com/user-attachments/assets/e8ca04bf-9989-4a7d-a8b4-34e04666663b" />

También puede especificar una bandera `--show-reasoning` para imprimir el razonamiento de cada agente en la consola.

```bash
poetry run python src/main.py --ticker AAPL --model 4o --show-reasoning
```

Opcionalmente puede especificar las fechas de inicio y fin para tomar decisiones en un período específico.

```bash
poetry run python src/main.py --ticker AAPL --model deepseek --start-date 2024-01-01 --end-date 2024-03-01 
```

### Ejecutando el Backtester

El backtester también soporta ambos modelos:

#### Usando GPT-4:
```bash
poetry run python src/backtester.py --ticker AAPL --model 4o
```

#### Usando DeepSeek:
```bash
poetry run python src/backtester.py --ticker AAPL --model deepseek
```

**Ejemplo de Salida:**
[Imagen de ejemplo]

Opcionalmente puede especificar las fechas de inicio y fin para hacer backtest en un período específico.

```bash
poetry run python src/backtester.py --ticker AAPL --model 4o --start-date 2024-01-01 --end-date 2024-03-01
```

## Estructura del Proyecto
```
ai-hedge-fund/
├── src/
│   ├── agents/                   # Definiciones de agentes y flujo de trabajo
│   │   ├── fundamentals.py       # Agente de análisis fundamental
│   │   ├── portfolio_manager.py  # Agente de gestión de portafolio
│   │   ├── risk_manager.py      # Agente de gestión de riesgos
│   │   ├── sentiment.py         # Agente de análisis de sentimiento
│   │   ├── technicals.py        # Agente de análisis técnico
│   │   ├── valuation.py         # Agente de análisis de valoración
│   ├── tools/                    # Herramientas de agentes
│   │   ├── api.py               # Herramientas API
│   ├── backtester.py            # Herramientas de backtesting
│   ├── main.py                  # Punto de entrada principal
├── pyproject.toml
├── ...
```

## Contribuir

1. Haga fork del repositorio
2. Cree una rama de características
3. Haga commit de sus cambios
4. Haga push a la rama
5. Cree un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - consulte el archivo LICENSE para más detalles.