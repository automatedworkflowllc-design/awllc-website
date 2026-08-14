# Social graphics — how the Instagram post was made, and the rule it follows

## The rule
**Use the real product's real output.** The 2026-08-14 post shows three findings the live
`/demo/` actually computed from a pasted invoice book — not an illustration of what it might say.
Colin's brief was "a cool photo infographic that doesn't look like AI slop", and the reliable way
to clear that bar is to stop illustrating and start showing. No gradients, no glassmorphism, no
stock photography, no emoji, no fake 3D. Site palette, one accent, real numbers.

## Where the numbers came from
Pasted into the live `/demo/` and read back off the page. Verified by hand before use:
- unpaid 4,820 + 1,310 + 3,140 + 2,260 + 2,075 = **13,605** ✓
- Northgate 4,820 + 3,140 + 2,075 = **10,035** = 73.8% → **74%** ✓
- overdue (>30d) 4,820 + 1,310 + 3,140 + 2,260 = **11,530** = 84.7% → **85%** ✓

## The honesty control
The card carries a **SAMPLE DATA** chip, mirroring the one the product itself shows. Without it a
reader could take "Northgate Builders holds 74% of everything you are owed" as a real client
engagement. AWLLC has zero clients; nothing published may imply otherwise. The caption repeats it.

## How it was built
`instagram-findings-post.js` — drawn on a `<canvas>` **inside the browser**, then the blob handed
straight to Instagram's file input. Two reasons: `file_upload` only accepts files the user shared
with the session, and pushing a 230KB PNG through as base64 would have been a wasteful payload.
The `{a_w}` mark is drawn from its **native 26x10 pixel grid** (recovered from icon-512.png using
the SVG's 4-unit cell size), so the brand mark costs a few hundred characters instead of an image.

Paste the file's contents into `javascript_tool` on any page, then set the file input:
```js
const f = new File([window.__blob], 'post.png', {type:'image/png'});
const i = document.querySelector('input[type=file]');
const dt = new DataTransfer(); dt.items.add(f); i.files = dt.files;
i.dispatchEvent(new Event('change', {bubbles:true}));
```

## Instagram gotchas, measured
- Canvas is **1080x1350 (4:5)** but the crop step still defaults to **1:1** and silently cuts the
  eyebrow and the footer. Open the crop control and pick **4:5** every time.
- The **Website** profile field is **read-only on web** — "editing your links is only available on
  mobile". Only the app can set it.
- Leave **"Add AI label"** off for graphics like this: that policy targets photorealistic synthetic
  media, and mislabelling a data card would be inaccurate.
