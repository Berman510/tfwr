# ============================================================
# WOOD MASTER LAYOUT BENCHMARK
# ============================================================
#
# MODE:
#
#   0 = BUSH
#       Bush on every tile.
#
#   1 = MIX
#       Tree / Bush checkerboard.
#       Trees have no orthogonal Tree neighbors.
#
#   2 = TREEPOLY
#       Tree sources on checkerboard parity 0.
#       Other parity contains:
#           Grass
#           Bush
#           Carrot
#
#   3 = BUSHPOLY
#       Bush sources on checkerboard parity 0.
#       Other parity contains:
#           Grass
#           Tree
#           Carrot
#
#
# WET:
#
#   False = no watering
#
#   True  = pre-water source ground before warmup.
#           No Water operations occur during measured run.
#
#
# RUN:
#
#   False = setup + warmup + synchronization
#   True  = identical setup + gather TARGET additional Wood
#
#
# sim_wood.py subtracts RUN=False from RUN=True.
# ============================================================


SYNC_DELAY = 5

WARMUP = 15

QUIET_DELAY = 2

GO_DELAY = 1

PHASE = 0


# ============================================================
# MOVEMENT
# ============================================================

def go_to(
	x,
	y
):

	size = get_world_size()


	cx = get_pos_x()


	east = (
		x - cx
	) % size

	west = (
		cx - x
	) % size


	if east <= west:

		for i in range(
			east
		):

			move(
				East
			)

	else:

		for i in range(
			west
		):

			move(
				West
			)


	cy = get_pos_y()


	north = (
		y - cy
	) % size

	south = (
		cy - y
	) % size


	if north <= south:

		for i in range(
			north
		):

			move(
				North
			)

	else:

		for i in range(
			south
		):

			move(
				South
			)


# ============================================================
# POLYCULTURE SOURCE TILE
# ============================================================

def is_poly_source(
	x,
	y
):

	return (
		(x + y) % 2
		== PHASE
	)


# ============================================================
# SOURCE ENTITY
# ============================================================

def source_entity(
	mode,
	x,
	y
):

	# --------------------------------------------------------
	# ALL BUSH
	# --------------------------------------------------------

	if mode == 0:

		return Entities.Bush


	# --------------------------------------------------------
	# TREE / BUSH CHECKERBOARD
	# --------------------------------------------------------

	if mode == 1:

		if (
			(x + y) % 2
			== 0
		):

			return Entities.Tree


		return Entities.Bush


	# --------------------------------------------------------
	# TREE POLY
	# --------------------------------------------------------

	if mode == 2:

		return Entities.Tree


	# --------------------------------------------------------
	# BUSH POLY
	# --------------------------------------------------------

	return Entities.Bush


# ============================================================
# STATIC COMPANION
# ============================================================

def companion_entity(
	mode,
	x,
	y
):

	value = (
		x
		+ y * 2
	) % 3


	# ========================================================
	# TREE SOURCE
	#
	# Valid companions:
	#
	#     Grass
	#     Bush
	#     Carrot
	# ========================================================

	if mode == 2:

		if value == 0:

			return Entities.Grass


		if value == 1:

			return Entities.Bush


		return Entities.Carrot


	# ========================================================
	# BUSH SOURCE
	#
	# Valid companions:
	#
	#     Grass
	#     Tree
	#     Carrot
	# ========================================================

	if value == 0:

		return Entities.Grass


	if value == 1:

		return Entities.Tree


	return Entities.Carrot


# ============================================================
# PREPARE ONE NORMAL PLANT
# ============================================================

def prepare_plant(
	entity
):

	current = get_entity_type()


	if current != None:

		harvest()


	if entity == Entities.Carrot:

		if get_ground_type() != Grounds.Soil:

			till()


	else:

		if get_ground_type() != Grounds.Grassland:

			till()


	plant(
		entity
	)


# ============================================================
# PREPARE GRASS COMPANION
# ============================================================

def prepare_grass():

	current = get_entity_type()


	if current != None:

		if current != Entities.Grass:

			harvest()


	if get_ground_type() != Grounds.Grassland:

		till()


# ============================================================
# PREPARE ROW
# ============================================================

def prepare_row(
	row,
	mode
):

	size = get_world_size()


	go_to(
		0,
		row
	)


	for x in range(
		size
	):

		# ====================================================
		# FULL-PRODUCTION MODES
		# ====================================================

		if mode == 0 or mode == 1:

			prepare_plant(
				source_entity(
					mode,
					x,
					row
				)
			)


		# ====================================================
		# POLYCULTURE MODES
		# ====================================================

		else:

			if is_poly_source(
				x,
				row
			):

				prepare_plant(
					source_entity(
						mode,
						x,
						row
					)
				)


			else:

				entity = companion_entity(
					mode,
					x,
					row
				)


				if entity == Entities.Grass:

					prepare_grass()


				else:

					prepare_plant(
						entity
					)


		if x < size - 1:

			move(
				East
			)


	return 1


