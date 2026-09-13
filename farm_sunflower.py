import farm_config
import farm_common
import farm_megafarm
import farm_telemetry


# ============================================================
# CONTINUOUS SUNFLOWER PHASE
# ============================================================
#
# Production version of sunflower_run.py (Sunflower Master
# achievement: 12,000 Power in 1 minute).
#
# sim_sunflower MATURE 15, 32x32 / 32 drones, seeds 1-3:
#
#     25.97 sec per +12,000 Power (27,726 Power/min)
#     vs 86.07 sec for the old whole-field sweep
#
# Real game: +15,006 Power in 32.63 sec, unlocked it.
#
#
# Rules (sunflower_probe.py):
#
#   - Petals (7-15) are fixed at planting.
#   - A harvest pays ~1 Power, or 8 Power when the flower has
#     the max petals on the field and >= 10 sunflowers are on
#     it (young ones count). Ties all pay 8.
#   - Grow: ~6.8 sec plain, ~1.3 sec watered.
#
#
# Process:
#
#     1. clear(), plant every tile with a Sunflower on soil,
#        and water to WATER_TO (one pass, all drones).
#
#     2. Every drone loops over its rows: harvest any mature
#        flower, replant once, water, move East. About 1 in 9
#        new flowers has 15 petals and pays the bonus; the
#        rest pay ~1 each, and nothing is spent re-rolling.
#
#     3. Stop when Power has grown by sunflower_gain_target,
#        or continuous_phase_max_seconds have passed.
#
#
# Power is read from inventory, which under-counts harvested
# Power a little: drones spend Power to move and act faster.
#
# The harvest loop is deliberately lean (see farm_dinosaurs).
# ============================================================


WATER_TO = 0.9


# ============================================================
# PREPARE + WATER ONE ROW
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

		if get_entity_type() != None:

			harvest()


		farm_common.make_soil()


		farm_common.plant_if_affordable(
			Entities.Sunflower
		)


		while get_water() < WATER_TO:

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
# arg = (target_power, deadline). Inventory and get_time() are
# shared by every drone.

def harvest_worker(
	rows,
	arg
):

	target = arg[0]

	deadline = arg[1]


	size = get_world_size()


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

				if num_items(Items.Power) >= target:

					return


				if can_harvest():

					harvest()

					plant(
						Entities.Sunflower
					)


					while get_water() < WATER_TO:

						if not use_item(
							Items.Water
						):

							break


				move(
					East
				)


# ============================================================
# SUNFLOWER PHASE
# ============================================================

def farm():

	size = get_world_size()

	area = (
		size
		* size
	)


	if not farm_common.can_afford(
		Entities.Sunflower,
		area
	):

		farm_telemetry.add_counter(
			"crop phases skipped for cost",
			1
		)

		return False


	# --------------------------------------------------------
	# PLANT + WATER
	# --------------------------------------------------------

	start = farm_telemetry.subphase_start(
		"plant / water"
	)


	farm_common.clear_field()


	farm_megafarm.run_rows(
		prepare_row,
		size
	)


	farm_telemetry.subphase_end(
		"plant / water",
		start
	)


	# --------------------------------------------------------
	# CONTINUOUS HARVEST
	# --------------------------------------------------------

	gain = farm_config.SETTINGS["sunflower_gain_target"]

	start_power = num_items(
		Items.Power
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
			start_power + gain,
			deadline
		)
	)


	farm_telemetry.subphase_end(
		"continuous harvest",
		start
	)


	gained = (
		num_items(Items.Power)
		- start_power
	)


	farm_telemetry.add_counter(
		"power gained in continuous harvest",
		gained
	)


	if gained < gain:

		farm_telemetry.add_counter(
			"sunflower phases stopped by time cap",
			1
		)


	return True
