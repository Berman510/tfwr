# ============================================================
# CARROT MASTER RUNNER
# ============================================================
#
# Achievement (Steam CARROT_MASTER, stat "carrot"):
#
#     "Farm 200 million carrots in 1 minute."
#
#
# Proven simulation (sim_carrot PAIR SWEEP density 1/4, 32x32 /
# 32 drones, real Hay / Wood / Water stock):
#
#     Average:  40.87 sec per +200M Carrots after setup
#     Seeds:    3 / 3 pass (41.02 / 40.45 / 41.14)
#
#
# Rules (carrot_probe.py, Carrots 10, Polyculture 5):
#
#   - A Carrot costs 512 Hay + 512 Wood; companions are free.
#   - Harvest: 512, or 81,920 with the exact requested companion
#     type on the exact requested tile (companion may be young).
#   - The request (Bush / Tree / Grass within 3 tiles) is fixed
#     at planting. Fertilizer halves the yield: never used.
#
#
# Method:
#
#     1. clear(); every tile to bare soil (all drones).
#
#     2. One carrot tile in every 4: (x + 2y) % 4 == 0. Plant
#        each carrot, replanting until its companion request
#        lands on a non-carrot tile, water it, then plant the
#        requested companion on that tile if it isn't there.
#
#     3. All drones synchronise and share one Carrot baseline.
#
#     4. Each drone sweeps its row's carrot tiles: every mature
#        carrot is harvested and re-planted the same way.
#
#     5. Stop when Carrots have grown by TARGET_GAIN, or after
#        MAX_SECONDS.
#
#
# Stop main first so every drone is free.
#
# This file intentionally imports nothing.
# ============================================================


TARGET_GAIN = 250000000

MAX_SECONDS = 120

WATER_TO = 0.9

MAX_REROLLS = 20

DENSITY = 4

STEP = 2

SYNC_DELAY = 4

QUIET_DELAY = 1

GO_DELAY = 1


# ============================================================
# MOVEMENT (normal farm wraps)
# ============================================================

def go_to(
	x,
	y
):

	size = get_world_size()


	while get_pos_x() != x:

		if (x - get_pos_x()) % size <= size // 2:

			move(East)

		else:

			move(West)


	while get_pos_y() != y:

		if (y - get_pos_y()) % size <= size // 2:

			move(North)

		else:

			move(South)


# ============================================================
# TILE HELPERS
# ============================================================

def is_carrot_tile(
	x,
	y
):

	return (
		(x + STEP * y) % DENSITY
		== 0
	)


def water_up():

	while get_water() < WATER_TO:

		if not use_item(Items.Water):

			return


def plant_carrot_pair(
	x,
	y
):
	# Drone stands on carrot tile (x, y). Returns re-roll count.

	rolls = 0

	request = None


	while True:

		if get_entity_type() != None:

			harvest()


		plant(Entities.Carrot)

		request = get_companion()


		if request == None:

			break


		if not is_carrot_tile(request[1][0], request[1][1]):

			break


		if rolls >= MAX_REROLLS:

			request = None

			break


		rolls = rolls + 1


	water_up()


	if request == None:

		return rolls


	want = request[0]


	go_to(
		request[1][0],
		request[1][1]
	)


	if get_entity_type() != want:

		if get_entity_type() != None:

			harvest()


		plant(want)


	go_to(
		x,
		y
	)


	return rolls


def stripe_rows(
	start,
	count,
	size
):

	rows = []

	row = start


	while row < size:

		rows.append(row)

		row = row + count


	return rows


# ============================================================
# SETUP WORKERS
# ============================================================

def soil_worker(
	rows
):

	size = get_world_size()


	for row in rows:

		go_to(0, row)


		for x in range(size):

			if get_entity_type() != None:

				harvest()


			if get_ground_type() != Grounds.Soil:

				till()


			if x < size - 1:

				move(East)


	return 1


def plant_worker(
	rows
):

	size = get_world_size()


	for row in rows:

		for x in range(size):

			if is_carrot_tile(x, row):

				go_to(x, row)

				plant_carrot_pair(x, row)


	return 1


# ============================================================
# RUN WORKER
# ============================================================

