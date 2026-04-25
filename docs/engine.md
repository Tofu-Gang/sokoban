# Engine

The engine is pure JS with zero React dependencies. Every module is fully testable in isolation.

All modules live in `src/engine/`.

---

## State (`state.js`)

### GameState shape

```js
{
  width: number,          // grid width in cells
  height: number,         // grid height in cells
  grid: Uint8Array,       // flat row-major array, length = width * height, encoded as row * width + column
  player: {
    row: number,
    column: number,
  },
  boxes: Set<number>,     // encoded as row * width + column
}
```

### Cell encoding (`grid`)

The `grid` stores static terrain only — walls, floors, and goals. Boxes and the player are tracked separately and are never written into `grid`.

| Value | Constant | Meaning |
|-------|----------|---------|
| `0`   | `FLOOR`  | Walkable floor (includes out-of-bounds treated as wall) |
| `1`   | `WALL`   | Wall |
| `2`   | `GOAL`   | Goal square |

### Cell index helpers

```js
cellIndex(row, column, width)   // → row * width + column
cellRow(index, width)           // → Math.floor(index / width)
cellColumn(index, width)        // → index % width
```

### Constructing a GameState

```js
fromLevel(level)       // Level → GameState; parses XSB chars into grid/player/boxes
```

`fromLevel` reads each character of `level.grid`, populates the `Uint8Array`, sets `player`, and builds `boxes`. Goals under a player or box are recorded in `grid` as `GOAL`.

### Copying a GameState

States must be copied before mutation (undo stack, solver nodes):

```js
clone(state)           // → deep copy: new Uint8Array, new Set, new player object copy
```

---

## Moves (`moves.js`)

### Direction constants

```js
const DIRECTIONS = {
  UP:    { deltaRow: -1, deltaColumn:  0 },
  DOWN:  { deltaRow:  1, deltaColumn:  0 },
  LEFT:  { deltaRow:  0, deltaColumn: -1 },
  RIGHT: { deltaRow:  0, deltaColumn:  1 },
};
```

### Move validation

```js
canMove(state, direction)   // → boolean
```

Returns `true` if the move is legal:
- Target cell is not a wall.
- If target cell has a box: the cell beyond the box is floor or goal (not wall, not another box).

### Move execution

```js
applyMove(state, direction)  // → new GameState (does not mutate input)
```

1. Clone the state.
2. Move player to target cell.
3. If a box was pushed, update `boxes`: remove old position, add new position.
4. Return the new state.

`applyMove` does not check legality — call `canMove` first.

### Win detection

```js
isSolved(state)   // → boolean; true when every box index is a GOAL cell in grid
```

### Reachability (player flood-fill)

Used by the solver to compute the canonical player region — two states with the same box positions but different player positions within the same reachable region are equivalent.

```js
reachable(state)   // → Set<number> of cell indices the player can reach without pushing a box
```

Implemented as BFS from `state.player`. Walls and box positions are treated as blocked.

---

## Deadlock detection (`deadlock.js`)

Precomputed once per level load. Not recalculated per move.

### Dead squares

A square is *dead* if a box placed on it can never be pushed to any goal, regardless of other box positions.

```js
computeDeadSquares(state)   // → Set<number> of dead cell indices
```

Algorithm: reverse BFS ("pull" moves) from every goal. Any floor cell not reachable in reverse is a dead square.

### Freeze deadlock

A group of boxes is *frozen* if no box in the group can be pushed in any direction. A frozen group not covering all goals is a deadlock.

Detected patterns (in addition to dead squares):
- Any 2×2 block of boxes and/or walls with at least one box.

```js
isFrozenDeadlock(state)   // → boolean
```

### Usage

In the solver, prune any successor state where:
- Any box lands on a dead square, or
- `isFrozenDeadlock` returns `true`.

Dead squares are passed into the solver at startup and reused across all nodes at no per-node cost.