# Solver

The solver runs entirely in a Web Worker to keep the UI responsive. It searches over the *push-space* of a level — exponentially smaller than move-space — and posts results back to the main thread.

All solver modules live in `src/solver/`.

---

## Push-space search

A *push* is a single box displacement: the player moves adjacent to a box and pushes it one cell in some direction. The solver treats each push as one search step, not each player move.

This is valid because:
- The player's exact path between pushes is irrelevant to the solution.
- Player routing between pushes is a sub-problem solved by reachability BFS (see `engine/moves.js`).
- The branching factor drops dramatically compared to move-space.

---

## Canonical state

Two game states are equivalent if they share the same box positions and the player can reach the same set of cells. The solver collapses such states into one canonical form to avoid redundant exploration.

**Canonical state = sorted box positions + player reachable region**

In practice, a canonical key is constructed as:
- The player position is replaced by the **top-left-most cell** of the player's reachable region (the normalized player position).
- Box positions are stored as a sorted array of flat indices.

Two states with the same canonical key are identical from the solver's perspective and are deduplicated via a transposition table.

---

## Algorithms

### BFS (`bfs.js`)

Breadth-first search over the push-state space. Used for smaller/simpler levels (Microban). No heuristic — just deadlock pruning.

- **Complete**: always finds the shortest solution (fewest pushes).
- **Memory**: stores every visited state in a transposition table — becomes impractical for large levels.
- **Use**: Phase 3 baseline; reliable reference implementation.

```js
bfs(state, deadSquares)   // → number[][] of flat box indices per push, or null if no solution found
```

### IDDFS (`iddfs.js`)

Iterative-deepening depth-first search. Used for larger levels (XSokoban) where BFS runs out of memory. Same deadlock pruning as BFS, plus the heuristic to guide and prune the search.

- **Complete**: yes, finds optimal solution when combined with a consistent heuristic (IDA*).
- **Memory**: O(depth) — negligible compared to BFS.
- **Use**: Phase 5 — replaces BFS for levels where BFS runs out of memory.

```js
iddfs(state, deadSquares, heuristic)   // → number[][] of flat box indices per push, or null if no solution found
```

### Heuristic (`heuristic.js`)

See `docs/heuristic.md`.

### Dynamic pruning (`pi-corral.js`)

See `docs/pi-corral.md`. PI-corral pruning — reduces the effective branching factor at each node by restricting pushes to the boundary boxes of the most constrained PI-corral. Applied in IDDFS (Phase 5), not BFS.

---

## Transposition table

Both BFS and IDDFS use a transposition table (a `Set<string>`) to avoid revisiting equivalent states.

The key is a string serialization of the canonical state:

```js
`${normalizedPlayerIndex}:${sortedBoxIndices.join(",")}`
```

---

## Deadlock pruning

At every node, before expanding successors, prune states where:
- Any box lands on a dead square (precomputed — see `docs/deadlock.md`), or
- The state is a freeze deadlock.

Dead squares are passed into the solver once at startup and reused across all nodes at zero per-node cost.

---

## Worker message protocol (`worker.js`)

Communication between the main thread (`useSolver.js`) and the worker (`worker.js`) uses `postMessage`.

### Main → Worker

```js
// Start solving
{ type: "SOLVE", state: SerializedState, deadSquares: number[] }

// Abort current search
{ type: "ABORT" }
```

### Worker → Main

```js
// Solution found
{ type: "SOLUTION", pushes: number[][] }

// No solution exists
{ type: "NO_SOLUTION" }

// Search aborted
{ type: "ABORTED" }

// Periodic progress update
{ type: "PROGRESS", nodesExplored: number }
```

### SerializedState

`GameState` cannot cross the Worker boundary directly (`Set` and `Uint8Array` require explicit handling). The serialized form is a plain object:

```js
{
    width: number,          // grid width in cells
    height: number,         // grid height in cells
    grid: number[],         // Uint8Array converted to plain array
    player: { 
        row: number, 
        column: number 
    },
    boxes: number[],        // Set<number> converted to array
}
```

The worker reconstructs a full `GameState` from this before searching.

---

## Solution format

A solution is an array of pushes. Each push is represented as a pair:

```js
[boxIndex, targetIndex]   // flat indices: box before push, box after push
```

The main thread replays the solution by:
1. For each push: computing the player's path to the push position via BFS (`reachable`), then applying the push.
2. Animating each step at a configurable playback speed.