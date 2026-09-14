# ============================================================
# SUNFLOWER HARVEST A/B/C TEST
# ============================================================
#
# MODE:
#
#   0 = setup only
#   1 = current ordering
#   2 = serpentine spatial ordering
#   3 = spatial + nearest-neighbor route
#
#
# Target:
#
#   sun_ab.py
#
# ============================================================


SEEDS = [
	1,
	2,
	3,
	4,
	5
]


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
# CURRENT INVENTORY
# ============================================================
#
# Unlike the cactus algorithm benchmark, keep the real current
# inventory.
#
# Power is automatically consumed by normal operation, so this
# gives us more representative sunflower timings.

sim_items = {}


for item in Items:

	sim_items[
		item
	] = num_items(
		item
	)


# ============================================================
# TOTALS
# ============================================================

setup_sum = 0

cur_sum = 0
snake_sum = 0
route_sum = 0

cur_wins = 0
snake_wins = 0
route_wins = 0
ties = 0

runs = 0

failed = False


# ============================================================
# HEADER
# ============================================================

quick_print(
	""
)

quick_print(
	"<<< SUN_AB_BEGIN >>>"
)

quick_print(
	"SUNFLOWER HARVEST TEST"
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
	"Seeds:",
	len(SEEDS)
)

quick_print(
	""
)


# ============================================================
# RUN SEEDS
# ============================================================

for seed in SEEDS:

	if failed:

		break


	quick_print(
		"--- SEED",
		seed,
		"---"
	)


	# --------------------------------------------------------
	# SETUP
	# --------------------------------------------------------

	setup = simulate(
		"sun_ab",
		sim_unlocks,
		sim_items,
		{
			"MODE": 0
		},
		seed,
		SIM_SPEEDUP
	)


	if setup == None:

		quick_print(
			"ERROR setup",
			seed
		)

		failed = True

		break


	# --------------------------------------------------------
	# CURRENT
	# --------------------------------------------------------

	cur_total = simulate(
		"sun_ab",
		sim_unlocks,
		sim_items,
		{
			"MODE": 1
		},
		seed,
		SIM_SPEEDUP
	)


	if cur_total == None:

		quick_print(
			"ERROR current",
			seed
		)

		failed = True

		break


	# --------------------------------------------------------
	# SNAKE
	# --------------------------------------------------------

	snake_total = simulate(
		"sun_ab",
		sim_unlocks,
		sim_items,
		{
			"MODE": 2
		},
		seed,
		SIM_SPEEDUP
	)


	if snake_total == None:

		quick_print(
			"ERROR snake",
			seed
		)

		failed = True

		break


	# --------------------------------------------------------
	# ROUTE
	# --------------------------------------------------------

	route_total = simulate(
		"sun_ab",
		sim_unlocks,
		sim_items,
		{
			"MODE": 3
		},
		seed,
		SIM_SPEEDUP
	)


	if route_total == None:

		quick_print(
			"ERROR route",
			seed
		)

		failed = True

		break


	# ========================================================
	# REMOVE IDENTICAL FIELD SETUP COST
	# ========================================================
	#
	# These values contain:
	#
	#     scan
	#     +
	#     planning
	#     +
	#     sunflower harvest
	#
	# which is exactly what we're trying to optimize.

	cur = (
		cur_total
		- setup
	)

	snake = (
		snake_total
		- setup
	)

	route = (
		route_total
		- setup
	)


	if cur < 0:

		cur = 0


	if snake < 0:

		snake = 0


	if route < 0:

		route = 0


	# ========================================================
	# WINNER
	# ========================================================

	best = cur

	winner = "CURRENT"


	if snake < best:

		best = snake

		winner = "SNAKE"


	elif snake == best:

		winner = "TIE"


	if route < best:

		best = route

		winner = "ROUTE"


	elif route == best:

		winner = "TIE"


	if winner == "CURRENT":

		cur_wins = (
			cur_wins + 1
		)


	elif winner == "SNAKE":

		snake_wins = (
			snake_wins + 1
		)


	elif winner == "ROUTE":

		route_wins = (
			route_wins + 1
		)


	else:

		ties = (
			ties + 1
		)


	# ========================================================
	# TOTALS
	# ========================================================

	runs = (
		runs + 1
	)


	setup_sum = (
		setup_sum
		+ setup
	)


	cur_sum = (
		cur_sum
		+ cur
	)


	snake_sum = (
		snake_sum
		+ snake
	)


	route_sum = (
		route_sum
		+ route
	)


	# ========================================================
	# OUTPUT
	# ========================================================

	quick_print(
		"setup:",
		setup,
		"current:",
		cur,
		"snake:",
		snake,
		"route:",
		route,
		"winner:",
		winner
	)


# ============================================================
# FINAL RESULT
# ============================================================

if not failed:

	avg_setup = (
		setup_sum
		/ runs
	)

	avg_cur = (
		cur_sum
		/ runs
	)

	avg_snake = (
		snake_sum
		/ runs
	)

	avg_route = (
		route_sum
		/ runs
	)


	quick_print(
		""
	)

	quick_print(
		"=== AVERAGES ==="
	)

	quick_print(
		"Setup:",
		avg_setup
	)

	quick_print(
		"Current:",
		avg_cur
	)

	quick_print(
		"Snake:",
		avg_snake
	)

	quick_print(
		"Route:",
		avg_route
	)


	# ========================================================
	# OVERALL WINNER
	# ========================================================

	best = avg_cur

	winner = "CURRENT"


	if avg_snake < best:

		best = avg_snake

		winner = "SNAKE"


	if avg_route < best:

		best = avg_route

		winner = "ROUTE"


	quick_print(
		""
	)

	quick_print(
		"=== RESULT ==="
	)

	quick_print(
		"WINNER:",
		winner
	)


	quick_print(
		"Seed wins:",
		"Current:",
		cur_wins,
		"Snake:",
		snake_wins,
		"Route:",
		route_wins,
		"Ties:",
		ties
	)


	saved = (
		avg_cur
		- best
	)


	improvement = (
		saved
		* 100
		/ avg_cur
	)


	quick_print(
		"Best vs current saves:",
		saved,
		"seconds"
	)

	quick_print(
		"Improvement:",
		improvement,
		"%"
	)


	# ========================================================
	# ROUTE VS SIMPLE SNAKE
	# ========================================================

	route_delta = (
		avg_snake
		- avg_route
	)


	quick_print(
		"Route vs Snake delta:",
		route_delta,
		"seconds"
	)


else:

	quick_print(
		"BENCHMARK ABORTED"
	)


quick_print(
	"<<< SUN_AB_END >>>"
)


print(
	"SUN TEST DONE\n",
	"Open output.txt"
)
