# -*- coding: utf-8 -*-
"""Every user-visible string on /workflow-automation/.

PROVENANCE
  Transcribed by hand from the copy spec (see SOURCE below) on 2026-08-03.
  The build NEVER reads that document -- a build that reads a file outside the
  repo is non-hermetic and fails open. `python build_page.py --check-sources`
  re-hashes the doc and reports drift; the default build does not touch it.

CONVENTIONS
  - This file is pure ASCII on purpose. Typographic characters are written as
    HTML entities (&mdash; &rsquo; &ldquo; &rarr; &middot;) so the source is
    diffable everywhere and the build never has to fight a console codepage.
  - Nothing here may assert a client, a review, a revenue figure, or an entity
    type. See the gates in build_page.py -- they mirror _qa/autoqa.py so a
    violation fails HERE instead of at push time.
"""

SOURCE = {
    'doc': 'Documents/AWLLC-flagship-copy-2026-08-03.md',
    # sha256 recorded at transcription time; --check-sources re-hashes and diffs
    'sha256': '403e75e9eecd79b9a36a5749303d0ae133ed39ca74f04296d6ccfccd6de3e75e',
    'on': '2026-08-03',
}

EMAIL = 'colin@automatedworkflowllc.com'
MAILTO_HERO = ('mailto:colin@automatedworkflowllc.com'
               '?subject=The%20workflow%20that%20eats%20my%20week'
               '&amp;body=Hi%20Colin%2C%0A%0AThe%20repetitive%20part%20of%20my%20week'
               '%20I%27d%20most%20like%20to%20stop%20doing%20by%20hand%3A%20')
MAILTO_PLAIN = 'mailto:colin@automatedworkflowllc.com?subject=The%20workflow%20that%20eats%20my%20week'

HEAD = {
    # 58 chars -- inside seo_audit's 50-60 window, unchanged from the live page
    'title': 'Automation With a Human Approve Button | Automated Workflow',
    # 155 chars -- the copy spec's 161-char version trimmed to seo_audit's 120-158 window
    'description': ('I build the automated version of the boring parts of a small business '
                    '&mdash; invoicing, follow-ups, weekly reports. AI drafts the words; you press send.'),
    'og_title': 'Workflow Automation With a Human Approve Button',
    'canonical': 'https://automatedworkflowllc.com/workflow-automation/',
}

HEADER = {
    'cta': ('Send me a file &rarr;', '/free-demo/'),
    'nav': [('The gate', '#gate'), ('The method', '#method'),
            ('Touch it', '#bench'), ('Prices', '#prices')],
    'skip': 'Skip to content',
}

HERO = {
    'eyebrow': 'Workflow automation &middot; the whole system, not just the sheet',
    # h1 line 2 is set in the serif italic accent -- the page's signature move
    'h1_a': 'The system finds the money and writes the emails.',
    'h1_b': 'You stay the only one allowed to press send.',
    'subhead': ('I build the automated version of the parts of your week that are pure remembering '
                '&mdash; the job that finished and never got invoiced, the invoice nobody chased, the '
                'Monday numbers nobody has time to assemble. <b>Formulas do the arithmetic. AI drafts '
                'the words. You make every call that leaves the building.</b>'),
    'cta_primary': ('Tell me the workflow that eats your week &rarr;', MAILTO_HERO),
    'cta_ghost': ('Or send one messy file &mdash; free &rarr;', '/free-demo/'),
    'meta': ('A real person in <b>Gainesville, FL</b> &middot; working with small businesses anywhere '
             '&middot; <b>four free tools on this site run entirely in your browser</b> &mdash; press '
             'one before you decide whether I&rsquo;m worth an email'),
    'teaser_cap': 'waiting on a human',
    'teaser_link': 'What happens if you say go? &darr;',
}

