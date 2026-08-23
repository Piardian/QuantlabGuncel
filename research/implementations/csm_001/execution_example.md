# CSM-001 Execution Example

## Python Example

```python
import pandas as pd
from csm001_momentum_model import CSM001MomentumModel

close_panel = pd.read_csv("data/csm001_close_panel.csv", parse_dates=["date"]).set_index("date")
model = CSM001MomentumModel()
result = model.transform(close_panel).frame
result.to_csv("output/csm_001_validation/csm001_momentum_state.csv", index=False)
```

## Required Input Shape

The close panel must use dates as the index and one column per ticker. Values must be adjusted close prices.

## Boundary

This example generates construct output only. It is not a backtest or trading strategy.
