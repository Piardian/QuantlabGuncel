# EXB-001 Data Schema

## Dataset Identifier

EXB001_ALPACA_IEX_DAILY_REDUCED

## Bar Schema

| Field | Type | Description |
| --- | --- | --- |
| symbol | string | Alpaca symbol |
| timestamp | datetime UTC | Daily bar timestamp |
| open | float | Raw daily open |
| high | float | Raw daily high |
| low | float | Raw daily low |
| close | float | Raw daily close |
| volume | integer/float | Reported daily volume |
| trade_count | integer/float/null | Alpaca reported trade count when available |
| vwap | float/null | Alpaca reported VWAP when available |

## Metadata Schema

| Field | Type | Description |
| --- | --- | --- |
| dataset_id | string | Frozen EXB-001 dataset identifier |
| source | string | Alpaca Market Data API |
| feed | string | iex |
| adjustment | string | raw |
| timeframe | string | 1Day |
| start | datetime UTC | Request start |
| end | datetime UTC | Request end |
| symbol_count_requested | integer | Number of requested symbols |
| symbol_count_with_rows | integer | Number of symbols with returned rows |
| row_count | integer | Returned bar count |

## Storage Policy

EXB-001 stores dataset metadata and quality summaries only. Raw market data is not persisted as a frozen formal dataset during EXB-001.