GATE = {
    'eyebrow': 'Try it &mdash; right here',
    'h2': 'The approve button, live',
    'intro': ('This is a working miniature of the follow-up system I build. Overdue invoices get a '
              'drafted email in a tone that matches their age &mdash; and one that&rsquo;s <em>too fresh '
              'to chase</em> gets deliberate silence. Approve the ones you&rsquo;d actually send. '
              '<b>Sample data &mdash; every number and business name invented.</b>'),
    'ledger_head': 'Run ledger',
    'ledger_note': 'Layer 05, live: every run leaves a receipt.',
    'status_wait': 'Drafts are piling up at the gate &mdash; nothing leaves.',
    'status_open': 'Approved &mdash; the queue flows through. Flip it back and everything waits again.',
    'toggle': 'Give the OK',
    'send': 'Send approved',
    'reset': 'Reset the queue',
    'nojs': ('This queue is interactive &mdash; with JavaScript on you can approve each draft and watch '
             'what would leave. The four drafts, their tone tiers and the rule behind each one are all '
             'below either way.'),
    'outcome_body': ('&hellip;and that&rsquo;s where this demo stops, by design. In the real system that '
                     'approve click is the moment they actually go out &mdash; and the drafts you '
                     'didn&rsquo;t approve simply wait for the next queue. Nothing on this page sent '
                     'anything anywhere.'),
    'caption': ('The tone tiers aren&rsquo;t decoration. A nudge at nine days reads as twitchy; the same '
                'words at sixty days read as overdue. The system picks the tier. You still pick whether.'),
    'rail_cap': ('Every workflow on this page runs this same five-step shape &mdash; the Money Leak '
                 'Autopilot, the Lead Concierge, the invoice chase queue, the review flywheel, the '
                 'Monday Pulse.'),
}

# --- the invoice queue. INVENTED. Tier, pill colour, left rule, approvability and
# --- the footer counts are all DERIVED from `days` by tier_for() -- never typed twice.
INVOICES = [
    dict(ref='INV-2130', who='Fernwood Vet Clinic', amt='940', days=9,
         draft='No draft. Nine days is too fresh &mdash; a nudge now reads as twitchy, not attentive. '
               'The system waits on purpose.',
         why='Under fifteen days the invoice is still inside a normal payment habit, so the rule is '
             'silence: no draft is written at all.'),
    dict(ref='INV-2123', who='Bluebird Print Co.', amt='1,120', days=22,
         draft='&ldquo;Hi &mdash; quick nudge on invoice 2123 from last month. No rush if it&rsquo;s '
               'already queued up on your end&hellip;&rdquo;',
         why='Twenty-two days is one cycle late, so the draft assumes good faith and offers an out.'),
    dict(ref='INV-2118', who='Crestline Auto Care', amt='1,875', days=37,
         draft='&ldquo;Hi &mdash; invoice 2118 is now a month past due. Could you let me know when '
               'payment is scheduled?&hellip;&rdquo;',
         why='Thirty-seven days is past a full billing cycle, so the draft asks for a date rather than '
             'offering one.'),
    dict(ref='INV-2101', who='Harbor Coffee Roasters', amt='1,450', days=68,
         draft='&ldquo;Hi &mdash; invoice 2101 is 68 days outstanding. I&rsquo;d like to resolve this '
               'week; here are the options&hellip;&rdquo;',
         why='Past sixty days the money is at real risk, so the draft names a deadline and puts options '
             'on the table. It is still a draft.'),
]

PROBLEM = {
    'eyebrow': 'The problem',
    'h2': 'It&rsquo;s not the work. It&rsquo;s the work <em>between</em> the work.',
    'p1': ('The job itself usually goes fine. What quietly eats the week is everything around it: '
           'retyping the same customer into three places, remembering which quote never got an answer, '
           'invoicing the job that finished last Tuesday, chasing the invoice from six weeks ago, and '
           'assembling the numbers into something you can act on.'),
    'lead': ('Every one of those is a handoff. Every handoff depends on somebody remembering. '
             'That&rsquo;s the leak.'),
    'p2': ('Automation done right doesn&rsquo;t replace your judgment &mdash; it replaces the '
           'remembering. The system watches the handoffs, does the drafting and the arithmetic, and '
           'brings you a short list of decisions instead of a long list of chores.'),
    'pull': 'The system decides <b>who and what tone</b>. You decide <b>whether</b>.',
    'bridge': 'Here&rsquo;s the shape every one of my builds takes.',
}

