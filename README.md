# Currency Rates Data Mart

27 years of exchange rates from the European Central Bank, pulled from a free
API, turned into a star schema, and refreshed every morning by a scheduled job.

I built this to answer things like: how has the rupee moved against the euro
since 1999, and which currencies jump around the most.

## What it does

Four steps, and they run in order:

| Notebook | What it does |
|----------|--------------|
| `01_ingest_rates` | Checks the newest date I already have, asks the API only for what's newer, saves it to bronze |
| `02_merge_silver` | MERGE into silver so running it twice doesn't duplicate anything |
| `03_star_schema` | Builds the date and currency tables, and the fact table |
| `04_tests` | Six tests. If any fail the job fails |

There's also `00_setup` which creates the schemas. That one only runs once.

## It runs on its own

The four notebooks are set up as a Databricks job, one task each, chained
together. It runs every day at 6:30am. If a step fails, the steps after it don't
run and I get an email.

That's the main difference between this project and my retail one. That one I run
by hand.

## Numbers from my run

| | |
|---|---|
| Fact rows | 266,774 |
| Trading days | 7,091 (Jan 1999 to Sep 2026) |
| Currencies in the data | 47 |
| Currencies the ECB still publishes | 30 |
| Retired currencies | 17 |

The ECB only publishes on working days, which is why 27 years gives 7,091 days
and not around 9,900.

## Things I learned building it

**Only fetching what's new.** Instead of downloading 27 years every time, the
notebook reads the newest date in my silver table and starts from the day after.
First run loads everything. The next day loads one day. If there's nothing new it
stops instead of failing.

**MERGE instead of INSERT.** INSERT would duplicate every row the second time I
ran it. MERGE matches on date plus the two currency codes and either updates or
inserts. I tested it by running the same cell twice and watching the row count
stay the same.

**Grain.** One row = one currency on one day. That sentence is the grain of the
fact table, and the first test checks it holds. If the grain breaks, every number
built on top doubles.

## A bug my tests caught

My first version built the currency table from the API's list of currencies. The
referential integrity test then failed with 63,531 orphan rows.

The reason is history. 17 currencies show up in the data that the ECB doesn't
publish any more, because those countries switched to the euro:

| Currency | Last published |
|----------|----------------|
| Lithuanian litas | 2014-12-31 |
| Latvian lats | 2013-12-31 |
| Estonian kroon | 2010-12-31 |
| Slovak koruna | 2008-12-31 |
| Cypriot pound, Maltese lira | 2007-12-31 |
| Slovenian tolar | 2006-12-29 |

So I rebuilt the dimension from the data itself and joined the API names on where
they exist, with a flag for the retired ones. A dimension has to cover every key
in the fact table.

## The tables

- `fact_daily_rate` - the rate, the previous day's rate, the daily percent change,
  and a 30 day moving average
- `dim_date` - year, quarter, month, day name
- `dim_currency` - code, full name, first and last date it appeared

The percent change and the moving average use window functions. They're
partitioned by currency, because the previous row has to be the same currency.
Otherwise you'd compare a rupee rate against a yen rate.

## Tests

All six have to return 0.

| Test | What it checks |
|------|----------------|
| grain_violations | One row per currency per day |
| orphan_date_keys | Every date in the fact is in the date table |
| orphan_currency_codes | Every currency in the fact is in the currency table |
| impossible_rates | No rate is zero or negative |
| row_count_mismatch | The build didn't lose or duplicate rows |
| suspicious_gaps | No gap longer than 5 days between trading days |

The last one allows small gaps because weekends and holidays are normal. A long
gap would mean a load failed.

## Data

[Frankfurter API](https://frankfurter.dev) - European Central Bank reference
rates. Free, no API key, history back to 1999-01-04.

## Built with

PySpark, Delta Lake, SQL, Databricks Jobs, Unity Catalog.

## Note

Personal project on Databricks Free Edition, not production work.
