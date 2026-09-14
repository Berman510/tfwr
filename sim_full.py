# ============================================================
# FULL AUTOMATION (FASTEST RESET) SIMULATION
# ============================================================
#
# Runs full_run.py in simulate() from the state a Fastest Reset
# starts with (archive/lb_reset_probe.py):
#
#   - every language unlock at 1, Grass at 1
#   - every farm unlock at 0
#   - no items
#
# full_run prints its own [FR] timeline (every purchase, every
# change of farming target) to output.txt. This driver adds the
# total simulated time per seed.
#
#
# Output:
#
#   output.txt, between
#
#       <<< FULL_BENCH_BEGIN >>>
#       <<< FULL_BENCH_END >>>
#
# Does NOT modify the real farm.
# ============================================================


SEEDS = [
	1
]


SIM_SPEEDUP = 10000


RESET_UNLOCKED = [
	Unlocks.Auto_Unlock,
	Unlocks.Costs,
	Unlocks.Debug,
	Unlocks.Debug_2,
	Unlocks.Dictionaries,
	Unlocks.Functions,
	Unlocks.Grass,
	Unlocks.Import,
	Unlocks.Lists,
	Unlocks.Loops,
	Unlocks.Operators,
	Unlocks.Senses,
	Unlocks.Simulation,
	Unlocks.Timing,
	Unlocks.Utilities,
	Unlocks.Variables
]


# ============================================================
# RESET STATE
# ============================================================

sim_unlocks = {}


for unlock_type in Unlocks:

	sim_unlocks[
		unlock_type
	] = 0


for unlock_type in RESET_UNLOCKED:

	sim_unlocks[
		unlock_type
	] = 1


sim_items = {}


for item in Items:

	sim_items[
		item
	] = 0


# ============================================================
# HEADER
# ============================================================

quick_print(
	""
)

quick_print(
	"<<< FULL_BENCH_BEGIN >>>"
)

quick_print(
	"FULL AUTOMATION (Fastest Reset from a 1x1 plot)"
)

quick_print(
	"Seeds:",
	len(SEEDS)
)

quick_print(
	""
)


# ============================================================
# RUNS
# ============================================================

best = -1


for seed in SEEDS:

	quick_print(
		"--- seed",
		seed,
		"---"
	)


	run_time = simulate(
		"full_run",
		sim_unlocks,
		sim_items,
		{},
		seed,
		SIM_SPEEDUP
	)


	if run_time == None:

		quick_print(
			"ERROR run seed",
			seed
		)

		continue


	quick_print(
		"seed:",
		seed,
		"time:",
		run_time
	)


	if best < 0 or run_time < best:

		best = run_time


quick_print(
	""
)

quick_print(
	"=== RESULT ==="
)


if best < 0:

	quick_print(
		"No completed runs"
	)

else:

	quick_print(
		"Best simulated seconds:",
		best,
		"(check [FR] DONE vs STOP lines above)"
	)


quick_print(
	"<<< FULL_BENCH_END >>>"
)


print(
	"FULL BENCH DONE\n",
	"Open output.txt"
)