METHOD = {
    'eyebrow': 'How every build is wired',
    'h2': 'Five layers. The same five, every time.',
    'intro': ('Anyone can connect two apps together. What makes one of these hold up on week forty is '
              'the shape it was built in. Every system I build has the same five layers, and each one '
              'has a rule I don&rsquo;t break &mdash; including on the days it would be faster to.'),
    'pull': ('Read-only in. Formulas for the math. AI for the words. A human at the door. A receipt for '
             'every run.'),
    'layers': [
        dict(n='01', name='The sensor', rule='It watches. It never touches.', spine=False,
             body='Something has to notice. A schedule that wakes up Monday morning, a form submission, '
                  'a new row in a sheet, an email landing in an inbox. <em>The rule: the sensor is '
                  'read-only.</em> It looks at your data and never writes back to it. If you unplugged '
                  'my system tomorrow, your spreadsheet would be exactly the file you&rsquo;d have had '
                  'anyway.'),
        dict(n='02', name='The math', rule='The AI never does arithmetic.', spine=True,
             body='Every total, every days-overdue count, every &ldquo;this is up 12% from last '
                  'month&rdquo; is computed by an ordinary formula in your own sheet, <em>before</em> '
                  'any AI is involved. <em>The rule: the AI never does arithmetic.</em> This isn&rsquo;t '
                  'caution for its own sake &mdash; during an early build the model added up a column '
                  'itself and got it wrong. The fix wasn&rsquo;t a better prompt. It was removing the '
                  'model&rsquo;s opportunity to do arithmetic at all. Every number the AI writes is a '
                  'number that already existed in a cell you can click on.'),
        dict(n='03', name='The brain', rule='Words only. Every figure traces to a cell.', spine=False,
             body='Now the AI gets the verified numbers and does the thing it is genuinely excellent at: '
                  'turning them into three paragraphs a human would actually read, and drafting the '
                  'follow-up emails in a tone that fits the situation. <em>The rule: narrative only.</em> '
                  'Every figure in what it writes traces back to a cell.'),
        dict(n='04', name='The gate', rule='Nothing sends itself. Ever.', spine=False,
             body='Anything that would leave your business with your name on it stops here and waits. '
                  'The drafts stack up. You read them, you delete the one that&rsquo;s wrong, you press '
                  'send on the rest. <em>The rule: no exceptions</em> &mdash; not for &ldquo;obvious&rdquo; '
                  'ones, not for the third reminder, not at 2am. This is the layer everyone else skips, '
                  'and it&rsquo;s the reason you can hand this thing your customer list without lying '
                  'awake. <b>You are the only one allowed to press send.</b>'),
        dict(n='05', name='The ledger', rule='The audit trail is a deliverable.', spine=False,
             body='Every time the system runs, it writes a row: what it read, what it computed, what it '
                  'drafted, what you approved, what went out. <em>The rule: the audit trail is a '
                  'deliverable, not an afterthought.</em> Six months from now, when someone asks why a '
                  'customer got that email, the answer is a row, not a memory.'),
    ],
    'gate_backref_off': 'try it &uarr;',
    'gate_backref_on': 'you already did this one &uarr;',
}

BENCH = {
    'eyebrow': 'Free &middot; nothing uploads',
    'h2': 'Four tools on this site. Press one right now.',
    'intro': ('Every one of these runs <b>entirely inside your browser</b>. There is no server to send '
              'your file to. You don&rsquo;t have to take my word for it &mdash; open your '
              'browser&rsquo;s network tab, drop a file in, and watch: after the page loads, zero '
              'requests. That&rsquo;s architecture, not a privacy policy. No signup, no email, no '
              'account.'),
    'tool_h3': 'Start without leaving this page',
    'tool_intro': ('Paste a customer or vendor list &mdash; any number of lines &mdash; and this page '
                   'will tell you how many real customers are in it. Same normalization as the full '
                   'tool: case, punctuation and legal suffixes ignored, then near-miss spellings '
                   'grouped for a human glance.'),
    'tool_note': 'sample lines &mdash; clear the box and paste your own',
    'tool_run': 'Check it',
    'tool_clear': 'Clear',
    'tool_after': '',   # set just below, so the link markup lives in one place
    'sample': ['Acme Roofing', 'Acme Roofing LLC', 'acme roofing inc.', 'Brightside Dental',
               'Brightside Dental, P.A.', 'Cedar Field Services', 'Cedar Feild Services',
               'Northgate Church'],
    'nojs': 'This box needs JavaScript. The full tool is at /duplicate-customer-finder/ and works the same way.',
    'receipts_pre': 'Receipts:',
    'closing': ('<b>Why the tools stop where they stop.</b> Every one of them ends at the point where a '
                'script would have to guess &mdash; which duplicate is the real customer, what a blank '
                'cell means, who should cover Thursday. Those decisions need a person who can ask you a '
                'question. That&rsquo;s what the $300 cleanup and the free demo are. A tool that guessed '
                'there would be faster and worse.'),
    'tools': [
        dict(url='/spreadsheet-health-check/', kicker='Free tool', name='Spreadsheet Health Check',
             what='Drop any CSV and get an honest report: columns that carry no information, status '
                  'fields that never vary, mixed date formats, numbers stored as text that '
                  '<code>SUM()</code> silently skips, duplicate rows. Then download the file with the '
                  'judgment-free problems already fixed.',
             proof='On its own sample it finds six problems and the automatic fix takes it to two '
                   '&mdash; and the two that remain are exactly the ones a script must not touch.'),
        dict(url='/money-leak-finder/', kicker='Free tool', name='Money Leak Finder',
             what='Two exports every business already has &mdash; the work log and the invoices &mdash; '
                  'lined up so only the mismatches show: finished jobs nobody billed, invoices sitting '
                  'unpaid past 60 days.',
             proof='It matches on exact ID only, and says so on the report. Nothing fuzzy, nothing guessed.'),
        dict(url='/duplicate-customer-finder/', kicker='Free tool', name='Duplicate Customer Finder',
             what='Acme Roofing. Acme Roofing LLC. acme roofing inc. Three rows, one customer &mdash; '
                  'inflating your count, splitting your revenue history, and sending the mail merge '
                  'three times.',
             proof='Every group states <em>why</em> it grouped: identical after ignoring case, '
                   'punctuation and legal suffixes, or a near-miss typo worth a human glance.'),
        dict(url='/shift-coverage-check/', kicker='Free tool', name='Shift Coverage Check',
             what='For anyone who runs on a roster &mdash; senior living, clinics, restaurants, '
                  'facilities. Finds days a role is uncovered, staff crossing 40 hours, roles only one '
                  'person can fill, and turnarounds too short to be safe.',
             proof='It reads your columns itself and shows you which ones it used. I built this one '
                   'because I schedule people for a living.'),
    ],
    'all_builds': ('All four, plus everything else I&rsquo;ve built, are indexed at '
                   '<a href="/builds/">/builds/</a> &mdash; and there&rsquo;s a single drop zone at '
                   '<a href="/check/">/check/</a> that works out which check your file needs and runs it.'),
}
BENCH['tool_after'] = ('Same engine as the full tool &mdash; <a href="/duplicate-customer-finder/">that '
                       'one</a> takes a whole CSV export and works out which column holds the names.')

