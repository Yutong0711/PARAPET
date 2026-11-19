# Copyright 2026 The PARAPET Authors
# SPDX-License-Identifier: Apache-2.0
"""PARAPET: security hardening as a performance-budgeted decision.

For one known weakness, PARAPET runs four stages:

* Generate candidate fixes (default generator: a local open-weight model),
* Validate that a candidate closes the weakness and keeps required behavior,
* Measure what the candidate costs on the project's own workload,
* Decide which candidates fit a budget the maintainer declared in advance.

The output is a decision and a reproducible hardening record.
"""

__version__ = "1.1.0-alpha"
