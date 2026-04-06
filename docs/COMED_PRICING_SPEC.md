# COMED_PRICING_SPEC.md

## Purpose

This document summarizes how ComEd Residential Hourly Single billing appears to settle
imported and exported energy based on multiple monthly bills. It is intended as a practical
model for replay and battery-strategy analysis, not a legal tariff interpretation.

## Core model

ComEd bills imported and exported energy separately, then combines the line items.

For a billing period:

- `import_kwh` = meter reading "kWh From Grid"
- `export_kwh` = meter reading "kWh To Grid"

The bill structure is consistently:

- supply charges on imported kWh
- supply credits on exported kWh
- delivery charges on imported kWh
- delivery credits on exported kWh
- a separate net metering adjustment line in Taxes/Fees that may be positive or negative

A practical monthly accounting identity is:

```text
total_bill
  = fixed_charges
  + import_kwh * import_supply_rate
  - export_kwh * export_supply_credit_rate
  + import_kwh * import_delivery_rate
  - export_kwh * export_delivery_credit_rate
  + import_kwh * taxes_and_fees_rate_like_items
  + export_kwh * net_metering_adjustment_rate
  + monthly_adjustments
```

This is more accurate than a single net-flow formula like:

```text
net_kwh * (hourly_price + delivery_rate)
```

because import and export are settled on separate line items, and export has its own supply,
delivery, and net-metering-adjustment terms.

## What is stable across the bills

### Metering

Every bill includes both:

- `kWh From Grid`
- `kWh To Grid`

Examples:

- 3/18/24 to 4/16/24: 736 kWh from grid, 392 kWh to grid
- 4/16/24 to 5/15/24: 698 kWh from grid, 567 kWh to grid
- 4/16/25 to 5/18/25: 838 kWh from grid, 584 kWh to grid
- 5/18/25 to 6/17/25: 758 kWh from grid, 538 kWh to grid
- 11/16/25 to 12/15/25: 1,153 kWh from grid, 15 kWh to grid
- 12/15/25 to 1/19/26: 1,417 kWh from grid, 36 kWh to grid
- 2/16/26 to 3/17/26: 884 kWh from grid, 123 kWh to grid

### Delivery settlement is symmetric

Variable delivery is charged on imports and credited on exports at nearly the same rate.

Examples:

- 3/18/24 to 4/16/24:
  - Distribution Facility: 736 kWh x 0.04777
  - IL Electricity Distribution: 736 kWh x 0.00124
  - Net Metering Credit - Delivery: 392 kWh x -0.04901

- 4/16/24 to 5/15/24:
  - Distribution Facility: 698 kWh x 0.05003
  - IL Electricity Distribution: 698 kWh x 0.00124
  - Net Metering Credit - Delivery: 567 kWh x -0.05127

- 4/16/25 to 5/18/25:
  - Distribution Facility: 838 kWh x 0.06041
  - IL Electricity Distribution: 838 kWh x 0.00125
  - Net Metering Credit - Delivery: 584 kWh x -0.06166

- 5/18/25 to 6/17/25:
  - Distribution Facility: 758 kWh x 0.06055
  - IL Electricity Distribution: 758 kWh x 0.00125
  - Net Metering Credit - Delivery: 538 kWh x -0.06180

- 12/15/25 to 1/19/26:
  - Distribution Facility: 1,417 kWh x 0.06228
  - IL Electricity Distribution: 1,417 kWh x 0.00126
  - Net Metering Credit - Delivery: 36 kWh x -0.06354

This implies a practical variable delivery model of:

```text
delivery_cost
  = import_kwh * delivery_import_rate
  - export_kwh * delivery_export_credit_rate
```

with `delivery_import_rate` and `delivery_export_credit_rate` usually very close.

### Supply settlement is separate for imports and exports

Supply is not represented only by one hourly price. Bills show multiple supply components:

Imports:
- Electricity Supply Charge
- Transmission Services Charge
- Capacity Charge
- Purchased Electricity Adjustment
- Misc Procurement Components Charge

Exports:
- Net Metering Credit - Hourly Pricing
- Net Metering Credit - Supply

Examples:

- 4/16/25 to 5/18/25:
  - Electricity Supply Charge: 838 kWh, $21.86
  - Transmission: 838 kWh x 0.00982
  - PEA: $22.32
  - Net Meterering Credit - Hourly Pricing: 584 kWh, -$17.11
  - Net Metering Credit - Supply: 584 kWh x -0.03704

- 5/18/25 to 6/17/25:
  - Electricity Supply Charge: 758 kWh, $20.73
  - Transmission: 758 kWh x 0.01101
  - PEA: $4.91
  - Net Metering Credit - Hourly Pricing: 538 kWh, -$15.46
  - Net Metering Credit - Supply: 538 kWh x -0.01822

- 6/17/25 to 7/17/25:
  - Electricity Supply Charge: 1,181 kWh, $55.58
  - Transmission: 1,181 kWh x 0.01101
  - PEA: -$16.97
  - Net Metering Credit - Hourly Pricing: 421 kWh, -$32.41
  - Net Metering Credit - Supply: 421 kWh x 0.00263

