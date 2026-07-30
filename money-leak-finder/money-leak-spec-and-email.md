# Money Leak Finder — sample workbook spec (source of truth for outreach claims)

Built 2026-07-29 by `build_money_leak.py`. THE artifact the money-leak outreach hook promises:
work-completed vs. work-invoiced side by side, flagging ONLY the mismatches.

**Scenario:** "Cedar Field Services" — an INVENTED small field-services company. Every figure
is sample data and every tab's title band says so.

## The traceable numbers (grep targets for /presend)

| Claim | Value | Where |
|---|---|---|
| Jobs completed | 14 | Work Log |
| Invoices sent | 11 | Invoices |
| Completed but **never invoiced** | 3 jobs — J-111, J-112, J-114 | Leak Report §A |
| Never-invoiced total | **$1,280** ($520 + $310 + $450) | Leak Report KPI A |
| Invoiced but **unpaid** | 6 invoices | Leak Report §B |
| Unpaid total | **$5,430** | Leak Report KPI B |
| Unpaid **past 60 days** | **$705** (INV-2210 77d $410, INV-2211 99d $295) | Leak Report KPI C |
| As-of date | 2026-07-28 (FIXED — no TODAY(), so aging never drifts from colors) | Leak Report title |

Self-reconciliation: build log prints every row's input → computed flag/bucket/color, plus
Python totals vs. the exact ranges each KPI formula sums. All three KPIs verified matching.

## Files
- Repo + Downloads (fresh): `money-leak-finder-sample.xlsx`
- Drive (xlsx, owner-only — set link-share before sending the LINK; attaching from Downloads
  is the cleaner path): file id `1Bb632k13aVA96F47bn_RCXQ8yZnZh2ZQ`

## Reply email (send when a money-leak prospect answers WITHOUT attaching a file)

Subject: (reply in-thread)

> Great to hear from you. So you can see the shape of it before sending anything over,
> I've attached the sample version — a made-up field-services company, every number invented,
> but the mechanics are exactly what I'd build from your real exports.
>
> Three tabs: the work log (what got done), the invoices (what got billed), and the leak
> report — which only shows the mismatches. In the sample it surfaces three finished jobs
> that never got invoiced ($1,280 in made-up money) and two invoices sitting past 60 days.
>
> When you're ready, send me any two exports that cover "done" and "billed" — messy is fine,
> redact whatever you like — and I'll send back your version within a day. Free either way.
>
> Colin

Honesty notes: sample figures are explicitly labeled invented in both the email and the
workbook; no claim about the recipient's books; no bare URLs (attach, don't link).

## If they attach a FILE → skip this, run `/mini-demo` on their real data same hour.