DASH = {
    'eyebrow': 'The $650 rung, running',
    'h2': 'A dashboard you can click, not a screenshot of one.',
    'p1': ('<a href="/demo/">/demo/</a> is a real Google Sheets dashboard built as an Apps Script web '
           'app &mdash; revenue, jobs, overdue invoices, tabs you can click, a chart you can tap. No '
           'login, no signup. It&rsquo;s the $650 Automated Dashboard doing its actual job.'),
    'p2': ('It also refreshes itself. A weekly trigger re-runs the whole build every Monday morning, '
           'which is why the numbers you&rsquo;re looking at aren&rsquo;t from whenever I last '
           'remembered to update the page. <b>The data in it is invented sample data</b> &mdash; the '
           'machinery is not.'),
    'p3': ('There&rsquo;s a second one at <a href="/staffing-commission-dashboard/">'
           '/staffing-commission-dashboard/</a>: a live commission dashboard for a staffing desk that '
           'settles splits, draws and fall-off clawbacks by rule instead of by argument. Built for a '
           'vertical where the math <em>is</em> the whole disagreement.'),
    'cta': ('Open the live dashboard &nearr;', '/demo/'),
}

REPORT = {
    'eyebrow': 'The reporting half',
    'h2': 'Watch a report write itself',
    'kpis': [('$208,900', 'revenue, wk 12'), ('38 &rarr; 61', 'new customers'), ('+47%', 'vs wk 1')],
    'kpi_note': 'invented sample numbers',
    'narrative': ('Revenue grew 47% from week 1 to week 12, and new customers rose from 38 to 61 over '
                  'the same stretch. The growth is broad rather than lumpy: no single week carried it. '
                  'Worth watching: acquisition is outpacing revenue per customer, so the next lever is '
                  'ticket size, not traffic.'),
    'run': 'Run it',
    'replay': 'Replay',
    'caption': ('<b>The rule on display:</b> every figure above was computed by formulas before the AI '
                'saw a word of it. The model only writes the sentences &mdash; it is never trusted with '
                'the arithmetic.'),
    'video_cap': 'The same thing on video, 20 seconds, end to end',
    'video_aria': ('Twenty-second demo: the workflow reads your numbers, writes a plain-English summary, '
                   'and emails it to you.'),
}