- 12/15/25 to 1/19/26:
  - Electricity Supply Charge: 1,417 kWh, $36.09
  - Transmission: 1,417 kWh x 0.01083
  - PEA: $10.53
  - Net Metering Credit - Hourly Pricing: 36 kWh, -$1.04
  - Net Metering Credit - Supply: 36 kWh x -0.01888

This means export settlement is a separate credit stack, not simply the negative of import settlement.

### Net metering adjustment is a separate line

Bills also include a separate tax/fees line:

- `Net Metering - Adjustment`

This can be either positive or negative.

Examples:

- 3/18/24 to 4/16/24: 392 kWh x -0.03507
- 4/16/24 to 5/15/24: 567 kWh x -0.02523
- 4/16/25 to 5/18/25: 584 kWh x -0.00630
- 5/18/25 to 6/17/25: 538 kWh x 0.00546
- 6/17/25 to 7/17/25: 421 kWh x -0.00264
- 11/16/25 to 12/15/25: 15 kWh x -0.00880
- 12/15/25 to 1/19/26: 36 kWh x 0.01220
- 2/16/26 to 3/17/26: 123 kWh x 0.02949

This line should be modeled explicitly if bill matching matters.

## Recommended modeling levels

### Level 1: simple strategy replay

Good enough for comparing battery strategies within the same month.

Use:

```text
grid_cost
  = import_kwh * (hourly_supply_price + variable_delivery_rate)
  - export_kwh * (hourly_export_credit_rate + variable_delivery_credit_rate)
```

Suggested notes:

- use separate import and export kWh, not net kWh
- use variable delivery only, not fixed customer/meter charges
- treat monthly non-energy adjustments as out of scope for strategy comparison

### Level 2: bill-approximation replay

Better for matching actual monthly bills.

Add:

- monthly PEA allocation
- transmission charge
- misc procurement charge
- capacity charge allocation
- net metering adjustment
- tax/fees items that scale with imported kWh
- fixed customer and meter charges

### Level 3: exact bill reproduction

Needed only if you want invoice-grade agreement.

Requires:

- exact hourly export credit mapping used by ComEd
- month-specific PEA handling
- exact tax treatment and municipal/franchise treatment
- confirmation of how hourly pricing credits roll into bill-period line items

## Practical guidance for battery analysis

For battery strategy replay, the most important corrections are:

1. Do not use a single `net_kwh * rate` formula.
2. Track `import_kwh` and `export_kwh` separately.
3. Include variable delivery charges and delivery export credits.
4. Include export settlement explicitly.
5. Treat fixed monthly charges as irrelevant to battery strategy comparison.

Recommended replay approximation:

```python
import_cost = import_kwh * (import_supply_rate + delivery_import_rate)
export_credit = export_kwh * (export_supply_credit_rate + delivery_export_credit_rate)
net_grid_cost = import_cost - export_credit
```

## Implementation notes

### Delivery rate drift

The variable delivery rate changes over time:

| Period | Delivery rate |
| --- | --- |
| Spring 2024 | 4.901c/kWh |
| Spring 2025 | 6.166c/kWh |
| Winter 2025-26 | 6.354c/kWh |

The rate should be updated periodically from the most recent bill. It is
currently hardcoded in `daily_summary.py` as `delivery_cents_per_kwh = 6.354`.

### Export supply credit approximation

The Level 1 formula uses `hourly_export_credit_rate` but we do not have
the exact per-hour export credit rate from ComEd. The bill line item
"Net Metering Credit - Hourly Pricing" settles export supply at a rate
close to but not identical to the ComEd hourly supply price. Using the
same hourly price for both import and export supply is an acceptable
approximation for strategy ranking.

### Current implementation

**`daily_summary.py`** implements two cost tables:
- **Supply-only table**: uses `net_kwh * hourly_comed_price` per hour.
  This is a Level 1 approximation with import and export using the same
  hourly price. Does not separate import/export kWh.
- **Delivery-inclusive table**: uses `net_kwh * (hourly_price + 6.354)`
  per hour. Same approximation with delivery added.

Both tables use `net_kwh` rather than separate import/export tracking.
For hours where solar > load, net is negative (export). For hours where
load > solar, net is positive (import). This is equivalent to separate
tracking when the same rate applies to both directions, which is true
for delivery but approximate for supply.

**`replay_strategy.py`** uses supply-only pricing (`replayed_grid_kwh *
comed_price`) for strategy comparison. It does not include delivery because
delivery is a fixed per-kWh rate that scales all strategies equally and
does not change relative rankings.

### Upgrading to separate import/export tracking

To move from the current `net_kwh * rate` model to proper separate
import/export accounting (as recommended in Level 1):

```python
if net_kwh > 0:
    # importing from grid
    cost = net_kwh * (hourly_price + delivery_import_rate)
else:
    # exporting to grid
    cost = net_kwh * (hourly_price + delivery_export_credit_rate)
```

This matters if import and export supply rates diverge significantly.
From current bill data, the difference is small enough that the `net_kwh`
approximation is adequate for strategy comparison.

## Conclusions

- The billing structure is consistent across the bills reviewed.
- Delivery is effectively symmetric: import delivery charges and export delivery credits are nearly equal in magnitude.
- Supply uses separate import and export line items and should not be collapsed into one net-flow term.
- Net metering adjustment is a separate export-related reconciliation term and can change sign by month.
- For replay and battery strategy work, separate import and export accounting is the correct model.