# ============================================================
# PREPARE FIELD IN PARALLEL
# ============================================================

def prepare_field(
	mode
):

	clear()


	size = get_world_size()

	handles = []


	for row in range(
		1,
		size
	):

		handle = spawn_drone(
			prepare_row,
			row,
			mode
		)


		if handle != None:

			handles.append(
				handle
			)


	prepare_row(
		0,
		mode
	)


	for handle in handles:

		wait_for(
			handle
		)


# ============================================================
# IS SOURCE TILE
# ============================================================

def is_source(
	mode,
	x,
	y
):

	if mode == 0 or mode == 1:

		return True


	return is_poly_source(
		x,
		y
	)


# ============================================================
# WATER ONE ROW
# ============================================================
#
# Water only productive Wood source tiles.
#
# Water is applied before warmup and never refreshed during
# the measured run.
# ============================================================

def water_row(
	row,
	mode
):

	size = get_world_size()


	go_to(
		0,
		row
	)


	for x in range(
		size
	):

		if is_source(
			mode,
			x,
			row
		):

			# Four tanks from dry is nominally full.
			#
			# Stop when we're essentially at 1.

			while get_water() < 0.99:

				if not use_item(
					Items.Water
				):

					break


		if x < size - 1:

			move(
				East
			)


	return 1


# ============================================================
# PRE-WATER FIELD IN PARALLEL
# ============================================================

def prewater(
	mode
):

	if not WET:

		return


	size = get_world_size()

	handles = []


	for row in range(
		1,
		size
	):

		handle = spawn_drone(
			water_row,
			row,
			mode
		)


		if handle != None:

			handles.append(
				handle
			)


	water_row(
		0,
		mode
	)


	for handle in handles:

		wait_for(
			handle
		)


# ============================================================
# HARVEST + REPLANT
# ============================================================

def cycle_source(
	entity
):

	if can_harvest():

		harvest()


		plant(
			entity
		)


# ============================================================
# ROW WORKER
# ============================================================

def row_worker(
	row,
	mode,
	start_at,
	warm_end,
	sample_at,
	go_at,
	do_run
):

	size = get_world_size()


	# ========================================================
	# FULL FIELD MODES
	# ========================================================

	if mode == 0 or mode == 1:

		start_x = 0

		step = 1


	# ========================================================
	# POLYCULTURE MODES
	# ========================================================

	else:

		start_x = (
			PHASE - row
		) % 2

		step = 2


	go_to(
		start_x,
		row
	)


	# ========================================================
	# INITIAL BARRIER
	# ========================================================

	while get_time() < start_at:

		pass


	# ========================================================
	# WARMUP
	# ========================================================

	while get_time() < warm_end:

		x = get_pos_x()


		cycle_source(
			source_entity(
				mode,
				x,
				row
			)
		)


		for i in range(
			step
		):

			move(
				East
			)


	# ========================================================
	# QUIET BARRIER
	# ========================================================

	while get_time() < sample_at:

		pass


	# ========================================================
	# COMMON WOOD BASELINE
	# ========================================================

	start_wood = num_items(
		Items.Wood
	)


	target_wood = (
		start_wood
		+ TARGET
	)


	# ========================================================
	# FINAL GO BARRIER
	# ========================================================

	while get_time() < go_at:

		pass


	if not do_run:

		return


	# ========================================================
	# MEASURED RUN
	# ========================================================

	while num_items(
		Items.Wood
	) < target_wood:

		x = get_pos_x()


		cycle_source(
			source_entity(
				mode,
				x,
				row
			)
		)


		for i in range(
			step
		):

			move(
				East
			)


# ============================================================
# DEPLOY
# ============================================================

def deploy(
	mode,
	do_run
):

	size = get_world_size()


	start_at = (
		get_time()
		+ SYNC_DELAY
	)


	warm_end = (
		start_at
		+ WARMUP
	)


	sample_at = (
		warm_end
		+ QUIET_DELAY
	)


	go_at = (
		sample_at
		+ GO_DELAY
	)


	handles = []


	for row in range(
		1,
		size
	):

		handle = spawn_drone(
			row_worker,
			row,
			mode,
			start_at,
			warm_end,
			sample_at,
			go_at,
			do_run
		)


		if handle != None:

			handles.append(
				handle
			)


	row_worker(
		0,
		mode,
		start_at,
		warm_end,
		sample_at,
		go_at,
		do_run
	)


	for handle in handles:

		wait_for(
			handle
		)


# ============================================================
# ENTRYPOINT
# ============================================================

prepare_field(
	MODE
)


prewater(
	MODE
)


deploy(
	MODE,
	RUN
)