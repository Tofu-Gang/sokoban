# Dynamic Pruning

Dynamic pruning reduces the effective branching factor at each search node by restricting which pushes need to be explored. Unlike deadlock pruning (which eliminates entire branches after they are taken), dynamic pruning eliminates pushes that provably cannot contribute to a solution from the current node.

Dynamic pruning lives in `src/solver/pi-corral.js` and is called inside the node expansion loop in `iddfs.js`, alongside deadlock checks, before generating successors. It is **not** applied to BFS — Microban levels are small enough that BFS handles them without it.

---

## Corrals

A *corral* is a maximal connected set of floor cells that the player cannot currently reach, blocked by a combination of walls and boxes.

The *boundary boxes* of a corral are the boxes adjacent to corral cells — the boxes that form part of the corral's enclosure.

### Example

```
#########
#   $   #
# $@$ . #
#   $   #
#########
```

The player (`@`) can only reach the left-hand area. The three boxes in column 4 (rows 1–3) seal off the entire right-hand region — those cells (including the goal `.`) are unreachable and form a corral. Each boundary box can only be pushed rightward into the corral (pushing leftward would require the player to stand in the corral), making this a PI-corral.

---

## PI-corrals

A corral is first an *I-corral* if all boundary boxes can only be pushed into the zone — which is trivially true for every corral, since pushing a boundary box outward would require the player to stand inside the corral, which is impossible by definition.

A *PI-corral* (Player-Inaccessible corral) is an I-corral where the player can additionally reach all boundary boxes and perform the inward pushes. Concretely: for every boundary box, there must exist at least one inward push direction where the player can reach the required push position (outside the corral, adjacent to the box) and the push destination (inside the corral) is free.

### Why PI-corrals enable pruning

Consider a PI-corral with goals inside. Any solution must eventually push boxes into the corral to cover those goals. The key insight is that the corral is *independent* of the rest of the board — pushing a boundary box into the corral does not affect the player's ability to make any other push elsewhere. This means:

> Any solution that makes a non-boundary push before addressing the corral can be reordered to address the corral first, yielding an equally valid solution of the same cost.

Therefore, at a node where a PI-corral exists, the solver only needs to explore **pushes of boundary boxes of that corral**. All other pushes can be deferred to successor nodes. This replaces "all legal pushes" with "boundary pushes of one corral", dramatically cutting the branching factor.

If no goals exist inside the corral, any push of a boundary box into it is futile — a box pushed into a goalless corral can never reach a goal and will be caught by dead square detection. PI-corral pruning discards these pushes before they are even generated.

---

## Detection algorithm

```js
findPICorral(boxes, grid, width, height, playerReachable)
// → Set<number> of boundary box flat indices, or null if no PI-corral exists
// boxes: Set<number> of flat box indices from GameState
// grid: Uint8Array from GameState
// width, height: grid dimensions
// playerReachable: Set<number> of flat indices the player can currently reach
```

Steps:

1. **Find corrals.** A corral is a connected component of non-wall, non-box cells not included in `playerReachable`. For each cell in the grid: if it is floor or goal, not a box, and not in `playerReachable`, flood-fill to collect the full corral.

2. **Find boundary boxes.** For each corral cell, check its four neighbors. Any neighbor that is a box is a boundary box of that corral.

3. **Check PI condition.** For each boundary box, verify the player can perform at least one valid inward push. An inward push is valid if:
   - The push origin (the player cell adjacent to the box, on the outside of the corral) is in `playerReachable`.
   - The push destination (the cell on the corral side of the box) is floor or goal and not a box.

   If *any* boundary box has no valid inward push, the corral is not a PI-corral — skip it.

4. **Return.** If a corral passes the PI check, return its boundary boxes as a `Set<number>`. If multiple PI-corrals exist, return the one with the fewest boundary boxes (most constrained). If none exist, return `null`.

---

## Pruning rule

```js
// Inside the IDDFS node expansion loop:
const piCorralBoundary = findPICorral(boxes, grid, width, height, playerReachable);
const allowedBoxes = piCorralBoundary ?? boxes;  // if null, all boxes are candidates

for (const boxIndex of allowedBoxes) {
    // generate pushes only for boxes in allowedBoxes
}
```

When a PI-corral is found, only its boundary boxes are offered as push candidates for this node. When none is found, all boxes are candidates as normal.

---

## Integration in `iddfs.js`

The player's reachable region is already computed at each node to build the canonical state (see `docs/solver.md`). Pass that set directly into `findPICorral` — no redundant BFS needed.

Call order within node expansion:

1. Compute player reachable region (needed for canonical key and PI-corral detection).
2. Check transposition table — skip if already visited.
3. Compute heuristic — prune if `g + h > threshold`.
4. Call `findPICorral` — restrict push candidates to boundary boxes if a PI-corral exists.
5. For each push candidate box, generate legal push directions, apply dead square and freeze deadlock checks, then recurse.

---

## Summary

| Property | Value |
|----------|-----------------------------------------------------------------------|
| Applies to | IDDFS only (Phase 5) |
| Input | Current node's reachable region + box/grid state |
| Output | Boundary box set, or null |
| Cost | One BFS-like flood fill per node |
| Benefit | Branching factor reduced from all legal pushes to boundary pushes of one corral |
| Primary reference | Virkkala thesis, Section 4.4.1 (definition), Section 5.3 (experiments) |