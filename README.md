# TFWR — The Farmer Was Replaced automation

Scripts from my `Save0` save of [The Farmer Was Replaced](https://store.steampowered.com/app/2060160/The_Farmer_Was_Replaced/).
The game has you program a drone in a Python-like language. This repo holds a
fully automated farm that runs forever: it buys upgrades, keeps Gold and Bone
stocked, and cycles through every crop across the whole field using parallel
drones. It also includes benchmark and simulation scripts used to tune it.

> **Language note:** the in-game language only *looks* like Python. There are no
> classes, no real imports beyond other save files, and only the game's
> builtins are available. `__builtins__.py` (not tracked) is a community-made
> set of type stubs so VS Code can autocomplete. It is never executed.

---

## Quick start

1. Open the save in game (the files in this folder are the in-game code windows).
2. Run **`main`**. It loops forever.
3. To change behaviour, edit [`farm_config.py`](farm_config.py) first. Most
   tuning knobs live there.

This folder **is** the live save. Checking out a git branch changes the code
the game loads, so switch back to `main` before playing normally.

---

## How the main loop works

[`main.py`](main.py) repeats four steps:

| Step | Module | What it does |
|---|---|---|
| 1 | [`farm_unlocks`](farm_unlocks.py) | Spends only **surplus** resources on upgrades, in priority order |
| 2 | [`farm_maze`](farm_maze.py) | If Gold < `gold_floor`, runs maze batches until it's restored |
| 3 | [`farm_dinosaurs`](farm_dinosaurs.py) | If Bone < `bone_floor`, runs a dinosaur snake run |
| 4 | [`farm_rotation`](farm_rotation.py) | Runs one full-field crop rotation |

Auto-unlocks happen **only between rotations**. Buying `Expand` clears the
farm, so an unlock in the middle of a crop phase would destroy it.

### Crop rotation (`farm_rotation.run_cycle`)

Each phase checks up front that it can pay for a whole field. If it can't, it
skips the phase instead of starting a field it can't finish.

1. **Wood / Hay**: Trees on a checkerboard, Grass on the other tiles (on odd
   world sizes the last row and column are left out so no two Trees touch).
   Harvested with Polyculture when unlocked.
2. **Carrots**: full soil field, then Polyculture harvest.
3. **Sunflowers**: measure every flower and sort them into buckets by petal
   count (15 → 7). Each bucket is harvested in parallel, largest first,
   keeping the ≥10-sunflowers-remaining bonus rule. Inside a bucket, points
   are visited in serpentine order ([`sun_sort`](sun_sort.py)).
4. **Pumpkins**: plant the whole field and replant dead pumpkins until
   the pumpkin at (0,0) and the one at (n-1,n-1) have the same `measure()` id
   (one merged mega-pumpkin). Then harvest once.
5. **Cactus**: parallel cocktail-shaker sort of every row, then every column
   ([`cact_sort`](cact_sort.py)), then one chain harvest at (0,0).

Growth boost everywhere: water below `water_level`, then fertilize until the
plant is harvestable.

---

## File map

### Production code (used by `main`)

| File | Purpose |
|---|---|
| [`main.py`](main.py) | Top-level forever loop (see above) |
| [`farm_config.py`](farm_config.py) | `SETTINGS`, per-crop hat toggles, per-crop fertilizer toggles |
| [`farm_common.py`](farm_common.py) | Shared helpers: wraparound `go_to`, cost checks, water/fertilizer, soil/grassland, hat state, timing prints |
| [`farm_megafarm.py`](farm_megafarm.py) | Parallel drone helpers (see below) |
| [`farm_rotation.py`](farm_rotation.py) | The five-phase crop rotation |
| [`farm_polyculture.py`](farm_polyculture.py) | Companion-planting harvest: scan → plan → fused execute → reject cleanup |
| [`farm_unlocks.py`](farm_unlocks.py) | Auto-research with operating reserves |
| [`farm_maze.py`](farm_maze.py) | Gold: maze creation, target-guided DFS solver, maze reuse |
| [`farm_dinosaurs.py`](farm_dinosaurs.py) | Bones: Hamiltonian-cycle dinosaur run |
| [`farm_telemetry.py`](farm_telemetry.py) | Profiler: phase/sub-phase timing, resource deltas, drone utilisation, counters |
| [`cact_sort.py`](cact_sort.py) | Parallel cactus row/column sorter |
| [`sun_sort.py`](sun_sort.py) | Serpentine ordering for sunflower harvest points |

### Benchmarking and debugging (run manually)

| File | Purpose |
|---|---|
| [`benchmark_rotation.py`](benchmark_rotation.py) | Profiles one crop rotation (no unlocks, mazes, or dinosaurs) and prints a telemetry report |
| [`benchmark_full_cycle.py`](benchmark_full_cycle.py) | Profiles maze + dinosaurs (if needed) + rotation |
| [`simulate_rotation.py`](simulate_rotation.py) | Runs `benchmark_rotation` in `simulate()` with a fixed seed and the current unlocks and inventory. The real farm is not touched |
| [`debug_rotation.py`](debug_rotation.py) | Runs one rotation on a small world (default 6×6) at adjustable speed so you can watch it |

### Achievement and strategy experiments

These stand alone: the `*_ab`, `hay_bo`, and `hay_fc` targets import nothing
from the production modules. Each `sim_*` driver runs its target through
`simulate()` over several seeds and prints a winner.

| Driver | Target | Question it answers |
|---|---|---|
| [`sim_h2.py`](sim_h2.py) | [`hay_ab.py`](hay_ab.py) | Best static Grass layout for 200M Hay in 60 s (checkerboard vs. alternating rows vs. every 4th row) |
| [`sim_bo.py`](sim_bo.py) | [`hay_bo.py`](hay_bo.py) | Harvest all sources vs. only boosted ones vs. wait on boosted ones |
| [`sim_fc.py`](sim_fc.py) | [`hay_fc.py`](hay_fc.py) | Sparse vs. full vs. fixed companion layout, steady-state throughput |
| [`sim_wood.py`](sim_wood.py) | [`wood_ab.py`](wood_ab.py) | Wood layout (Bush / Tree-Bush mix / Tree-poly / Bush-poly) × dry/wet for 1B Wood in 60 s |
| [`sim_sun.py`](sim_sun.py) | [`sun_ab.py`](sun_ab.py) | Sunflower harvest order: current vs. serpentine vs. nearest-neighbour route |
| — | [`hay_run.py`](hay_run.py) | The real 200M-Hay run, using the winning fixed-companion checkerboard |

Most experiment scripts use **`RUN=False`** for a setup-only baseline. The
driver subtracts that time from the `RUN=True` time, so the result measures
farming alone and not setup or drone spawning.

---

## Megafarm helpers

[`farm_megafarm.py`](farm_megafarm.py) is the only place drones are spawned.
Every helper follows the same pattern:

- `worker_count(n)` = `min(free drones + 1, n)`. The calling drone also does
  work.
- **Row helpers** (`run_rows`, `run_rows_bool`, `collect_rows`, `sum_rows`, and
  the `_with_arg` variants) split rows into stripes. Worker `k` handles rows
  `k, k+count, k+2·count, …`.
- **Item helpers** (`run_items`, `sum_items`) split a list into contiguous
  chunks.
- If `spawn_drone` fails, that stripe or chunk runs serially on the
  coordinator.
- Results are combined on the coordinator with `wait_for`: AND for bool,
  concatenation for lists, and addition for sums.

**Gotchas:**
- Each drone has **its own module state**, so telemetry only counts on the
  coordinator drone.
- Inventory is **shared**. `shared_item_available` makes sure at least one
  item per active drone is in stock before using Water or Fertilizer, which
  avoids races where two drones spend the same last item.
- Row workers must start with `go_to(0, row)` and must not assume where the
  drone is.

---

## Configuration

All in [`farm_config.py`](farm_config.py):

| Setting | Default | Meaning |
|---|---|---|
| `water_level` | `0.5` | Water a tile when its water is below this |
| `timing_enabled` | `True` | Print `[TIMING]` lines from `main` |
| `auto_unlock_enabled` | `True` | Allow `farm_unlocks.manage()` to buy upgrades |
| `unlock_farm_reserve_multiplier` | `2.0` | Keep this many rotations' worth of planting costs before buying upgrades |
| `mazes_enabled` / `gold_floor` | `True` / `100000` | Run mazes while Gold is below the floor |
| `dinosaurs_enabled` / `bone_floor` | `True` / `100000` | Run dinosaurs while Bone is below the floor |

`HAT_ENABLED` (all off) and `FERTILIZE` (all on) are per-crop toggles.

### Upgrade priority

`Speed → Megafarm → Expand → Fertilizer → Watering → Polyculture → Mazes →
Dinosaurs → Sunflowers → Trees → Grass → Carrots → Pumpkins → Cactus`

Each unlock appears only once. `unlock(Unlocks.Expand)` buys whatever the next
level is. After every purchase the manager rebuilds all reserves and starts
again from the top, because an upgrade can change world size, costs, or drone
count.

Reserves kept before any purchase:
- 2× one rotation's planting cost (pumpkins count as 3 fields for replants)
- the Gold and Bone floors
- Weird Substance for one maze, when Gold is low
- a full board of Apples, when Bone is low

---

## Benchmark results recorded in code

| Change | Setup | Before | After |
|---|---|---|---|
| Skip cactus verification pass | 22×22, 8 drones | 68.98 s | 65.44 s (−5.1%) |
| Serpentine sunflower order | fixed seeds ×5 | 30.01 s | 25.99 s (−13.4%, 5/5 wins) |
| Fixed-companion Hay checkerboard | 32 drones, 200M Hay | — | avg ~33.36 s, worst ~33.71 s |

When a new experiment wins, record the numbers in the module header comment
and in this table.

---

## Profiling workflow

1. Run `simulate_rotation` (fixed seed, fast) or `benchmark_rotation` (real).
2. Read the report between `<<< FARM_PROFILE_BEGIN >>>` and
   `<<< FARM_PROFILE_END >>>` in the game's `output.txt`. It includes a phase
   ranking, drone utilisation, sub-phase ranking, the bottleneck, counters,
   and resource rates.
3. Change the code, re-run with the **same seed**, and compare. Lower
   simulated time wins.

---

## Repository conventions

- **`main` is always what the farm should run.** Every change goes on a
  feature branch (`feat/…`, `fix/…`, `perf/…`, `docs/…`). Test it in game or in
  simulation, then merge through a pull request.
- **Keep this README current.** Any PR that adds or removes a file, changes
  settings or the upgrade priority, or produces new benchmark numbers should
  update the matching section here.
- **Not tracked** (see [`.gitignore`](.gitignore)): `save.json`, which the game
  rewrites constantly (inventory, unlocks, editor layout), and
  `__builtins__.py`, the editor type stubs.
- **Code style:** tabs, generous vertical spacing, `# ===` section banners, and
  one argument per line in calls. New code should match.
