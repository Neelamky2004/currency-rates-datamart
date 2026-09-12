# Notes for myself

## One line
"I built a scheduled pipeline that pulls 27 years of exchange rates from a public
API, only fetches the days it doesn't already have, models them as a star schema,
and tests itself before anything gets used."

## Words I should be able to explain

**API ingestion** - instead of reading a file, my code calls a web service, gets
JSON back, and turns it into rows.

**Watermark** - the newest date I already have. I read it from my own table and
only ask the API for what comes after. That's what makes the load incremental.

**MERGE** - one statement that updates a row if it's already there and inserts it
if it isn't.

**Idempotent** - running the same load twice gives the same result as running it
once. It matters because a failed run can just be re-run, with nothing to clean up.

**Grain** - the sentence that describes exactly one row of my fact table. Mine is
"one exchange rate, for one currency, on one day".

**Star schema** - the fact table holds the numbers, the dimension tables hold the
descriptions you slice by.

**Referential integrity** - every key in the fact table exists in its dimension. I
check it with a LEFT ANTI JOIN that has to return 0.

**Window function** - a calculation that looks at other rows near this one.
`lag(rate)` gives me the previous day's rate for the same currency.

**Task dependency** - task B only starts if task A worked.

## Questions I should expect

**How does this run in production?**
It's a Databricks job with four tasks in order, on a daily schedule. If a task
fails, the ones after it don't run and I get an email. I don't click anything.

**What makes it incremental?**
Before calling the API I read the highest date already in silver and start from
the day after. First run does 27 years, the next does one day.

**Why MERGE and not INSERT?**
INSERT would duplicate rows on a second run. I tested MERGE by running it twice
and the row count didn't change.

**What's the grain of your fact table?**
One rate, one currency, one day. It's the first thing I test, because if the
grain breaks every number on top of it doubles.

**What if the API is down?**
`raise_for_status()` makes the call fail loudly instead of writing nothing, so
the task fails and nothing downstream runs on bad data.

**Why partition the window function by currency?**
Because the previous row has to be the same currency. Without it I'd be comparing
a rupee rate to a yen rate.

**Did anything go wrong?**
Yes, and it's the best part. My currency table came from the API's current list,
but the data has 27 years of history. The test failed with 63,531 orphan rows,
because 17 currencies in the data don't exist any more - they got replaced by the
euro. I rebuilt the dimension from the data instead.

**Why is data missing on some days?**
The ECB only publishes on working days. My sixth test allows gaps up to 5 days
and flags anything longer, because that would mean a load failed.

**Is your currency dimension Type 1 or Type 2?**
Type 1. Type 2 would keep the history with valid-from and valid-to dates. I went
with Type 1 because my reports slice by currency code, not by name, so the
history isn't used. It was a choice, not something I missed.

**How big is it?**
266,774 rows. 7,091 trading days across 47 currencies.

**Was this production?**
No. Personal project on Databricks Free Edition.