# --- Money Leak storyboard (W1). Cedar Field Services is INVENTED; the figures are
# --- reconciled against _brand/build_money_leak_page.py by gate G-LEAK at build time.
LEAK = {
    'eyebrow': 'The flagship, step by step',
    'h2': 'What the Money Leak Autopilot does on a Monday',
    'intro': ('Four steps, in order, on the same invented sample the free tool ships with. Nothing here '
              'is a screenshot &mdash; the arithmetic below is the arithmetic the tool actually does.'),
    'label': ('Cedar Field Services is an invented company. Every job, invoice and dollar in this '
              'section is made up &mdash; the arithmetic is real, the business isn&rsquo;t.'),
    'steps': [
        dict(t='Monday 6:00am &middot; READ',
             b='The sensor opens two exports you already produce &mdash; 14 jobs in the work log, 11 '
               'invoices in the invoice export &mdash; and reads them. It writes nothing back.'),
        dict(t='COMPUTE',
             b='Formulas line the two files up on job number and flag what doesn&rsquo;t match: '
               '<b>3 jobs</b> finished and never invoiced (<b>$1,280</b>), <b>6 invoices</b> still '
               'unpaid (<b>$5,430</b>), of which <b>$705</b> is past 60 days. Every one of those numbers '
               'came from a formula, before any model saw the data.'),
        dict(t='DRAFT',
             b='The AI gets those verified figures and writes two things: a short digest for you '
               '(&ldquo;three jobs finished, never invoiced&rdquo;) and one chase email per overdue '
               'invoice, in the tone tier that matches its age &mdash; the same tier table the queue '
               'above uses.'),
        dict(t='GATE',
             b='Every draft stops in a queue exactly like the one above and waits for you. Nothing is '
               'sent, nothing is filed, nothing is decided. '
               '<a href="#gate">That&rsquo;s the queue above &mdash; go approve them.</a>'),
    ],
    'cta': ('Run this on your own two exports &rarr;', '/money-leak-finder/'),
}

ENG = {
    'eyebrow': 'The part nobody shows you',
    'h2': 'I publish my own bugs.',
    'intro': 'Most people show you finished work. Here&rsquo;s the machinery that keeps it honest.',
    'items': [
        dict(h='The build log lists four bugs I shipped and caught.',
             b='<a href="/build-log/">/build-log/</a> walks through the multi-tenant reporting pipeline '
               'end to end &mdash; including the dashboard that displayed <b>MONEY LOST ON OVER-BUDGET '
               'JOBS: $0</b> directly above two jobs flagged over budget at &minus;$500 and &minus;$600, '
               'because five summary formulas were off by one column. It survived review because my own '
               'build log computed the totals independently and printed the <em>right</em> answer while '
               'the sheet showed the wrong one. Two sources of truth that never met. Each of the four '
               'left a permanent check behind.'),
        dict(h='Isolation was proven, not assumed.',
             b='When a loop setting looked like it might collapse a multi-client run into one send, I '
               'stopped reading documentation and ran it live: two sends, six seconds apart, distinct '
               'narratives per row, in the execution record. Now it&rsquo;s a fact I read off a log '
               'instead of a belief I took from a doc.'),
        dict(h='An automated quality gate blocks my own pushes.',
             b='A script scores every workbook and every page for defects and runs on a git pre-push '
               'hook &mdash; if the score goes up, the push is refused. On the last recorded run the '
               'score was zero.'),
        dict(h='Everything rebuilds identically.',
             b='Twelve sample workbooks, each generated by its own Python script rather than assembled '
               'by hand, all reading brand colours from a single source of truth. Nothing drifts, '
               'because nothing is typed twice. This page is built the same way &mdash; the file you '
               'are reading is generated, and the build refuses to write it if any of its own checks '
               'fail.'),
        dict(h='Two open-source repos you can read.',
             b='<code>flatline</code> finds signals that carry no information and jobs that produce '
               'nothing &mdash; a check that fires on 100% of rows, a scheduled task that reports '
               'success while writing nothing. I built it after a real scheduled job of mine discarded '
               'four days of data while reporting success every run. MIT licensed, 108 tests. '
               '<code>hearth</code> is a national crisis-resource directory built on federal data and '
               'refreshed automatically, with a public health endpoint that reports freshness per source '
               'so a stale feed can&rsquo;t hide behind a fresh one.'),
    ],
    'pull': ('The interesting work isn&rsquo;t wiring the happy path &mdash; a model does that before '
             'lunch. It&rsquo;s the four times I didn&rsquo;t trust it yet.'),
}

