# Heuristic

The heuristic estimates the minimum number of pushes needed to solve a given state. It is used by IDA* (Phase 5) as a lower bound to guide the search and prune branches that cannot improve on the best solution found so far.

The heuristic lives in `src/solver/heuristic.js`.

---

## Requirements

For IDA* to find an optimal solution, the heuristic must be *admissible* — it must never overestimate the true cost. An admissible heuristic that also never overestimates along any path is called *consistent* (or monotone), which additionally guarantees IDA* does not re-explore states.

---

## Lower bound: minimum box-to-goal matching

The heuristic computes the minimum total Manhattan distance over all possible one-to-one assignments of boxes to goals.

```js
heuristic(boxes, goals, width)
// → number; boxes is Set<number> of flat box indices, goals is Set<number> of flat goal indices, width is the grid width needed to convert flat indices to row/column coordinates; returns the lower-bound push count
```

### Why it is admissible

Each box must reach some goal, and each goal must be covered by exactly one box. The Manhattan distance between a box and a goal is a lower bound on the number of pushes needed to move that box to that goal (a push moves a box exactly one cell). Summing the optimal assignment gives a lower bound on the total pushes for the whole state.

### Hungarian algorithm

Finds the optimal assignment of n boxes to n goals in **O(n³)** time.

Steps:
1. Build an n×n cost matrix where `cost[i][j]` is the Manhattan distance from box `i` to goal `j`.
2. For each row of the cost matrix, subtract the smallest value in that row from every cell in that row — every row now has at least one zero.
3. For each column of the cost matrix, subtract the smallest value in that column from every cell in that column — every column now has at least one zero.
4. Find the minimum number of lines (rows or columns) needed to pass through every zero in the matrix. If n lines are needed, the zeros allow a complete optimal assignment — done. If fewer than n lines suffice, there are not enough independent zeros to assign every box to a unique goal, and step 5 creates more.

   Example (n=3): after steps 2.–3. the matrix is:
   ```
        G0  G1  G2
   B0 [  0   4   2 ]
   B1 [  3   0   1 ]
   B2 [  2   0   0 ]
   ```
   Zeros at (B0,G0), (B1,G1), (B2,G1), (B2,G2). Cover them with: column G1, row B0, row B2 — 3 lines, so n=3 lines suffice. The assignment selects exactly n zeros with no two in the same row or column: (B0,G0), (B1,G1), (B2,G2) — note (B2,G1) is covered by the lines but not selected. For each selected position (i,j), the original cost matrix value (before any subtractions) is looked up and summed to give the heuristic value. Optimal assignment: (B0,G0), (B1,G1), (B2,G2).
5. Otherwise, find the smallest uncovered value, subtract it from all uncovered cells, and add it to all doubly-covered cells. Repeat from step 4.

   Example: starting matrix after steps 2.–3.:
   ```
        G0  G1  G2
   B0 [  2   0   2 ]
   B1 [  1   0   5 ]
   B2 [  0   0   0 ]
   ```
   Zeros at (B0,G1), (B1,G1), (B2,G0), (B2,G1), (B2,G2). Minimum cover: row B2 and column G1 — only 2 lines, fewer than n=3. Since covering lines must pass through every zero, uncovered cells are guaranteed to be non-zero: (B0,G0)=2, (B0,G2)=2, (B1,G0)=1, (B1,G2)=5. Smallest uncovered value = 1.

   Subtract 1 from uncovered cells, add 1 to doubly-covered cell (B2,G1):
   ```
        G0  G1  G2
   B0 [  1   0   1 ]
   B1 [  0   0   4 ]
   B2 [  0   1   0 ]
   ```
   Zeros at (B0,G1), (B1,G0), (B1,G1), (B2,G0), (B2,G2). Minimum cover now needs 3 lines — done. Optimal assignment: (B0,G1), (B1,G0), (B2,G2).

---

## IDA* cost function

IDA* tracks the cost of the current path as:

```
f = g + h
```

where:
- `g` — number of pushes made so far (exact).
- `h` — heuristic lower bound for the remaining pushes (`heuristic(boxes, goals, width)`).

A branch is pruned when `f` exceeds the current depth threshold. The threshold starts at `h(initial state)` and increases by the minimum excess seen across all pruned nodes each iteration.