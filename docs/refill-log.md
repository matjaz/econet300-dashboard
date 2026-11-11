# Hopper refill log (n8n)

Logs when and how many bags went into the hopper, next to the daily max temperature at your location, so you can see the usage against the weather. It is one page, one webhook, two n8n workflows and two n8n data tables. It doesn't touch the ecoNET module or the controller.

| File | What |
|---|---|
| `n8n/refills.workflow.json` | workflow *Hopper refills*: a webhook that writes refills and lists them with temperatures |
| `n8n/temperature.workflow.json` | workflow *Daily max temperature*: writes each day's max temperature at your location (Open-Meteo) |
| `www/refills.html` | the page: entry form (time, bags), usage chart in kg with the temperature, list of entries with totals; EN / SL / PL |

```
page ──GET  /webhook/refills?days=30────────▶ Webhook ─▶ Read refills ─▶ Read temperatures ─▶ Build list
                                                      ─▶ 200 {from, days, items, temperature}
     ──POST /webhook/refills {time, bags}───▶ Webhook ─▶ Check entry ─▶ Valid? ─┬▶ Write refill ─▶ 201 {id, time, bags}
                                                                              └▶ 400 {error}

Daily max temperature (every 6 hours, or by hand):
Location ─▶ Read temperatures ─▶ Open-Meteo ─▶ New and corrected days ─▶ Write temperatures
```

## Setup in n8n

Needs an n8n version with Data tables; tested on n8n 2.44.3.

1. **Tables:** Overview → Data tables → Create.
   - `refills` with the columns `time` (type *Date*) and `bags` (type *Number*);
   - `temperature` with `date` (type *String*, e.g. `2026-10-31`) and `tmax` (type *Number*).

   n8n adds `id`, `createdAt` and `updatedAt` itself.
2. **Token:** Credentials → Create → *Header Auth*, with Name `X-Token` and as Value a random string, e.g. from `openssl rand -hex 24`. Don't commit the token anywhere.
3. **Import:** Workflows → Import from File → `n8n/refills.workflow.json`, then select the credential from step 2 in the **Webhook** node.
   - The Data table nodes find their tables by name. If yours are named differently or live in another project, select them in the nodes.
4. **Temperature:** import `n8n/temperature.workflow.json`. It needs no credential.
   - In its **Location** node, set `LATITUDE` and `LONGITUDE` (decimal degrees). Until then it stops with "Set LATITUDE and LONGITUDE in the Location node".
5. **Timezone:** days start at midnight in the workflow's timezone. That is *Settings → Timezone* of each workflow, by default the instance's `GENERIC_TIMEZONE`. Set it to yours.
6. **Activate** both workflows (Publish / Active).
   - The webhook's production URL is `https://<your-n8n>/webhook/refills`. The test URL `/webhook-test/...` works only while "Listen for test event" runs in the editor.
   - Run *Daily max temperature* once by hand: the first run fills the last 400 days in a few seconds, then it runs by itself.
7. **Page:** open `refills.html` and enter the URL from step 6 and the token from step 2 under *Settings*.
   - The browser keeps them in local storage, so you enter them once per device.
   - A default URL can also go into the constant `WEBHOOK_URL` at the top of the page; never put the token there.
   - `TEMP_PLACE` there names your location in the note under the chart.

### Where the page can live

