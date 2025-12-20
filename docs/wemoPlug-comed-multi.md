# WeMo multi-plug decision process

This page documents how `apps/wemoPlug-comed-multi.py` decides when to enable or
disable charging based on ComEd pricing.

## Overview
- Fetch ComEd pricing once per loop (current and predicted).
- Compute a cutoff from `ComedLib.getReasonableCutOff()`, then clamp to bounds.
- Apply a small bias and deadband to reduce churn.
- Decide to enable, disable, or hold, then apply the action to every plug.

## Inputs
- Current rate: `ComedLib.getCurrentComedRate()`
- Predicted rate: `ComedLib.getPredictedRate()`
- Baseline cutoff: `ComedLib.getReasonableCutOff()`
- Time-of-hour: used to suppress late-hour spikes

## Config knobs
- `wemoIpAddresses`: list of WeMo IPs to control.
- `badHours`: hours treated as high-price by default.
- `lower_bound`: always enable below this predicted rate.
- `upper_bound`: always disable above this predicted rate.
- `cutoff_adjust`: small bias applied to the cutoff after clamping.
- `buffer_rate`: deadband around the cutoff to avoid rapid toggling.

## Cutoff calculation
1. `cutoff = getReasonableCutOff()`
2. Clamp to `lower_bound` / `upper_bound`.
3. Apply `cutoff_adjust`.

## Decision flow
1. **Long disable (late-hour spike)**
   - If `predicted > 2 * cutoff` and current minute > 20:
   - Disable all plugs and sleep until the next hour.
2. **Force enable (cheap)**
   - If `predicted < lower_bound`: enable all plugs.
3. **Disable (expensive)**
   - If `predicted > cutoff + buffer_rate`: disable all plugs.
4. **Disable (hard ceiling)**
   - If `predicted > upper_bound`: disable all plugs.
5. **Enable (below cutoff)**
   - If `predicted < cutoff - buffer_rate`: enable all plugs.
6. **Hold**
   - Otherwise, log and leave current state unchanged.

## Hourly guardrails
- If `hour` is in `badHours` and minute < 20:
  - Disable all plugs, then sleep until `hour:20`.
- The optional “always enable before 5AM” block is present but commented out.

## Logging
- Each decision prints a shared message including current/predicted/cutoff.
- Each plug appends its IP to the message and logs to `car_charging-wemo_log.csv`.