def run_worker(
	rows,
	sample_at,
	go_at,
	deadline,
	gain,
	mark_60
):
	# Returns (harvests, re-rolls, start carrots, carrots 60 sec
	# after go or -1, finish time).

	size = get_world_size()


	while get_time() < sample_at:

		pass


	start_carrots = num_items(Items.Carrot)

	target = start_carrots + gain


	while get_time() < go_at:

		pass


	harvests = 0

	rolls = 0

	carrots_60 = -1

	minute = go_at + 60


	while get_time() < deadline:

		for row in rows:

			for x in range(size):

				if not is_carrot_tile(x, row):

					continue


				if mark_60 and carrots_60 < 0 and get_time() >= minute:

					carrots_60 = num_items(Items.Carrot)


				if num_items(Items.Carrot) >= target:

					return (harvests, rolls, start_carrots, carrots_60, get_time())


				go_to(x, row)


				if can_harvest():

					harvest()

					harvests = harvests + 1

					rolls = rolls + plant_carrot_pair(x, row)


	return (harvests, rolls, start_carrots, carrots_60, get_time())


# ============================================================
# MAIN
# ============================================================

quick_print(
	""
)

quick_print(
	"<<< CARROT_RUN_BEGIN >>>"
)


size = get_world_size()

count = min(max_drones(), size)


quick_print(
	"[CARROT] world:",
	size,
	"x",
	size,
	"| drones:",
	count,
	"| target gain:",
	TARGET_GAIN,
	"| carrot cost:",
	get_cost(Entities.Carrot),
	"| hay:",
	num_items(Items.Hay),
	"| wood:",
	num_items(Items.Wood),
	"| water:",
	num_items(Items.Water)
)


clear()


# ------------------------------------------------------------
# SETUP
# ------------------------------------------------------------

setup_start = get_time()


handles = []


for k in range(1, count):

	handle = spawn_drone(
		soil_worker,
		stripe_rows(k, count, size)
	)


	if handle != None:

		handles.append(handle)


soil_worker(
	stripe_rows(0, count, size)
)


for handle in handles:

	wait_for(handle)


handles = []


for k in range(1, count):

	handle = spawn_drone(
		plant_worker,
		stripe_rows(k, count, size)
	)


	if handle != None:

		handles.append(handle)


plant_worker(
	stripe_rows(0, count, size)
)


for handle in handles:

	wait_for(handle)


quick_print(
	"[CARROT] setup seconds:",
	get_time() - setup_start
)


# ------------------------------------------------------------
# SYNCHRONISED RUN
# ------------------------------------------------------------

sample_at = get_time() + SYNC_DELAY

go_at = sample_at + QUIET_DELAY + GO_DELAY

deadline = go_at + MAX_SECONDS


handles = []


for k in range(1, count):

	handle = spawn_drone(
		run_worker,
		stripe_rows(k, count, size),
		sample_at,
		go_at,
		deadline,
		TARGET_GAIN,
		False
	)


	if handle != None:

		handles.append(handle)


quick_print(
	"[CARROT] workers:",
	len(handles) + 1
)


totals = run_worker(
	stripe_rows(0, count, size),
	sample_at,
	go_at,
	deadline,
	TARGET_GAIN,
	True
)


harvests = totals[0]

rolls = totals[1]

start_carrots = totals[2]

carrots_60 = totals[3]

finish = totals[4]


for handle in handles:

	result = wait_for(handle)

	harvests = harvests + result[0]

	rolls = rolls + result[1]


	if result[4] > finish:

		finish = result[4]


gained = num_items(Items.Carrot) - start_carrots

elapsed = finish - go_at


# ============================================================
# RESULT
# ============================================================

quick_print(
	"[CARROT] carrots gained:",
	gained,
	"| seconds:",
	elapsed,
	"| Carrots/min:",
	gained * 60 / elapsed
)

quick_print(
	"[CARROT] harvests:",
	harvests,
	"| re-rolls:",
	rolls,
	"| avg per harvest:",
	gained / max(1, harvests)
)


if carrots_60 >= 0:

	quick_print(
		"[CARROT] carrots gained in first 60 sec:",
		carrots_60 - start_carrots
	)

else:

	quick_print(
		"[CARROT] target reached before 60 sec"
	)


if gained >= 200000000 and elapsed <= 60:

	quick_print(
		"[CARROT] 200M+ Carrots inside 60 sec - check for Carrot Master"
	)

else:

	quick_print(
		"[CARROT] under 200M in 60 sec - check results"
	)


quick_print(
	"<<< CARROT_RUN_END >>>"
)


print(
	"CARROT RUN COMPLETE\n",
	"Gained:",
	gained,
	"in",
	elapsed,
	"sec\n",
	"Open output.txt"
)
