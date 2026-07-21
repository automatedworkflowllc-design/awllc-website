# -*- coding: utf-8 -*-
"""Security sweep over the PUBLIC surface — codifies the "recurring security check
on AI-generated code" principle (gap #3), done on 2026-07-21 with a clean result.

Scope, deliberately narrow to what is actually exposed:
  - only GIT-TRACKED files (the repo is public; untracked local build scripts are not)
  - real secret signatures only (exact key formats), never generic entropy
  - the site's own embedded base64 fonts are EXPLICITLY excluded — they are ~58KB of
    random base64 per page and are the reason a naive scanner cries wolf every run.
    A checker that flags fonts on every push gets ignored, which is worse than none.

Checks:
  1. real secret patterns (Google AIza, OpenAI sk-, GitHub ghp_, AWS AKIA, PEM, client_secret)
  2. specific known-internal identifiers (sheet / workflow IDs) leaking into public files
  3. credential/env/key files accidentally committed

Run:  python _qa/security_sweep.py
Exit: 0 = clean · 1 = exposure found
"""
import io, os, re, sys, subprocess, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Exact secret signatures — precise on purpose. Generic "40+ char string" is what
# matched font data; these do not. AIza is capital-A only (a real Google key).
SECRETS = [
    (re.compile(r'AIza[0-9A-Za-z_-]{35}'),           'Google API key'),
    (re.compile(r'sk-[A-Za-z0-9]{20,}'),             'OpenAI/secret key'),
    (re.compile(r'ghp_[A-Za-z0-9]{36}'),             'GitHub PAT'),
    (re.compile(r'AKIA[0-9A-Z]{16}'),                'AWS access key'),
    (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY'),   'private key block'),
    (re.compile(r'client_secret["\s:=]+[A-Za-z0-9_-]{20,}'), 'OAuth client secret'),
]

# Specific internal identifiers that must NEVER appear in a public file — stored as
# SHA256 HASHES, not plaintext, because this file is itself git-tracked and public.
# (Listing the raw IDs here would leak them — the sweep caught exactly that on 7/21.)
# Detection: extract candidate ID tokens from each file, hash, compare to this set.
INTERNAL_ID_HASHES = {
    "1ea166a438e1ee916e1c1a0be81f04c79418b0851e355fae6bab3ee85b7a1e3a",  # S1 metrics sheet
    "c52476a0ee8677df3a2bf8db8ad327d73937c47c060e6de640617f9ca3d506e5",  # S2 workflow
    "e5a297030dd2dc0821044fbf0e6b30a05c89995cda356c0423b59505cd977bf8",  # S1 workflow
    "b44bc1b095fd4a2de1cb64e065968360328eda6e19a55a0cb221d124adfe337b",  # S2 config sheet
    "8fe3e7a5e46706617d2a33bc9d7cd1564194bf6575940cf57c4b2879bdff5908",  # lead tracker
}
# candidate identifier tokens: 44-char Drive IDs and 16-char n8n workflow IDs
ID_TOKEN = re.compile(r'\b(?:1[A-Za-z0-9_-]{43}|[A-Za-z0-9]{16})\b')

CRED_FILE = re.compile(r'(^|/)(\.env|.*\.pem|.*\.key|.*credential.*|secrets.*|\.clasprc.*)$', re.I)

findings = []

def tracked_files():
    out = subprocess.run(['git', 'ls-files'], cwd=ROOT, capture_output=True, text=True)
    return [f for f in out.stdout.splitlines() if f.strip()]

def strip_font_blocks(text):
    """Remove data:...base64,<blob> runs so font data can't produce false hits."""
    return re.sub(r'base64,[A-Za-z0-9+/=]+', 'base64,<stripped>', text)

def main():
    files = tracked_files()
    if not files:
        findings.append(('setup', 'no git-tracked files found — not in a repo?'))
    for rel in files:
        p = os.path.join(ROOT, rel)
        if CRED_FILE.search(rel):
            findings.append((rel, 'credential/env/key file is committed'))
        if not os.path.exists(p):
            continue
        try:
            raw = io.open(p, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        text = strip_font_blocks(raw)   # fonts can't false-positive past this
        for rx, label in SECRETS:
            if rx.search(text):
                findings.append((rel, 'possible %s' % label))
        for tok in set(ID_TOKEN.findall(text)):
            if hashlib.sha256(tok.encode()).hexdigest() in INTERNAL_ID_HASHES:
                findings.append((rel, 'internal identifier exposed (%s…)' % tok[:6]))

    print('SECURITY SWEEP  —  %d tracked files scanned' % len(files))
    if not findings:
        print('  CLEAN — no secrets, internal IDs, or credential files in the public surface.')
        return 0
    for f, msg in findings:
        print('  [EXPOSED] %-40s %s' % (f, msg))
    print('\n  %d exposure(s). Rotate/redact before the next push.' % len(findings))
    return 1

if __name__ == '__main__':
    sys.exit(main())
