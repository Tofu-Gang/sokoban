# Deadlock Detection

A *deadlock* is a state from which the level cannot be solved. Detecting deadlocks early and pruning those branches is the single most effective way to reduce the solver's search space.

All deadlock logic lives in `src/engine/deadlock.js`.

---

## Dead squares

A square is *dead* if a box placed on it can never reach any goal, regardless of the positions of other boxes or the player. Goal squares are never dead by definition.

Dead squares are a static property of the level — they depend only on the grid, not on the current game state. They are computed once at level load and reused throughout the entire search at zero per-node cost. The result is a `Set<number>` of flat cell indices, allowing O(1) existence checks via `deadSquares.has(index)`.

```js
computeDeadSquares(grid, width, height)   // → Set<number> of dead cell indices; grid is the Uint8Array from GameState
```

### Algorithm

BFS over reverse push moves from every goal:

1. Start with all goal cells in the queue.
2. For each dequeued cell, ask: from which neighbor cells could a box have been pushed into this cell? For each of the four directions:
   - The box was at the neighbor cell, the player was one step further in the same direction, and pushed the box into the dequeued cell.
   - That player cell (two steps from the dequeued cell, opposite the neighbor) must be floor — if it is a wall, this push was impossible.
3. If the push was valid and the neighbor is a floor cell not yet visited, mark it reachable and enqueue it — it becomes the next dequeued cell, repeating from step 2.
4. Any floor cell not reached by this reverse BFS is a dead square.

### Usage

After every push in the solver, check whether the pushed box's new position is in `deadSquares`. If so, prune the state immediately — do not expand it further.

---

## Freeze deadlock

A *freeze deadlock* occurs when a group of boxes is stuck such that no box in the group can be pushed in any direction, and the group does not cover all goals.

Unlike dead squares, freeze deadlocks depend on the current box configuration and must be checked per node.

```js
isFrozenDeadlock(boxes, grid, width, height, pushedIndex)
// → boolean; boxes is Set<number> from GameState, grid is Uint8Array from GameState, pushedIndex is the flat index of the just-pushed box; checks the four 2×2 blocks containing pushedIndex
```

### Detected pattern: 2×2 block

Any 2×2 block containing at least one box and no empty floor cell (i.e. every cell is either a wall or a box) is a freeze deadlock, unless every box in the block is on a goal — a partial match (some boxes on goals, some not) is still a deadlock.

This covers the most common freeze pattern and is cheap to detect: after each push, check the four 2×2 blocks that include the pushed box's new position (top-left, top-right, bottom-left, bottom-right of it).

### Usage

Called after each push in the solver. If it returns `true`, prune the state.

---

## Summary

| Type | When computed | Per-node cost | Covers |
|------|--------------|---------------|--------|
| Dead squares | Once at level load | O(1) lookup | Single box, position-only |
| Freeze deadlock (2×2) | Every node | O(1) — checks 4 blocks | Multi-box mutual blocking |