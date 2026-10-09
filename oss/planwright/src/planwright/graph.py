"""Turn a plan into the manager's three answers.

Every computation here is deterministic and depends only on the plan's items
and their ``depends`` edges — never on an LLM. That is the point: the schedule
is a fact you can check, not an opinion.

Definitions
-----------
- **ready**: a not-done item whose dependencies are all done. Start these now.
- **blocked**: a not-done item with at least one not-done dependency, listed
  with the exact ids it waits on.
- **parallel layers**: a topological layering of the *unfinished* items. Items
  in the same layer share no dependency ordering, so they can run at once.
- **critical path**: the longest chain through the DAG by summed estimate; its
  length is the floor on how long the remaining work can take, however many
  people you add.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import Item, Plan


@dataclass
class Cycle:
    """A dependency cycle, as the ordered list of ids forming the loop."""

    nodes: list[str]

    def __str__(self) -> str:
        return " -> ".join([*self.nodes, self.nodes[0]])


@dataclass
class CriticalPath:
    ids: list[str]
    hours: float


@dataclass
class Graph:
    plan: Plan

    def __post_init__(self) -> None:
        self._deps: dict[str, list[str]] = {it.id: list(it.depends) for it in self.plan}

    # -- integrity -------------------------------------------------------

    def dangling_dependencies(self) -> list[tuple[str, str]]:
        """(item_id, missing_dep) for each dependency that names no known item."""
        out: list[tuple[str, str]] = []
        for it in self.plan:
            for dep in it.depends:
                if not self.plan.has(dep):
                    out.append((it.id, dep))
        return out

    def self_dependencies(self) -> list[str]:
        return [it.id for it in self.plan if it.id in it.depends]

    def find_cycles(self) -> list[Cycle]:
        """Return dependency cycles (DFS). Dangling deps are ignored here."""
        WHITE, GREY, BLACK = 0, 1, 2
        color: dict[str, int] = {it.id: WHITE for it in self.plan}
        stack: list[str] = []
        cycles: list[Cycle] = []
        seen_signatures: set[frozenset[str]] = set()

        def visit(node: str) -> None:
            color[node] = GREY
            stack.append(node)
            for dep in self._deps.get(node, []):
                if not self.plan.has(dep):
                    continue
                if color[dep] == GREY:
                    loop = stack[stack.index(dep) :]
                    sig = frozenset(loop)
                    if sig not in seen_signatures:
                        seen_signatures.add(sig)
                        cycles.append(Cycle(list(loop)))
                elif color[dep] == WHITE:
                    visit(dep)
            stack.pop()
            color[node] = BLACK

        for it in self.plan:
            if color[it.id] == WHITE:
                visit(it.id)
        return cycles

    def is_schedulable(self) -> bool:
        """True when the graph can be scheduled: no cycles, no dangling deps."""
        return not self.find_cycles() and not self.dangling_dependencies()

    # -- status buckets --------------------------------------------------

    def _done(self, item_id: str) -> bool:
        it = self.plan.get(item_id)
        return it is not None and it.status.is_done

    def ready(self) -> list[Item]:
        """Not-done items whose every known dependency is done."""
        out: list[Item] = []
        for it in self.plan:
            if it.status.is_done:
                continue
            if all(self._done(d) for d in it.depends if self.plan.has(d)):
                out.append(it)
        return out

    def blocked(self) -> dict[str, list[str]]:
        """{item_id: [unfinished dependency ids]} for not-done items that wait."""
        out: dict[str, list[str]] = {}
        for it in self.plan:
            if it.status.is_done:
                continue
            waiting = [d for d in it.depends if self.plan.has(d) and not self._done(d)]
            if waiting:
                out[it.id] = waiting
        return out

    # -- scheduling ------------------------------------------------------

    def parallel_layers(self) -> list[list[str]]:
        """Topological layers of the unfinished items (Kahn's algorithm).

        Raises ValueError if the graph is not schedulable (cycle/dangling);
        callers should check :meth:`is_schedulable` first.
        """
        if not self.is_schedulable():
            raise ValueError("cannot layer a plan with cycles or dangling dependencies")
        pending = {it.id for it in self.plan if not it.status.is_done}
        # Edges restricted to unfinished items (done deps are already satisfied).
        remaining: dict[str, set[str]] = {
            node: {d for d in self._deps.get(node, []) if d in pending} for node in pending
        }
        layers: list[list[str]] = []
        while pending:
            layer = sorted(n for n in pending if not remaining[n])
            if not layer:  # defensive: a cycle would do this, but we checked
                raise ValueError("unexpected cycle while layering")
            layers.append(layer)
            pending -= set(layer)
            done_now = set(layer)
            for node in pending:
                remaining[node] -= done_now
        return layers

    def critical_path(self) -> CriticalPath:
        """Longest path by summed estimate over all items (done + not done).

        A missing estimate counts as 0 hours, so the number is a lower bound
        until every item on the path is estimated.
        """
        if not self.is_schedulable():
            raise ValueError("cannot compute a critical path with cycles or dangling dependencies")

        memo: dict[str, tuple[float, list[str]]] = {}

        def cost(item_id: str) -> tuple[float, list[str]]:
            if item_id in memo:
                return memo[item_id]
            it = self.plan.get(item_id)
            own = (it.estimate_hours or 0.0) if it else 0.0
            best_hours = 0.0
            best_chain: list[str] = []
            for dep in self._deps.get(item_id, []):
                if not self.plan.has(dep):
                    continue
                dh, dchain = cost(dep)
                if dh > best_hours:
                    best_hours, best_chain = dh, dchain
            memo[item_id] = (own + best_hours, [*best_chain, item_id])
            return memo[item_id]

        best = CriticalPath(ids=[], hours=0.0)
        for it in self.plan:
            hours, chain = cost(it.id)
            if hours > best.hours:
                best = CriticalPath(ids=chain, hours=hours)
        return best
