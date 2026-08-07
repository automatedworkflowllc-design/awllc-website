# -*- coding: utf-8 -*-
"""Keep the PUBLIC /log/ page in step with the private build log, nightly.

Colin's ask: "I just want it to be constantly updated." The public log is
generated from dev/BUILD-LOG.html, which several sessions append to every day,
so without this the page silently drifts behind the thing it claims to mirror —
which is precisely the failure this company sells against.

DELIBERATELY NARROW. This job may only ever touch log/index.html:

  * it stages exactly one path, never `git add -A`, so unrelated work another
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

GATES = [
    ("security sweep", ["_qa/security_sweep.py"]),
    ("SEO audit", ["_qa/seo_audit.py"]),
    ("AutoQA", ["_qa/autoqa.py", "--fast"]),
]


def run(cmd, **kw):
    return subprocess.run(cmd, cwd=SITE, capture_output=True, text=True, **kw)


def git(*args):
    return run(["git"] + list(args))


def main():
    py = sys.executable

    # 1. rebuild from the private log. The builder is itself fail-closed: it
    #    refuses to write if a blocked term survives filtering.
    r = run([py, "_brand/build_log_page.py"])
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode != 0:
        print("BLOCKED: builder refused to write (see above).")
        return 1

    # 2. did anything actually change?
    if git("diff", "--quiet", "--", PAGE).returncode == 0 and \
       git("diff", "--cached", "--quiet", "--", PAGE).returncode == 0:
        print("public log already current — nothing to do.")
        return 0

    # 3. gates BEFORE commit. A leak must never become a commit.
    for name, cmd in GATES:
        g = run([py] + cmd)
        if g.returncode != 0:
            print("BLOCKED by %s:\n%s" % (name, (g.stdout + g.stderr).strip()[-1200:]))
            git("checkout", "--", PAGE)
            print("reverted %s; nothing committed." % PAGE)
            return 1
    print("gates clean: security, SEO, AutoQA")

    # 4. commit ONLY the page.
    git("add", "--", PAGE)
    staged = git("diff", "--cached", "--name-only").stdout.split()
    if staged != [PAGE.replace(os.sep, "/")]:
        print("BLOCKED: expected to stage only %s, got %s" % (PAGE, staged))
        git("reset", "HEAD", "--", PAGE)
        return 1

    msg = ("log: refresh public build log from source\n\n"
           "Automated nightly regeneration. Only log/index.html is touched; the "
           "privacy filter and the security/SEO/AutoQA gates all passed before "
           "this commit was created.")
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
