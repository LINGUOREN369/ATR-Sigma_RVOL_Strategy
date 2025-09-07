# ATR & RVOL Strategy

This project provides a simple pipeline to load daily stock data, compute features like **Relative Volume (RVOL)** and **Average True Range (ATR)**, and visualize them for trading analysis.

---

## 🔄 Data Processing Pipeline

```python
df_daily = daily_data_handler(stock_ticker, daily_date_range)

# Select features
volume_df = daily_data_feature(df_daily, "volume")
close_df  = daily_data_feature(df_daily, "close")

# Compute RVOL (relative volume)
daily_rvol_df = daily_data_rvol(volume_df, look_back_days_daily)

# Compute ATR (volatility measure)
atr_df = daily_data_atr(df_daily, atr_look_back_days)