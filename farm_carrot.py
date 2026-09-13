import farm_config
import farm_common
import farm_megafarm
import farm_telemetry


# ============================================================
# CONTINUOUS CARROT PHASE
# ============================================================
#
# Production version of carrot_run.py (Carrot Master
# achievement: 200M Carrots in 1 minute).
#
# sim_carrot PAIR SWEEP density 1/4, 32x32 / 32 drones,
# seeds 1-3:
#
#     40.87 sec per +200M Carrots (293.6M/min)
#     vs 244.16 sec for the old farm_carrots + Polyculture
#
# Real game: +251M Carrots in 50.95 sec, unlocked it.
#
#
# Rules (carrot_probe.py, Carrots 10, Polyculture 5):
#
#   - A Carrot costs 512 Hay + 512 Wood; Grass / Bush / Tree
#     are free.
#   - Harvest: 512, or 81,920 (160x) with the exact requested
#     companion type on the exact requested tile. The companion
#     may be young. Wrong type or tile = 512.
#   - The request (Bush / Tree / Grass within 3 tiles) is fixed
#     at planting.
#   - Grow ~5.9 sec plain, ~1.1 sec watered. Fertilizer halves
#     the yield, so it is never used (and is off for Carrots in
#     farm_config.FERTILIZE).
#
#
# Process:
#
#     1. clear(), every tile to bare soil (all drones).
#
#     2. One carrot tile in every DENSITY tiles:
#        (x + STEP * y) % DENSITY == 0. Every other tile is a
#        companion tile. Plant each carrot, replanting until its
#        companion request lands on a companion tile, water it,
#        then plant the requested companion there if missing.
#
#     3. Every drone loops over its rows' carrot tiles: each
#        mature carrot is harvested and re-planted the same way.
#
#     4. Stop when Carrots have grown by carrot_gain_target, or
#        continuous_phase_max_seconds have passed, or Hay / Wood
#        run out.
#
#
# Density 1/4 beat 1/2 (companions overwritten by neighbours)
# and 1/8 (drones walk and wait more).
# ============================================================


WATER_TO = 0.9

MAX_REROLLS = 20

DENSITY = 4

STEP = 2


# ============================================================
# LAYOUT
# ============================================================

def is_carrot_tile(
	x,
	y
):

	return (
		(x + STEP * y) % DENSITY
		== 0
	)


# ============================================================
# PLANT ONE CARROT + ITS COMPANION
# ============================================================

def plant_pair(
	x,
	y
):
	# Drone stands on carrot tile (x, y). Returns False when a
	# carrot can no longer be afforded.

	request = None

	rolls = 0


	while True:

		if get_entity_type() != None:

			harvest()


		if not farm_common.can_afford(
			Entities.Carrot,
			1
		):

			return False


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


	while get_water() < WATER_TO:

		if not use_item(Items.Water):

			break


	if request == None:

		return True


	want = request[0]


	farm_common.go_to(
		request[1][0],
		request[1][1]
	)


	if get_entity_type() != want:

		if get_entity_type() != None:

			harvest()


		plant(want)


	farm_common.go_to(
		x,
		y
	)


	return True


# ============================================================
# SETUP ROWS
# ============================================================

def soil_row(
	row
):

	size = get_world_size()


	farm_common.go_to(
		0,
		row
	)


	for x in range(size):

		if get_entity_type() != None:

			harvest()


		farm_common.make_soil()


		if x < size - 1:

			move(East)


def plant_row(
	row
):

	size = get_world_size()


	for x in range(size):

		if is_carrot_tile(x, row):

			farm_common.go_to(
				x,
				row
			)


			if not plant_pair(x, row):

				return


# ============================================================
# CONTINUOUS HARVEST WORKER
# ============================================================
#
# arg = (target_carrots, deadline). Inventory and get_time()
# are shared by every drone.

def harvest_worker(
	rows,
	arg
):

	target = arg[0]

	deadline = arg[1]


	size = get_world_size()


	while get_time() < deadline:

		for row in rows:

			for x in range(size):

				if not is_carrot_tile(x, row):

					continue


				if (
					num_items(Items.Carrot) >= target
					or
					get_time() >= deadline
				):

					return


				farm_common.go_to(
					x,
					row
				)


				if can_harvest():

					harvest()


					if not plant_pair(x, row):

						return


# ============================================================
# CARROT PHASE
# ============================================================

def farm():

	size = get_world_size()

	carrots = (
		size
		* size
		// DENSITY
	)


	if not farm_common.can_afford(
		Entities.Carrot,
		carrots * 2
	):

		farm_telemetry.add_counter(
			"crop phases skipped for cost",
			1
		)

		return False


	# --------------------------------------------------------
	# SOIL + PLANT
	# --------------------------------------------------------

	start = farm_telemetry.subphase_start(
		"soil / plant pairs"
	)


	farm_common.clear_field()


	farm_megafarm.run_rows(
		soil_row,
		size
	)


	farm_megafarm.run_rows(
		plant_row,
		size
	)


	farm_telemetry.subphase_end(
		"soil / plant pairs",
		start
	)


	# --------------------------------------------------------
	# CONTINUOUS HARVEST
	# --------------------------------------------------------

	gain = farm_config.SETTINGS["carrot_gain_target"]

	start_carrots = num_items(
		Items.Carrot
	)

	deadline = (
		get_time()
		+ farm_config.SETTINGS["continuous_phase_max_seconds"]
	)


	start = farm_telemetry.subphase_start(
		"continuous harvest"
	)


	farm_megafarm.run_stripes_with_arg(
		harvest_worker,
		size,
		(
			start_carrots + gain,
			deadline
		)
	)


	farm_telemetry.subphase_end(
		"continuous harvest",
		start
	)


	gained = (
		num_items(Items.Carrot)
		- start_carrots
	)


	farm_telemetry.add_counter(
		"carrots gained in continuous harvest",
		gained
	)


	if gained < gain:

		farm_telemetry.add_counter(
			"carrot phases stopped by time cap or cost",
			1
		)


	return True