# status must be one of LIVE / RUNNING / BUILDING / DESIGNED (asserted at build time).
# LIVE is reserved for "running for a paying customer" and is therefore unused -- there isn't
# one. RUNNING means built, published and firing on a schedule against Colin's OWN data.
WORKFLOWS = {
    'eyebrow': 'What I&rsquo;d build you',
    'h2': 'Five systems. Same five layers underneath.',
    'intro': ('Each is the same architecture wearing a different job. Two run every week on my own '
              'business right now &mdash; my invoices, my contact form &mdash; which is how I know '
              'the wiring holds before I point it at yours. The other three are designs.'),
    'honesty': ('To be exact: the two that run, run for <em>me</em> &mdash; not a customer. That is '
                'the difference between a system that works and a system with a track record, and '
                'I&rsquo;d rather draw that line than let a green chip draw it for you. The other '
                'three get built for the first person who wants one.'),
    'closing': ('All of it runs on tools you already have &mdash; Google Sheets, Gmail, your existing '
                'forms. There&rsquo;s no new software for your people to learn, which is the reason the '
                'spreadsheet won in the first place.'),
    'cta': ('Which one sounds like your week? &rarr;', MAILTO_PLAIN),
    'rows': [
        dict(id='W1', name='Money Leak Autopilot', status='RUNNING', price='$1,000 + $250&ndash;500/mo',
             what='Every week the system reads your work log and your invoice export, the sheet&rsquo;s '
                  'own formulas flag the jobs that finished and never got billed plus everything aging '
                  'past 30 and 60 days, an AI writes you a short digest, and the chase emails draft '
                  'themselves in a tone that matches each invoice&rsquo;s age. Then everything stops and '
                  'waits for you.',
             note='Fires every Monday at 7am on my own books. The digest quotes the sheet&rsquo;s '
                  'figures rather than adding them up itself &mdash; a model doing arithmetic is a '
                  'model you can&rsquo;t check.'),
        dict(id='W2', name='Lead Concierge', status='RUNNING', price='$650 install',
             what='An inquiry arrives, by form or by inbox. Within minutes it&rsquo;s a tracked row, a '
                  'notification, and a drafted personal reply waiting for your approval &mdash; and if '
                  'it&rsquo;s still unanswered in 24 hours, the system tells on itself. Most lost leads '
                  'aren&rsquo;t lost to competitors. They&rsquo;re lost to Tuesday.',
             note='Wired to the contact form on this site, so you can test it rather than take my '
                  'word: send something through and a drafted reply waits in my inbox within about '
                  'fifteen minutes. When a submission came in empty, the draft said so instead of '
                  'inventing a reason to talk to me &mdash; that refusal is the part I care about.'),
        dict(id='W3', name='Invoice Chase Queue, live edition', status='DESIGNED',
             price='$500&ndash;750 install',
             what='The chase spreadsheet with a live layer on top: the sheet that chases for you. '
                  'Overdue invoices move through 15 / 30 / 60-day tone tiers, drafts stage in your '
                  'Gmail, you approve.',
             note=''),
        dict(id='W4', name='Review Flywheel', status='DESIGNED',
             price='$500&ndash;750 install, or bundled into a retainer',
             what='A job gets marked complete. The system waits the right number of days, drafts the '
                  'review ask in your voice, and holds it for your approval. The ask that actually gets '
                  'sent is the one that doesn&rsquo;t depend on you remembering to send it.',
             note=''),
        dict(id='W5', name='Weekly Pulse', status='DESIGNED', price='$1,000 + $250&ndash;500/mo',
             what='Monday morning, the system reads your live numbers, the formulas compute everything, '
                  'and an AI writes the three paragraphs you&rsquo;d actually read: what moved, what '
                  'needs attention, what to do next. That&rsquo;s the panel further up, pointed at your '
                  'business.',
             note=''),
    ],
}

TEMPLATES = {
    'eyebrow': 'Free templates',
    'h2': 'Take these and never speak to me. That&rsquo;s the point.',
    'intro': ('Three working Google Sheets templates, no cost and no email required: an '
              '<a href="/free/executive-kpi-dashboard.html">executive KPI dashboard</a>, an '
              '<a href="/free-expense-tracker-template/">expense tracker</a>, and a '
              '<a href="/free-staffing-commission-tracker/">staffing commission tracker</a>. Download, '
              'open, use. If one of them solves your problem and you never contact me, the template did '
              'its job.'),
}

