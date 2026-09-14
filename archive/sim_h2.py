# ============================================================
# HAY STATIC-LAYOUT A/B/C
# ============================================================
#
# Compare achievement-window throughput from an already:
#
#     primed
#     deployed
#     positioned
#     synchronized
#
# 32-drone farm.
#
#
# LAYOUT:
#
#   0 = checkerboard
#   1 = alternating Grass rows
#   2 = one Grass row every four rows
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


LAYOUTS = [
	0,
	1,
	2
]


NAMES = {
	0: "CHECKER",
	1: "ROWS2",
	2: "ROWS4"
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
#
# We want algorithmic throughput.
#
# The real achievement attempt can be preceded by stockpiling
# Power and companion-plant resources.

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
	"<<< HAY2_BEGIN >>>"
)

quick_print(
	"HAY WARM STATIC TEST"
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
	""
)


# ============================================================
# GLOBAL WINNER
# ============================================================

best_avg = -1

best_layout = -1


# ============================================================
# LAYOUTS
# ============================================================

for layout in LAYOUTS:

	name = NAMES[
		layout
	]


	total = 0

	min_time = -1

	max_time = 0

	wins = 0


	quick_print(
		"---",
		name,
		"---"
	)


	for seed in SEEDS:

		# ----------------------------------------------------
		# IDENTICAL SETUP / DEPLOY BASELINE
		# ----------------------------------------------------

		base = simulate(
			"hay_ab",
			sim_unlocks,
			sim_items,
			{
				"TARGET": TARGET,
				"LAYOUT": layout,
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
		# SETUP + ACHIEVEMENT RUN
		# ----------------------------------------------------

		full = simulate(
			"hay_ab",
			sim_unlocks,
			sim_items,
			{
				"TARGET": TARGET,
				"LAYOUT": layout,
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
		# PURE WARM THROUGHPUT TIME
		# ----------------------------------------------------

		run_time = (
			full
			- base
		)


		total = (
			total
			+ run_time
		)


		if min_time < 0:

			min_time = run_time


		elif run_time < min_time:

			min_time = run_time


		if run_time > max_time:

			max_time = run_time


		if run_time <= 60:

			wins = (
				wins + 1
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

	avg = (
		total
		/ len(SEEDS)
	)


	rate = (
		TARGET
		* 60
		/ avg
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
		rate
	)

	quick_print(
		"60s margin:",
		(
			60 - avg
		)
	)

	quick_print(
		"Passing seeds:",
		wins,
		"/",
		len(SEEDS)
	)


	if best_avg < 0:

		best_avg = avg

		best_layout = layout


	elif avg < best_avg:

		best_avg = avg

		best_layout = layout


	quick_print(
		""
	)


# ============================================================
# RESULT
# ============================================================

quick_print(
	"=== RESULT ==="
)

quick_print(
	"WINNER:",
	NAMES[
		best_layout
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
	"<<< HAY2_END >>>"
)


print(
	"HAY2 DONE\n",
	"Open output.txt"
)
