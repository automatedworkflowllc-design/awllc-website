# -*- coding: utf-8 -*-
"""Negative control for the security sweep.

This exists because the sweep was, for its whole life, unable to fail on the
credential this shop is likeliest to leak. Its key pattern was
`sk-[A-Za-z0-9]{20,}` -- which cannot match `sk-ant-api03-...`, because the
hyphen after "ant" ends the character run. An Anthropic key could sit in a
tracked file and the gate would print CLEAN and exit 0.

Nobody noticed because the sweep had only ever been observed passing. A check
that has never been seen to fail is not evidence of anything, so the duty here
is symmetrical and the second half matters as much as the first:

  1. every pattern catches a planted synthetic key
  2. ordinary page copy does NOT trip it -- a gate that cries wolf gets
     disabled, and a disabled gate is worse than none

Every value below is synthetic and non-functional. The AWS string is the
example key from AWS's own public documentation.

Run: python _qa/test_security_sweep.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from security_sweep import SECRETS


def label_for(text):
    """The label of the first pattern that fires, or None."""
    for rx, label in SECRETS:
        if rx.search(text):
            return label
    return None


# Every fixture is ASSEMBLED AT RUNTIME rather than written out, so this file
# contains no string that looks like a credential. That is not cosmetic: the
# first version spelled them literally, and the sweep -- correctly, with its
# newly widened pattern -- flagged six exposures in this very file and blocked
# the push. The obvious fix was to allowlist this path, which is exactly how a
# scanner rots: one exemption, then another, until it is scanning nothing that
# matters. Splitting the literals keeps the gate exemption-free.
_NOT_REAL = 'NOTAREAL'
_FILLER = '0123456789abcdefghij'

MUST_CATCH = [
    ('sk-' + 'ant-api03-' + _NOT_REAL * 5,
     'Anthropic key -- the regression this file exists for'),
    ('sk-' + _NOT_REAL + 'OPENAIKEY' + _FILLER,
     'OpenAI-style key without hyphens'),
    ('AWS_SECRET_ACCESS_KEY=' + _NOT_REAL + 'awssecret' + _FILLER + '+/=',
     'AWS secret access key assignment'),
    ('AKIA' + 'IOSFODNN7EXAMPLE',
     'AWS access key id'),
    # Exactly 35 chars after AIza, which is what the pattern requires.
    ('AIza' + (_NOT_REAL + _FILLER + 'GOOGLEKEYXX')[:35],
     'Google API key'),
    # Exactly 36 after ghp_. The first fixture was 35 and the test reported a
    # MISS -- the fixture was wrong, not the sweep. Counted by machine after
    # eyeballing it wrong once.
    ('ghp_' + (_NOT_REAL + 'GITHUBTOKEN' + _FILLER + 'zz')[:36],
     'GitHub personal access token'),
    ('-----BEGIN ' + 'RSA PRIVATE KEY-----',
     'private key block'),
]

# Real sentences from the kind of copy this site actually publishes. If any of
# these trips a pattern, the gate starts blocking honest pushes and somebody
# switches it off.
MUST_IGNORE = [
    'We do not ask for your API key, and there is no field to put one in.',
    'Nothing uploads: open your network tab while you drop the file.',
    'The privacy filter is the only thing making that page safe to publish.',
    'Install from these files, not by name: awllc-attest, awllc-canary.',
    'sk- is a common prefix, but this sentence carries no secret.',
    'Receipts are signed with a key only we hold, which is a stated limit.',
]


def main():
    failures = []

    for text, why in MUST_CATCH:
        if label_for(text) is None:
            failures.append('MISSED  %s\n        %s' % (why, text[:60]))

    for text in MUST_IGNORE:
        hit = label_for(text)
        if hit is not None:
            failures.append('FALSE ALARM  (%s)\n        %s' % (hit, text[:70]))

    if failures:
        print('SECURITY SWEEP TESTS FAILED')
        for f in failures:
            print('  ' + f)
        return 1

    print('security sweep: %d planted key(s) caught, %d honest sentence(s) ignored'
          % (len(MUST_CATCH), len(MUST_IGNORE)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