PRICING = {
    'eyebrow': 'What it costs',
    'h2': 'Start at zero. The ladder is the same either way.',
    # rendered as an ascending stair, read bottom to top
    'steps': [
        dict(price='Free', name='The 1-day mini-demo',
             body='Send me one messy file &mdash; a job log, an invoice export, an intake sheet, a '
                  'schedule. I&rsquo;ll send back a working automated version within a day. Yours to '
                  'keep whether you hire me or not. This is how every engagement starts, and it&rsquo;s '
                  'the whole reason the tools on this page are free too: I&rsquo;d rather you judge the '
                  'work than the pitch.'),
        dict(price='$300', name='Spreadsheet Cleanup',
             body='Your messiest sheet, rebuilt into one you can trust. Formulas that don&rsquo;t '
                  'silently skip rows, dates in one format, statuses that mean one thing. 24&ndash;48 '
                  'hours.'),
        dict(price='$500&ndash;750', name='Workflow Install',
             body='I build one workflow <b>in your own account</b> &mdash; your Zapier, your Google, '
                  'your Gmail &mdash; document it, and hand it over. You own it completely. If we never '
                  'speak again it keeps running. No subscription, no lock-in, no dependency on me.'),
        dict(price='$650', name='Automated Dashboard',
             body='Your numbers on one live page that updates itself. The <a href="/demo/">/demo/</a> '
                  'you can click on this site is this rung, running.'),
        dict(price='$1,000 + $250&ndash;500/mo', name='Report Autopilot',
             body='The Monday report that writes itself, plus approve-gated follow-ups on money '
                  'you&rsquo;re owed. Setup, then I run it, watch it, and tune it.'),
        dict(price='From $2,000', name='Full Workflow Automation',
             body='Intake to invoice to follow-up, built end to end around how your business already '
                  'works.'),
    ],
    'under': ('Two honest notes. First: the free demo is not a trick &mdash; you keep the artifact '
              'either way, and if the answer is &ldquo;you don&rsquo;t need me for this,&rdquo; '
              'I&rsquo;ll say that in the same email. Second: I&rsquo;m early enough that the first few '
              'engagements are priced to earn an honest review rather than to maximize the invoice. '
              'That&rsquo;s a real advantage to being first, and it doesn&rsquo;t last.'),
}

WHO = {
    'eyebrow': 'Who&rsquo;s building it',
    'h2': 'One person. In public. On purpose.',
    'p1': ('I&rsquo;m Colin McCarthy. I build and run Automated Workflow out of Gainesville, Florida, '
           'and I work with small businesses anywhere, because all of this is remote.'),
    'p2': ('Before I wrote systems for operations, I ran them. I still do &mdash; I manage dining '
           'operations at a continuing-care community affiliated with the University of Florida: '
           'scheduling, inventory, vendors, and a staff who did not sign up to learn new software. '
           'That&rsquo;s why the Shift Coverage Check exists, and it&rsquo;s why I&rsquo;m allergic to '
           'automation that adds a tool instead of removing a chore. I&rsquo;ve held the clipboard the '
           'software is supposed to help.'),
    'p3': ('I&rsquo;m certified through Anthropic Academy &mdash; six credentials &mdash; and more '
           'usefully, I use the same AI tooling on my own business every day before I point it at '
           'anyone else&rsquo;s.'),
    'ledger_head': 'The honesty ledger',
    'can': ['four tools that run in your browser', 'a live dashboard that refreshes itself',
            'a public log of my own bugs', 'two open-source repos, 108 tests',
            'every sample figure labelled invented'],
    'wont': ['a customer count', 'revenue figures', 'a testimonial', 'borrowed credibility',
             'other people&rsquo;s logos'],
    'ledger_line': ('I have zero paying customers. I&rsquo;m early, and that&rsquo;s why the first '
                    'engagements are priced to earn a review rather than a margin. What I have instead '
                    'is work you can inspect without asking me anything &mdash; and the first thing '
                    'I&rsquo;d build you costs nothing.'),
}

