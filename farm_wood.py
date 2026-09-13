import farm_config
import farm_common
import farm_megafarm
import farm_telemetry


# ============================================================
# CONTINUOUS WOOD PHASE
# ============================================================
#
# Production version of wood_run.py (Wood Master achievement:
# 1B Wood in 60 sec).
#
# sim_wood / wood_ab winner, 32x32 / 32 drones, seeds 1-5:
#
#     Tree / Bush checkerboard, pre-watered
#
#     Average:  53.98 sec per 1B Wood
#     Best:     53.14 sec
#     Worst:    54.97 sec
#
#
# Layout:
#
#     T B T B T B ...
#     B T B T B T ...
#
#     Trees never have an orthogonally adjacent Tree. On odd
#     world sizes the last row and column are Bush so that
#     still holds across the world wrap.
#
#
# Process:
#
#     1. clear(), plant the checkerboard, water every tile to
#        PREWATER_LEVEL (one pass, all drones).
#
#     2. Every drone owns a set of rows and loops over them:
#        harvest + replant whatever is ready, then move East.
#
#     3. Stop when Wood has grown by wood_gain_target, or
#        continuous_phase_max_seconds have passed.
#
#
# No fertilizer, no Polyculture, no watering after step 1,
# matching the validated method.
#
# The harvest loop is deliberately lean. Code between moves
# costs game time (see farm_dinosaurs.py).
# ============================================================


PREWATER_LEVEL = 0.99


# ============================================================
# LAYOUT
# ============================================================

def is_tree_tile(
	x,
	y,
	size
):

	if size % 2 == 1:

		if x == size - 1:

			return False


		if y == size - 1:

			return False


	return (
		(x + y) % 2 == 0
	)


# ============================================================
# PREPARE + PRE-WATER ONE ROW
# ============================================================

def prepare_row(
	row
):

	size = get_world_size()


	farm_common.go_to(
		0,
		row
	)


	for x in range(size):

		farm_common.harvest_reset_grass()


		if is_tree_tile(
			x,
			row,
			size
		):

			farm_common.plant_if_affordable(
				Entities.Tree
			)

		else:

			farm_common.plant_if_affordable(
				Entities.Bush
			)


		while get_water() < PREWATER_LEVEL:

			if not farm_common.shared_item_available(
				Items.Water
			):

				break


			if not use_item(
				Items.Water
			):

				break


		if x < size - 1:

			move(
				East
			)


# ============================================================
# CONTINUOUS HARVEST WORKER
# ============================================================
#
# arg = (target_wood, deadline)
#
# Inventory and get_time() are shared by every drone, so all
# workers see the same stop condition.

def harvest_worker(
	rows,
	arg
):

	target = arg[0]

	deadline = arg[1]


	size = get_world_size()

	odd = (
		size % 2 == 1
	)


	while get_time() < deadline:

		for row in rows:

			if get_time() >= deadline:

				return


			farm_common.go_to(
				0,
				row
			)


			# size moves East wraps back to x = 0.

			for x in range(size):

				if num_items(Items.Wood) >= target:

					return


				if can_harvest():

					harvest()


					if (
						(x + row) % 2 == 0
						and
						not (
							odd
							and
							(
								x == size - 1
								or
								row == size - 1
							)
						)
					):

						plant(
							Entities.Tree
						)

					else:

						plant(
							Entities.Bush
						)


				move(
					East
				)


# ============================================================
# WOOD PHASE
# ============================================================

def farm():

	size = get_world_size()

	area = (
		size
		* size
	)


	if not farm_common.can_afford(
		Entities.Tree,
		area // 2
	):

		farm_telemetry.add_counter(
			"crop phases skipped for cost",
			1
		)

		return False


	# --------------------------------------------------------
	# PREPARE + PRE-WATER
	# --------------------------------------------------------

	start = farm_telemetry.subphase_start(
		"prepare / pre-water"
	)


	farm_common.clear_field()


	farm_megafarm.run_rows(
		prepare_row,
		size
	)


	farm_telemetry.subphase_end(
		"prepare / pre-water",
		start
	)


	# --------------------------------------------------------
	# CONTINUOUS HARVEST
	# --------------------------------------------------------

	gain = farm_config.SETTINGS["wood_gain_target"]

	start_wood = num_items(
		Items.Wood
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
			start_wood + gain,
			deadline
		)
	)


	farm_telemetry.subphase_end(
		"continuous harvest",
		start
	)


	gained = (
		num_items(Items.Wood)
		- start_wood
	)


	farm_telemetry.add_counter(
		"wood gained in continuous harvest",
		gained
	)


	if gained < gain:

		farm_telemetry.add_counter(
			"wood phases stopped by time cap",
			1
		)


	return True
