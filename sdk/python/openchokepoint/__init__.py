# Handling: Unclassified — public
# SPDX-License-Identifier: Apache-2.0
"""OpenChokepoint Python SDK.

A thin, read-only client for OpenChokepoint instance files. It loads a registry, answers
graph questions about it, and validates it with the project's own validator
(tools/validate.py), so the SDK never carries a second copy of the rules.

    from openchokepoint import Registry, validate

    reg = Registry.load("examples/synthetic-turbopump-thread.yaml")
    for issue in validate("examples/synthetic-turbopump-thread.yaml"):
        print(issue.rule, issue.message)

The SDK records facts and pointers only. It does not score, rank or judge any
organization or part. See CONTRIBUTION-SCOPE.md and docs/digital-thread.md.
"""
from .registry import Record, Registry, find_root
from .validation import Issue, validate

__all__ = ["Issue", "Record", "Registry", "find_root", "validate"]
__version__ = "0.1.0"
