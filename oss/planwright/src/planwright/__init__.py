"""planwright — a maker of plans.

Turn a plain-Markdown plan (a table of work items with estimates and explicit
dependencies) into the three answers a project manager actually needs:

- what is ready to start now,
- what can run in parallel,
- what the critical path is.

The plan is data (a Markdown file in git). The engine is deterministic and has
zero third-party dependencies. See README.md and POSITIONING.md.
"""

from .model import Item, Plan, Status
from .parse import ParseError, parse_plan, parse_text

__all__ = ["Item", "ParseError", "Plan", "Status", "parse_plan", "parse_text"]
__version__ = "0.3.0"