FAQ = {
    'eyebrow': 'The questions I actually get',
    'h2': 'Fair questions, answered plainly.',
    'qs': [
        ('&ldquo;Won&rsquo;t AI just do all of this by itself in a year?&rdquo;',
         'The drafting, probably &mdash; it already does, and I use it for exactly that. The deciding, '
         'no. Every system here is built on the assumption that the model is a fast, capable writer '
         'with no judgment and no stake in your reputation. So the machine does the watching, the '
         'arithmetic and the drafting, and a human does the one thing that carries consequences: '
         'approving. If a model gets good enough to replace <em>that</em>, you&rsquo;d still want a gate '
         'in front of it. The gate is the product. The rest is wiring.'),
        ('&ldquo;Why should I trust you with my data?&rdquo;',
         'Start by not giving me any. The four tools on this page run entirely inside your browser '
         '&mdash; there&rsquo;s no server for them to send your file to. Open the network tab and check; '
         'after the page loads it makes zero requests. That&rsquo;s the design, not a promise. When we '
         'do work together, the same posture holds: everything is built in <em>your</em> accounts, the '
         'sensors are read-only so nothing writes back to your source data, and every run logs what it '
         'touched.'),
        ('&ldquo;Do you actually have customers?&rdquo;',
         'No. Not yet &mdash; I&rsquo;ll say that plainly rather than let a stock photo imply otherwise. '
         'Automated Workflow is new, I&rsquo;ve built everything you see here myself, and you&rsquo;d be '
         'first. What that buys you: my full attention, pricing set to earn a review rather than pad an '
         'invoice, and a founder who cannot afford to do a mediocre job. What it costs you: you '
         'can&rsquo;t call a reference. So judge the work instead &mdash; that&rsquo;s why it&rsquo;s '
         'all pressable, readable, and free to inspect.'),
        ('&ldquo;My spreadsheet is a disaster. I&rsquo;m embarrassed to send it.&rdquo;',
         'Good. A tidy file tells me nothing. The mess <em>is</em> the diagnostic &mdash; merged cells, '
         'three tabs that should be one, four spellings of the same customer, a column somebody stopped '
         'filling in last March. I&rsquo;ve never once received a file I thought less of someone for. '
         'Send the worst one.'),
        ('&ldquo;What happens when the AI writes something wrong?&rdquo;',
         'Three things stop it before you do. It never touches the arithmetic &mdash; every number is '
         'computed by formula before the model sees it, because a model added up a column wrong on me '
         'once and the fix was to take arithmetic away from it entirely. It never sends &mdash; drafts '
         'stage and wait for you, so a bad sentence dies in a review, not in a customer&rsquo;s inbox. '
         'And every run is logged, so when something looks off there&rsquo;s a row explaining what it '
         'read and what it did. When I do get something wrong, it goes on the build log.'),
        ('&ldquo;Do I have to switch software?&rdquo;',
         'No. Everything runs on what you already have &mdash; Google Sheets, Gmail, whatever form you '
         'already use. The spreadsheet won because it was already there; a system that asks you to '
         'abandon it is a system that&rsquo;ll get abandoned in three months. If you want zero ongoing '
         'dependency on me, the $500&ndash;750 Workflow Install is built in your own accounts and handed '
         'over.'),
        ('&ldquo;What do I actually get in the free demo, and what&rsquo;s the catch?&rdquo;',
         'You send one file. Within a day you get back a working automated version of it &mdash; real '
         'formulas, real structure, your real data &mdash; plus a short note on what I&rsquo;d build '
         'next and what it&rsquo;d cost. You keep it whether you hire me or not. The catch, such as it '
         'is: I&rsquo;m betting that a working artifact is more persuasive than a proposal, and that if '
         'I&rsquo;m right you&rsquo;ll come back. If I&rsquo;m wrong, you got a fixed spreadsheet for '
         'free.'),
        ('&ldquo;How long does any of this take?&rdquo;',
         'Cleanup: 24&ndash;48 hours. A dashboard or a workflow install: usually within a week. The '
         'mini-demo: a day. I&rsquo;m one person, which means you&rsquo;re never in a queue behind an '
         'account manager &mdash; and it also means I&rsquo;ll tell you honestly if something is bigger '
         'than my calendar.'),
    ],
}

CTA = {
    'eyebrow': 'The whole pitch, honestly',
    'h2': 'What&rsquo;s the workflow that eats your week?',
    'p': ('Tell me in one sentence. I&rsquo;ll tell you in one email whether it&rsquo;s automatable, '
          'what it would cost, and what I&rsquo;d build first &mdash; and if the answer is that you '
          'don&rsquo;t need me, I&rsquo;ll tell you that too. The first artifact is free either way.'),
    'primary': ('Email Colin &rarr;', MAILTO_PLAIN),
    'ghost': ('Or start with one messy file &rarr;', '/free-demo/'),
    'sub': ('Or just press a tool. Nothing uploads, nothing signs you up, and you&rsquo;ll learn more '
            'about how I work in ninety seconds than this page can tell you.'),
    'nap': 'colin@automatedworkflowllc.com &middot; (703) 939-1174 &middot; Gainesville, FL',
}
