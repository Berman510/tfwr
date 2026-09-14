# ============================================================
# HAY BOOSTED-ONLY A/B/C
# ============================================================
#
# MODE:
#
#   1 = ALL
#       Current warm checkerboard winner.
#
#   2 = BOOST
#       Harvest only successfully boosted Grass sources.
#       Skip immature plants.
#
#   3 = WAIT
#       Harvest only successfully boosted sources and wait
#       locally for maturity.
#
#
# Every strategy is measured after:
#
#   companion scanning
#   phase selection
#   companion planting
#   drone spawning
#   worker positioning
#   synchronization
#
# ============================================================


TARGET = 200000000


SEEDS = [
	1,
	2,
	3,
	4,
	5
]


MODES = [
	1,
	2,
	3
]


NAMES = {
	1: "ALL",
	2: "BOOST",
	3: "WAIT"
}


SIM_SPEEDUP = 10000


# ============================================================
# CURRENT UNLOCK STATE
# ============================================================

sim_unlocks = {}


for unlock_type in Unlocks:

	sim_unlocks[
		unlock_type
	] = num_unlocked(
		unlock_type
	)


# ============================================================
# LARGE TEST INVENTORY
# ============================================================

sim_items = {}


for item in Items:

	sim_items[
		item
	] = 1000000000


# ============================================================
# HEADER
# ============================================================

quick_print(
	""
)

quick_print(
	"<<< HAY_BO_BEGIN >>>"
)

quick_print(
	"HAY BOOSTED-ONLY TEST"
)

quick_print(
	"Target:",
	TARGET
)

quick_print(
	"Goal:",
	60,
	"seconds"
)

quick_print(
	"World:",
	get_world_size(),
	"x",
	get_world_size()
)

quick_print(
	"Drones:",
	max_drones()
)

quick_print(
	"Polyculture:",
	num_unlocked(
		Unlocks.Polyculture
	)
)

quick_print(
	""
)


# ============================================================
# GLOBAL BEST
# ============================================================

best_avg = -1

best_mode = -1


# ============================================================
# TEST MODES
# ============================================================

for mode in MODES:

	name = NAMES[
		mode
	]


	total = 0

	min_time = -1

	max_time = 0

	pass_count = 0

	completed = 0


	quick_print(
		"---",
		name,
		"---"
	)


	for seed in SEEDS:

		# ----------------------------------------------------
		# MATCHING WARM BASELINE
		# ----------------------------------------------------

		base = simulate(
			"hay_bo",
			sim_unlocks,
			sim_items,
			{
				"TARGET": TARGET,
				"MODE": mode,
				"RUN": False
			},
			seed,
			SIM_SPEEDUP
		)


		if base == None:

			quick_print(
				"ERROR baseline",
				name,
				seed
			)

			continue


		# ----------------------------------------------------
		# MATCHING ACHIEVEMENT RUN
		# ----------------------------------------------------

		full = simulate(
			"hay_bo",
			sim_unlocks,
			sim_items,
			{
				"TARGET": TARGET,
				"MODE": mode,
				"RUN": True
			},
			seed,
			SIM_SPEEDUP
		)


		if full == None:

			quick_print(
				"ERROR run",
				name,
				seed
			)

			continue


		# ----------------------------------------------------
		# PURE WARM FARMING WINDOW
		# ----------------------------------------------------

		run_time = (
			full - base
		)


		completed = (
			completed + 1
		)


		total = (
			total + run_time
		)


		if min_time < 0:

			min_time = run_time


		elif run_time < min_time:

			min_time = run_time


		if run_time > max_time:

			max_time = run_time


		if run_time <= 60:

			pass_count = (
				pass_count + 1
			)


		quick_print(
			"seed:",
			seed,
			"time:",
			run_time,
			"pass:",
			(
				run_time <= 60
			)
		)


	# ========================================================
	# AVERAGE
	# ========================================================

	if completed > 0:

		avg = (
			total
			/ completed
		)


		hay_per_minute = (
			TARGET
			* 60
			/ avg
		)


		margin = (
			60 - avg
		)


		quick_print(
			"AVG:",
			avg
		)

		quick_print(
			"MIN:",
			min_time
		)

		quick_print(
			"MAX:",
			max_time
		)

		quick_print(
			"Hay/min:",
			hay_per_minute
		)

		quick_print(
			"60s margin:",
			margin
		)

		quick_print(
			"Passing seeds:",
			pass_count,
			"/",
			completed
		)


		if best_avg < 0:

			best_avg = avg

			best_mode = mode


		elif avg < best_avg:

			best_avg = avg

			best_mode = mode


	quick_print(
		""
	)


# ============================================================
# FINAL RESULT
# ============================================================

quick_print(
	"=== RESULT ==="
)


if best_mode >= 0:

	quick_print(
		"WINNER:",
		NAMES[
			best_mode
		]
	)

	quick_print(
		"Average:",
		best_avg
	)

	quick_print(
		"Hay/min:",
		(
			TARGET
			* 60
			/ best_avg
		)
	)

	quick_print(
		"60s margin:",
		(
			60 - best_avg
		)
	)


	if best_avg <= 60:

		quick_print(
			"HAY MASTER:",
			"PASS CAPABLE"
		)


	else:

		quick_print(
			"HAY MASTER:",
			"MORE WORK NEEDED"
		)


quick_print(
	"<<< HAY_BO_END >>>"
)


print(
	"HAY BOOST TEST DONE\n",
	"Open output.txt"
)
