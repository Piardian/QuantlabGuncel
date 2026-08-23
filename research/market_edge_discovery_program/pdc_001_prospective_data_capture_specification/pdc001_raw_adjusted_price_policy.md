# Raw Vs Adjusted Price Policy

Raw market data must be stored independently from adjustment metadata.

Do not overwrite raw prices with adjusted values.

Store where available:

- raw OHLCV
- vendor adjusted close
- split adjustment factor
- dividend adjustment factor
- internally derived adjusted series version, if later authorized

Vendor adjusted data may be used only with source documentation and retained metadata.
