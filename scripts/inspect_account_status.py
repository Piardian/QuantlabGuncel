import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.alpaca_broker_adapter import AlpacaBrokerAdapter

broker = AlpacaBrokerAdapter.from_environment()

acc_status, account = broker.get_account()
pos_status, positions = broker.get_positions()
ord_status, open_orders = broker.get_open_orders()
all_ord_status, all_orders = broker.transport.get_json(broker.paper_base_url, "/v2/orders", {"status": "all", "limit": 60})

print("=== ACCOUNT STATE ===")
print("Equity:          $", account.get("equity"))
print("Cash:            $", account.get("cash"))
print("Buying Power:    $", account.get("buying_power"))
print("Portfolio Value: $", account.get("portfolio_value"))
print("Account Status:   ", account.get("status"))

pos_list = positions if isinstance(positions, list) else []
print(f"\n=== POSITIONS (Total: {len(pos_list)}) ===")
total_market_value = 0.0
total_unrealized_pl = 0.0
for p in pos_list:
    mkt_val = float(p.get("market_value", 0.0))
    unreal_pl = float(p.get("unrealized_pl", 0.0))
    plpc = float(p.get("unrealized_plpc", 0.0)) * 100
    total_market_value += mkt_val
    total_unrealized_pl += unreal_pl
    sym = p.get("symbol", "")
    qty = p.get("qty", "")
    avg_price = p.get("avg_entry_price", "")
    cur_price = p.get("current_price", "")
    print(f"  {sym:<6} | Qty: {qty:<8} | Entry: ${float(avg_price):<7.2f} | Current: ${float(cur_price):<7.2f} | Val: ${mkt_val:<9.2f} | P/L: ${unreal_pl:<7.2f} ({plpc:+.2f}%)")

print(f"\nTotal Holdings Market Value: ${total_market_value:,.2f}")
print(f"Total Unrealized P/L:        ${total_unrealized_pl:,.2f}")

open_list = open_orders if isinstance(open_orders, list) else []
print(f"\n=== OPEN ORDERS (Total: {len(open_list)}) ===")
for o in open_list:
    sym = o.get("symbol", "")
    side = o.get("side", "")
    qty = o.get("qty", "")
    notional = o.get("notional", "")
    st = o.get("status", "")
    print(f"  {sym:<6} | Side: {side} | Qty: {qty} | Notional: {notional} | Status: {st}")

all_list = all_orders if isinstance(all_orders, list) else []
status_counts = {}
for o in all_list:
    st = o.get("status", "unknown")
    status_counts[st] = status_counts.get(st, 0) + 1
print(f"\n=== ORDERS SUMMARY (Total Retrieved: {len(all_list)}) ===")
print("Status Counts:", status_counts)
print("\nRecent 10 Orders Detail:")
for o in all_list[:10]:
    sym = o.get("symbol", "")
    side = o.get("side", "")
    st = o.get("status", "")
    fq = o.get("filled_qty", "")
    favg = o.get("filled_avg_price", "")
    sub_at = o.get("submitted_at", "")
    print(f"  {sym:<6} | {side} | Status: {st:<8} | FilledQty: {fq:<8} | AvgPrice: ${favg} | SubAt: {sub_at}")