The page is a single file without external resources. It can be:
- opened straight from disk (`file://`);
- put on any static server the phone can reach;
- put next to the dashboard on the module (`/www/econet/client/`, behind the module's login).

The webhook must be reachable from the browser: at home, over a VPN, or publicly behind the token.

**CORS:** without *Allowed Origins (CORS)* set in the Webhook node, n8n accepts calls from any origin, including `file://` (origin `null`). To restrict it, enter the page's origin there, e.g. `http://192.168.1.50`; the page then no longer works from disk.

## The page

- **Time:** now by default; **Now** resets it. If you leave it untouched, saving takes the time of the click, since the page may have been open for long. It is sent in UTC (ISO 8601) and shown in local time.
- **Bags:** a whole number 1–100, default 1.
- **Save:** writes the entry and shows e.g. "Saved: <time>, 3 bags (45 kg)", then resets the form and refreshes the chart and list. The new entry is highlighted.
- **Usage chart:**
  - kilograms per refill: bags × bag weight (default 15 kg, set under *Settings*);
  - periods: 7, 14 or 30 days (a bar per day), 13 weeks (per week, the last week ending today) or 12 months (per calendar month);
  - above the chart: total kg, bags, average kg per day and the period;
  - hover or tap a bar for kg, bags and date.
  - The chart shows when the hopper was filled, not the momentary use: a refill day has a tall bar, the days between none. For consumption, look at the average over a longer period.
  - **Temperature** is a blue line on a right-hand °C axis that shares the grid with kg. It shows the daily max for days, and the mean of daily maxima for weeks and months. Where a day is missing, the line breaks. Without the temperature workflow, the chart has no line and no right axis.
- **List:** the entries of the chosen period, 20 per page, newest first, with a total; *Newer* / *Older* page through what was already read.
- **Errors:** a wrong token (403) opens *Settings*; an unreachable webhook shows its URL; a refused entry (400) shows the workflow's reason.
- The page reads the webhook once when opened and after each entry, with `days=30`; 13 weeks reads 91 days, 12 months up to 366. A period already read doesn't call again.
- Language: EN / SL / PL in the top right, shared with the dashboard (`dashLang`); `?lang=` overrides it.

Correcting or deleting entries: in n8n, Data tables → `refills`.

### Dashboard

The dashboard logs refills too. When the fuel level rises (after you set the hopper to full on the panel), it asks how many bags went in and writes them through the same webhook.

- **When it asks:** the level is at least 5 percentage points above the last level that browser saw, on two readings in a row. An unknown level (255) is ignored. The last level is kept in the browser, so a rise while the dashboard was closed is asked about on the next visit.
- **Already logged?** Before asking, and again before saving, it reads the log. An entry from 30 min before the rise or later means the refill was already logged, on another device or in `refills.html`. Then it only shows that entry, or offers *Save anyway*.
- **Settings:** it uses the same browser storage keys as `refills.html` (`refillUrl`, `refillToken`, `refillKg`), so both pages share them when served from the same address. The module's login isn't sent to n8n.
- **Skip** closes without writing and doesn't ask about that rise again. **Esc** keeps the question for later: *Log refill* turns amber.

## Temperature

**Source:** the [Open-Meteo](https://open-meteo.com/) *Historical Forecast API*, at the point set in the Location node.
- It returns model data (`best_match`), with `timezone=auto`, so the days are local days at that point.
- No key needed. Free for non-commercial use up to 10,000 calls a day; the workflow uses at most 4.
- The license is CC BY 4.0, so the page names the source under the chart (`TEMP_SOURCE`).

**How it runs:**
- At minute 20 every 6 hours.
- One call for the last 400 days up to yesterday (~6 KB), retried twice after 5 s on errors.
- **New and corrected days** writes the days the table doesn't have yet, and the days whose value Open-Meteo has corrected since (by at least 0.1 °C). If nothing changed, it stops there. Usually the first run after midnight adds yesterday and the others write nothing.
- **Write temperatures** upserts by `date`, so no day is duplicated.
- Today isn't written until it's over.
- If Open-Meteo is unreachable, the run ends with an error in the HTTP node. Missing days come with the next successful run, since every run reads all 400 days.

To redo a day, delete its row in Data tables → `temperature` and run the workflow.

## API

All requests need the header `X-Token: <token>`.

**GET** `/webhook/refills?days=30`
- `days`: how many recent days to return, today included. Default 30, clamped to 1–400; an invalid value gives the default.
- Returns 200:
  ```json
  {"from": "2026-10-13", "days": 30,
   "items": [{"id": 26, "time": "2026-11-01T15:19:00.000Z", "bags": 3}, ...],
   "temperature": [{"date": "2026-10-13", "tmax": 16.7}, ..., {"date": "2026-11-10", "tmax": 8.4}]}
  ```
  - `from`: the first day returned; the period starts at midnight of that day in the workflow's timezone.
  - `items`: all entries with `time` from then on (also any in the future), newest first, then by `id`.
  - `temperature`: daily max in °C from `from` to yesterday, oldest first. Days without data are left out. Without the `temperature` table the list is empty and the answer is still 200.

**POST** `/webhook/refills`, JSON body `{"time": "<ISO 8601>", "bags": <whole number>}`
- 201 `{"id": 26, "time": "2026-11-01T15:19:00.000Z", "bags": 3}`; the time is stored in UTC.
- 400 `{"error": "..."}`, nothing written, when:
  - `time` is missing, invalid, or more than a day in the future;
  - `bags` is not a whole number 1–100. A string of digits, e.g. `"3"`, is accepted.
- 422 when the body isn't JSON (n8n's own answer).

**Wrong or missing token:** 403 `Authorization data is wrong!`. **Inactive workflow:** 404.

```sh
TOKEN=...   # the token from the credential
curl -H "X-Token: $TOKEN" "https://<n8n>/webhook/refills?days=7"
curl -H "X-Token: $TOKEN" -H 'Content-Type: application/json' \
     -d '{"time":"2026-11-01T15:19:00Z","bags":2}' https://<n8n>/webhook/refills
```
