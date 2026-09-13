import farm_config
import farm_common
import farm_megafarm
import farm_telemetry


# ============================================================
# CONTINUOUS HAY PHASE
# ============================================================
#
# Production version of hay_run.py (200M Hay in 60 sec).
#
# sim_fc / hay_fc winner, 32x32 / 32 drones:
#
#     FIXED companion checkerboard
#
#     Average:     ~33.36 sec per 200M Hay
#     Worst seed:  ~33.71 sec
#
#
# Layout:
#
#     G C G C G C ...
#     C G C G C G ...
#
#     G = Grass source (SOURCE_PARITY)
#     C = static Bush / Tree / Carrot, spread evenly by
#         (x + 2y) % 3, with affordable fallbacks
#
#     Trees never touch each other because every companion
#     shares one checkerboard parity.
#
#
# Process:
#
#     1. clear() (fresh Grass everywhere), then plant a
#        companion on every non-source tile.
#
#     2. Every drone owns a set of rows and loops over them,
#        harvesting each ready Grass source and moving two
#        tiles East between sources.
#
#     3. Stop when Hay has grown by hay_gain_target, or
#        continuous_phase_max_seconds have passed.
#
#
# No water, no fertilizer, no get_companion(), no dynamic
# planning, matching the validated method.
# ============================================================


SOURCE_PARITY = 0


COMPANIONS = [
	Entities.Bush,
	Entities.Tree,
	Entities.Carrot
]


# ============================================================
# LAYOUT
# ============================================================

def is_source(
	x,
	y
):

	return (
		(x + y) % 2
		== SOURCE_PARITY
	)


def preferred_companion(
	x,
	y
):

	return COMPANIONS[
		(x + y * 2) % 3
	]


def choose_companion(
	x,
	y
):
	# Preferred crop first, then the other two in COMPANIONS
	# order. Same fallbacks as hay_run.py.

	preferred = preferred_companion(
		x,
		y
	)


	if farm_common.can_afford(
		preferred,
		1
	):

		return preferred


	for entity in COMPANIONS:

		if entity == preferred:

			continue


		if farm_common.can_afford(
			entity,
			1
		):

			return entity


	return None


# ============================================================
# PREPARE ONE ROW
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

		if not is_source(
			x,
			row
		):

			entity = choose_companion(
				x,
				row
			)


			if entity != None:

				if get_entity_type() != None:

					harvest()


				if entity == Entities.Carrot:

					farm_common.make_soil()


				plant(
					entity
				)


		if x < size - 1:

			move(
				East
			)


# ============================================================
# CONTINUOUS HARVEST WORKER
# ============================================================
#
# arg = (target_hay, deadline)

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


			start_x = (
				(SOURCE_PARITY - row)
				% 2
			)


			farm_common.go_to(
				start_x,
				row
			)


			sources = (
				(size - start_x + 1)
				// 2
			)


			for i in range(sources):

				if num_items(Items.Hay) >= target:

					return


				if can_harvest():

					harvest()


				move(
					East
				)

				move(
					East
				)


# ============================================================
# HAY PHASE
# ============================================================

def farm():

	size = get_world_size()


	# --------------------------------------------------------
	# PREPARE
	# --------------------------------------------------------

	start = farm_telemetry.subphase_start(
		"prepare companions"
	)


	farm_common.clear_field()


	farm_megafarm.run_rows(
		prepare_row,
		size
	)


	farm_telemetry.subphase_end(
		"prepare companions",
		start
	)


	# --------------------------------------------------------
	# CONTINUOUS HARVEST
	# --------------------------------------------------------

	gain = farm_config.SETTINGS["hay_gain_target"]

	start_hay = num_items(
		Items.Hay
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
			start_hay + gain,
			deadline
		)
	)


	farm_telemetry.subphase_end(
		"continuous harvest",
		start
	)


	gained = (
		num_items(Items.Hay)
		- start_hay
	)


	farm_telemetry.add_counter(
		"hay gained in continuous harvest",
		gained
	)


	if gained < gain:

		farm_telemetry.add_counter(
			"hay phases stopped by time cap",
			1
		)


	return True
