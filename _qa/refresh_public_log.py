# -*- coding: utf-8 -*-
"""Keep the PUBLIC /log/ page in step with the private build log, nightly.

Colin's ask: "I just want it to be constantly updated." The public log is
generated from dev/BUILD-LOG.html, which several sessions append to every day,
so without this the page silently drifts behind the thing it claims to mirror —
which is precisely the failure this company sells against.

It also owns proof/ai/index.html, which is generated from the attest ledger and
goes out of date every time a scheduled AI job runs.

WHY BOTH LIVE HERE (fixed 2026-08-17). The job was extended on 2026-08-08 to
rebuild /proof/ai/ as well, but the committing step still staged exactly one
path, so /proof/ai/ was rebuilt on disk every night and never committed. The
pre-push hook then rebuilt it, correctly found it stale, and blocked the push --
which killed the /log/ push too. The nightly job had been committing locally and
failing to push, printing "a human should reconcile" to a log file nobody reads,
and a human periodically noticed and pushed it by hand. A job that depends on
somebody spotting it is not automated. Both pages are gated and committed here
together, so neither can strand the other.

DELIBERATELY NARROW. This job may only ever touch the two pages it generates:

  * it stages exactly those paths, never `git add -A`, so unrelated work another
    session left in the tree can never ride along on an automated push;
  * it runs the full gate set BEFORE committing and aborts on any failure, so a
    privacy leak or an SEO regression stops here rather than reaching the domain;
  * it never force-pushes and never resolves a divergence — if the branch has
    moved, it exits non-zero and leaves the decision to a human;
  * if the rebuild produces no change it exits 0 having done nothing, so quiet
    nights stay quiet instead of generating noise somebody learns to ignore.

Exit codes: 0 = up to date (changed or already current), 1 = blocked, and the
reason is printed. Run under attest so the exit code becomes a signed receipt.
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
PAGE = os.path.join("log", "index.html")
AI_PAGE = os.path.join("proof", "ai", "index.html")

# Each page and the builder that generates it. Order matters only in that both
# are rebuilt before anything is gated or committed.
BUILDERS = [
    (PAGE, ["_brand/build_log_page.py"]),
    (AI_PAGE, ["_brand/build_proof_ai_page.py"]),
]

# /proof/ai/ stamps its own generation time, so a naive diff reports a change on
# EVERY rebuild. Committing that would put a timestamp-only commit on main every
# night -- noise somebody learns to ignore, which is how a guard gets muted. The
# pre-push hook already ignores this line; the same rule has to be applied here,
# or the two disagree about whether the page changed.
TIMESTAMP_MARKER = "Generated 20"

GATES = [
    ("security sweep", ["_qa/security_sweep.py"]),
    ("SEO audit", ["_qa/seo_audit.py"]),
    ("AutoQA", ["_qa/autoqa.py", "--fast"]),
]


def run(cmd, **kw):
    return subprocess.run(cmd, cwd=SITE, capture_output=True, text=True, **kw)


def git(*args):
    return run(["git"] + list(args))


def substantive_change(path):
    """True if `path` differs by more than its own generation timestamp.

    Mirrors the pre-push hook exactly. If these two rules ever disagree, one of
    them commits a page the other rejects, which is the deadlock this fixes.
    """
    diff = git("diff", "-U0", "--", path).stdout
    for line in diff.splitlines():
        if not line or line[0] not in "+-":
            continue
        if line[:2] in ("++", "--"):
            continue
        if TIMESTAMP_MARKER in line:
            continue
        return True
    return False


def main():
    py = sys.executable

    # 1. rebuild both generated pages. Each builder is fail-closed: it refuses to
    #    write if a blocked term or a local path survives filtering. Both run even
    #    if the first fails -- skipping the second would hide two problems behind
    #    one -- and the failure is reported after both have had their turn.
    failed = []
    for path, cmd in BUILDERS:
        r = run([py] + cmd)
        print(r.stdout.strip() or r.stderr.strip())
        if r.returncode != 0:
            failed.append(path)
    if failed:
        print("BLOCKED: builder refused to write for %s (see above)." % ", ".join(failed))
        return 1

    # 2. did anything actually change? Timestamp-only churn on /proof/ai/ does not
    #    count, or this commits noise to main every single night.
    changed = [p for p in (PAGE, AI_PAGE)
               if substantive_change(p)
               or git("diff", "--cached", "--quiet", "--", p).returncode != 0]
    if not changed:
        # Drop the timestamp churn so the tree is left as clean as it was found.
        for path, _ in BUILDERS:
            git("checkout", "--", path)
        print("public log and AI record already current — nothing to do.")
        return 0
    print("changed: %s" % ", ".join(changed))

    # 3. gates BEFORE commit. A leak must never become a commit.
    for name, cmd in GATES:
        g = run([py] + cmd)
        if g.returncode != 0:
            print("BLOCKED by %s:\n%s" % (name, (g.stdout + g.stderr).strip()[-1200:]))
            # Revert EVERY page this job rebuilt, not just the ones it judged
            # changed: /proof/ai/ is rewritten with a fresh timestamp on every run
            # even when its substance is identical, so reverting only `changed`
            # leaves the tree dirty and the next run inherits it.
            for path, _ in BUILDERS:
                git("checkout", "--", path)
            print("reverted %s; nothing committed."
                  % ", ".join(p for p, _ in BUILDERS))
            return 1
    print("gates clean: security, SEO, AutoQA")

    # 4. commit ONLY the pages this job generates. The whitelist is still exact --
    #    it is two paths now rather than one, and anything else appearing in the
    #    index still aborts the run rather than riding along.
    expected = []
    for path in changed:
        git("add", "--", path)
        expected.append(path.replace(os.sep, "/"))
    staged = git("diff", "--cached", "--name-only").stdout.split()
    if sorted(staged) != sorted(expected):
        print("BLOCKED: expected to stage only %s, got %s" % (expected, staged))
        for path in changed:
            git("reset", "HEAD", "--", path)
        return 1

    msg = ("log: refresh public build log and AI record from source\n\n"
           "Automated nightly regeneration. Only the generated pages are touched "
           "(%s); the privacy filter and the security/SEO/AutoQA gates all passed "
           "before this commit was created." % ", ".join(expected))
    c = git("commit", "-m", msg)
    if c.returncode != 0:
        print("BLOCKED: commit failed:\n%s" % (c.stdout + c.stderr).strip())
        return 1
    print("committed.")

    # 5. push, but never fight the remote.
    p = git("push")
    if p.returncode != 0:
        print("BLOCKED: push failed (branch likely diverged). Commit is local; "
              "a human should reconcile:\n%s" % (p.stdout + p.stderr).strip()[-600:])
        return 1
    print("pushed — /log/ is in step with the private build log.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
