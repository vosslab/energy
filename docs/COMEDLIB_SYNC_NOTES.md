# comedlib.py sync notes

Notes for syncing `battcontrol/comedlib.py` with the upstream
`energy/energylib/comedlib.py`. The file is shared across repos and
maintained in the energy repo.

## Current diff (battery-control vs energy)

Only difference is the cache file initialization:
- **energy**: has `os.chmod(self.cache_file, 0o666)` with PermissionError catch
- **battery-control**: simplified to just create the file, plus `# nosec B108`

The chmod is useful for multi-user systems. The nosec comment suppresses
bandit security warnings about the hardcoded /tmp path.

**Recommended**: merge both -- keep the chmod with PermissionError catch
AND the nosec comment.

## Bugs fixed in battery-control copy (ported upstream 2026-04-06)

### 1. Infinite loops on network failure

`getMostRecentRate()` and `getPredictedRate()` used `while data is None:`
which hangs forever if `downloadComedJsonData()` returns None.

**Fix**: changed to `if data is None:` with early `return None`.

### 2. Cache check after computation in getMedianComedRate()

The cache was checked AFTER downloading data and building the prices array.
Every call after the first wasted work computing prices before finding the
cache hit.

**Fix**: moved `if hasattr(self, '_median_cache')` to the top of the
function, before `downloadComedJsonData()`. Added `and data is None` guard
so passing explicit data bypasses the cache (allows fresh computation).

### 3. Missing None guards

`getCurrentComedRate()` and `getCurrentComedRateUnSafe()` would crash if
`downloadComedJsonData()` returned None, passing None to `parseComedData()`.

**Fix**: added `if data is None: return None` after the download call.

## Supply rate review

The `chargingCutoffPrice = 10.1` in `getReasonableCutOff()` is a hardcoded
anchor used in the cutoff formula:

```python
reasonableCutoff = (chargingCutoffPrice + 2 * defaultCutoff) / 3.0
```

This is NOT the supply rate. It is a tuning parameter that pulls the cutoff
upward. The actual supply rate comes from ComEd's live hourly pricing API.

### Current ComEd supply rates (from bills, 2025-2026)

The effective supply rate varies by month because of the Purchased
Electricity Adjustment (PEA) and other line items:

| Period | Import kWh | Supply charge | Effective rate |
| --- | --- | --- | --- |
| Mar-Apr 2024 | 736 | $19.97 | 2.71c/kWh |
| Apr-May 2024 | 698 | $19.23 | 2.75c/kWh |
| Apr-May 2025 | 838 | $53.79 | 6.42c/kWh |
| May-Jun 2025 | 758 | $34.65 | 4.57c/kWh |
| Jun-Jul 2025 | 1181 | $51.62 | 4.37c/kWh |
| Nov-Dec 2025 | 1153 | $47.87 | 4.15c/kWh |
| Dec-Jan 2026 | 1417 | $57.96 | 4.09c/kWh |
| Feb-Mar 2026 | 884 | $23.45 | 2.65c/kWh |

The effective supply rate ranges from ~2.7c to ~6.4c/kWh depending on
the month. The PEA can swing this significantly (ranging from -$16.97
to +$22.32 across bills).

### What the 10.1c anchor does

With current median hourly prices around 3c:
- `defaultCutoff` ~ 3.5c (75th percentile + sqrt(std)/5)
- `reasonableCutoff = (10.1 + 2 * 3.5) / 3 = 5.7c`

The 10.1c anchor ensures the cutoff is always significantly above the
median price, making the controller conservative (holds battery more
often than not). This is intentional -- the cutoff was designed for
load-adding devices where conservative means "add load only when it is
clearly cheap."

### Should 10.1 change?

The 10.1 was set when supply rates were similar to current levels. The
formula blends 1/3 fixed anchor + 2/3 live data, so it self-adjusts
somewhat. Changing 10.1 shifts the entire cutoff range up or down.

The `cutoff_scale` config key in the battery controller is a local
workaround for tuning this without modifying the shared comedlib. A
`cutoff_scale` of 0.75 effectively lowers the cutoff by 25%.

## Other notes

- `parseComedData()` cache is not invalidated when new data is passed
  as an argument. The in-memory `parsed_data_cache` persists across
  calls even if fresh data was explicitly provided. This is a minor
  issue since the daemon creates a fresh `ComedLib()` instance each
  cycle.
- `safeDownloadWebpage()` disables SSL verification after an SSLError
  and leaves it disabled for all subsequent retries in that call. This
  is a security concern but not a functional bug.
- The "Equivalent Gas Rate" on the ComEd bill is a display-only metric
  for consumer comparison; it is not used anywhere in the code.
