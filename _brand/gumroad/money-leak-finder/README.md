# Gumroad listing art for /money-leak-finder/

Rendered 2026-08-03. `cover.html` is a 1280x720 page and `thumb.html` its square
sibling; the two PNGs are what those pages produced, and are what a Gumroad
listing would actually use.

## Why this lives in `_brand/` and not beside the tool

Jekyll excludes underscore directories, so nothing here is served on the public
web. That is deliberate: these are marketing SOURCE assets, and putting 400 KB of
product art under `money-leak-finder/` would publish it as a side effect of
storing it.

## How they were nearly lost

They existed in exactly one place: an abandoned clone of this repository at
`Documents/awllc-website`, 254 commits behind, as UNTRACKED files. Recommending
that clone be deleted — which I did — would have destroyed them, and nothing in
the deletion would have looked wrong.

The lesson is narrow and worth keeping: **a stale checkout is only safe to remove
once its untracked files have been accounted for.** Committed content is
recoverable from the remote by definition; untracked content is not, and "this
clone is 254 commits behind" says nothing about what was never committed.

Checked at the same time and NOT preserved, deliberately: that clone's copy of
`free-sales-cleanup-template/sales-cleanup-template.xlsx` differed by 1 byte, but
the live version has since been through `f2fa263 Drop "LLC" everywhere it
appears`, so the clone's copy is a pre-correction variant rather than lost work.
