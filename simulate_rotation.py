# ============================================================
# SIMULATE CURRENT FARM ROTATION
# ============================================================
#
# Execute THIS file manually when you want to benchmark.
#
# It:
#
#   1. Copies current unlock levels
#   2. Copies current inventory
#   3. Starts a simulation
#   4. Runs benchmark_rotation
#   5. Uses a fixed seed for reproducibility
#   6. Does NOT modify the real farm
#
#
# To compare algorithm A vs algorithm B:
#
#   - keep SIM_SEED the same
#   - run this file
#   - record result
#   - change code
#   - run it again
#
# Lower simulated time wins.
# ============================================================


SIM_SEED = 1

SIM_SPEEDUP = 10000


# ============================================================
# COPY CURRENT UNLOCK LEVELS
# ============================================================

sim_unlocks = {}


for unlock_type in Unlocks:

	level = num_unlocked(
		unlock_type
	)


	if level > 0:

		sim_unlocks[
			unlock_type
		] = level


# ============================================================
# COPY CURRENT INVENTORY
# ============================================================

sim_items = {}


for item in Items:

	amount = num_items(
		item
	)


	if amount > 0:

		sim_items[
			item
		] = amount


# ============================================================
# RUN
# ============================================================

run_time = simulate(
	"benchmark_rotation",
	sim_unlocks,
	sim_items,
	{},
	SIM_SEED,
	SIM_SPEEDUP
)


quick_print(
	"[SIMULATION]",
	"one full rotation:",
	run_time,
	"seconds"
)
