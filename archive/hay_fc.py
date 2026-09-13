# ============================================================
# HAY FULL-COMPANION BENCHMARK
# ============================================================
#
# MODE:
#
#   0 = SPARSE
#
#       Scan all Grass.
#       Choose best checkerboard phase.
#       Install only companions requested by initial sources.
#
#
#   1 = FULL
#
#       Same optimized initial setup as SPARSE.
#
#       THEN fill every unused non-source checkerboard tile
#       with Bush / Tree / Carrot.
#
#
#   2 = FIXED
#
#       No companion scan or planning.
#
#       Use checkerboard phase 0.
#       Fill every non-source tile with a deterministic
#       Bush / Tree / Carrot pattern.
#
#
# After setup:
#
#   32 drones
#   one drone per row
#   16 Grass sources per row
#
#
# Before measurement:
#
#   run for WARMUP seconds
#
# This intentionally destroys the special advantage of the
# first generation and measures steady-state throughput.
#
#
# RUN:
#
#   False = setup + warmup + synchronization only
#   True  = identical setup + farm TARGET additional Hay
#
#
# sim_fc.py subtracts False from True.
# ============================================================


SYNC_DELAY = 5

QUIET_DELAY = 2

GO_DELAY = 1


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
# CHECKERBOARD SOURCE
# ============================================================

def is_source(
	phase,
	x,
	y
):

	return (
		(x + y) % 2
		== phase
	)


# ============================================================
# SCAN ONE ROW
# ============================================================

def scan_row(
	row
):

	size = get_world_size()

	results = []


	go_to(
		0,
		row
	)


	for x in range(
		size
	):

		if get_entity_type() == Entities.Grass:

			companion = get_companion()


			if companion != None:

				position = companion[1]


				results.append(
					(
						x,
						row,
						companion[0],
						position[0],
						position[1]
					)
				)


		if x < size - 1:

			move(
				East
			)


	return results


# ============================================================
# SCAN STRIPE
# ============================================================

def scan_stripe(
	start,
	count,
	size
):

	results = []

	row = start


	while row < size:

		more = scan_row(
			row
		)


		for record in more:

			results.append(
				record
			)


		row = (
			row + count
		)


	return results


# ============================================================
# PARALLEL FULL-FIELD SCAN
# ============================================================

def scan_all():

	size = get_world_size()

	count = min(
		max_drones(),
		size
	)


	handles = []


	for worker in range(
		1,
		count
	):

		handle = spawn_drone(
			scan_stripe,
			worker,
			count,
			size
		)


		if handle != None:

			handles.append(
				handle
			)


	results = scan_stripe(
		0,
		count,
		size
	)


	for handle in handles:

		more = wait_for(
			handle
		)


		for record in more:

			results.append(
				record
			)


	return results


# ============================================================
# BUILD OPTIMAL INITIAL PLAN
# ============================================================
#
# Groups all requests by target.
#
# If multiple source Grass plants want different companion
# entities on the same target, choose the entity satisfying
# the largest number of sources.
#
#
# Task:
#
# [
#     entity,
#     target_x,
#     target_y
# ]
# ============================================================

def build_plan(
	records,
	phase
):

	groups = {}


	for record in records:

		sx = record[0]

		sy = record[1]

		entity = record[2]

		tx = record[3]

		ty = record[4]


		# ----------------------------------------------------
		# SOURCE MUST BELONG TO THIS CHECKERBOARD
		# ----------------------------------------------------

		if not is_source(
			phase,
			sx,
			sy
		):

			continue


		# ----------------------------------------------------
		# TARGET CANNOT DESTROY ANOTHER SOURCE
		# ----------------------------------------------------

		if is_source(
			phase,
			tx,
			ty
		):

			continue


		key = (
			tx,
			ty
		)


		if key not in groups:

			groups[
				key
			] = {}


		entity_groups = groups[
			key
		]


		if entity not in entity_groups:

			entity_groups[
				entity
			] = 0


		entity_groups[
			entity
		] = (
			entity_groups[
				entity
			]
			+ 1
		)


	tasks = []

	accepted = 0


	# --------------------------------------------------------
	# SELECT WINNING ENTITY FOR EACH TARGET
	# --------------------------------------------------------

	for key in groups:

		entity_groups = groups[
			key
		]


		best_entity = None

		best_count = 0


		for entity in entity_groups:

			count = entity_groups[
				entity
			]


			if count > best_count:

				best_entity = entity

				best_count = count


		if best_entity != None:

			tasks.append(
				(
					best_entity,
					key[0],
					key[1]
				)
			)


			accepted = (
				accepted
				+ best_count
			)


	return (
		tasks,
		accepted
	)


# ============================================================
# CHOOSE BEST CHECKERBOARD PHASE
# ============================================================

def choose_plan(
	records
):

	plan_0 = build_plan(
		records,
		0
	)


	plan_1 = build_plan(
		records,
		1
	)


	if plan_1[1] > plan_0[1]:

		return (
			1,
			plan_1[0]
		)


	return (
		0,
		plan_0[0]
	)


# ============================================================
# PLANT ONE COMPANION
# ============================================================

def plant_companion(
	entity,
	x,
	y
):

	go_to(
		x,
		y
	)


	current = get_entity_type()


	# --------------------------------------------------------
	# ALREADY CORRECT
	# --------------------------------------------------------

	if current == entity:

		return


	# --------------------------------------------------------
	# REMOVE EXISTING GRASS / PLANT
	# --------------------------------------------------------

	if current != None:

		harvest()


	# --------------------------------------------------------
	# CARROT REQUIRES SOIL
	# --------------------------------------------------------

	if entity == Entities.Carrot:

		if get_ground_type() != Grounds.Soil:

			till()


	plant(
		entity
	)


# ============================================================
# INSTALL OPTIMAL TASKS
# ============================================================

def install_tasks(
	tasks
):

	for task in tasks:

		plant_companion(
			task[0],
			task[1],
			task[2]
		)


# ============================================================
# DETERMINISTIC FILL ENTITY
# ============================================================
#
# We don't actually need a particular crop to dominate.
#
# The goal is simply to ensure that every available
# companion-parity coordinate contains one of:
#
#     Bush
#     Tree
#     Carrot
#
# The pattern distributes all three throughout the field.
# ============================================================

def fill_entity(
	x,
	y
):

	value = (
		x
		+ y * 2
	) % 3


	if value == 0:

		return Entities.Bush


	if value == 1:

		return Entities.Tree


	return Entities.Carrot


# ============================================================
# FILL ALL UNUSED COMPANION TILES
# ============================================================
#
# preserve_existing:
#
#   True
#       FULL mode.
#       Keep optimized companions already installed.
#
#   False
#       FIXED mode.
#       Replace every companion tile according to our fixed
#       deterministic pattern.
# ============================================================

def fill_companions(
	phase,
	preserve_existing
):

	size = get_world_size()


	for y in range(
		size
	):

		for x in range(
			size
		):

			if not is_source(
				phase,
				x,
				y
			):

				go_to(
					x,
					y
				)


				current = get_entity_type()


				# --------------------------------------------
				# FULL MODE:
				#
				# Preserve any companion already installed by
				# the optimized initial plan.
				# --------------------------------------------

				if preserve_existing:

					if (
						current == Entities.Bush
						or current == Entities.Tree
						or current == Entities.Carrot
					):

						continue


				entity = fill_entity(
					x,
					y
				)


				# --------------------------------------------
				# REMOVE EXISTING ENTITY
				# --------------------------------------------

				if current != None:

					harvest()


				# --------------------------------------------
				# GROUND
				# --------------------------------------------

				if entity == Entities.Carrot:

					if get_ground_type() != Grounds.Soil:

						till()


				# --------------------------------------------
				# PLANT
				# --------------------------------------------

				plant(
					entity
				)


# ============================================================
# PRIME FARM
# ============================================================

def prime():

	clear()


	# ========================================================
	# FIXED
	# ========================================================
	#
	# No get_companion scan at all.
	#
	# The field is simply divided:
	#
	#     parity 0 = Grass sources
	#     parity 1 = static companions

	if MODE == 2:

		phase = 0


		fill_companions(
			phase,
			False
		)


		return phase


	# ========================================================
	# SPARSE / FULL
	# ========================================================

	records = scan_all()


	choice = choose_plan(
		records
	)


	phase = choice[0]

	tasks = choice[1]


	# --------------------------------------------------------
	# INSTALL FIRST-GENERATION OPTIMAL COMPANIONS
	# --------------------------------------------------------

	install_tasks(
		tasks
	)


	# --------------------------------------------------------
	# FULL:
	#
	# Fill every remaining companion tile.
	# --------------------------------------------------------

	if MODE == 1:

		fill_companions(
			phase,
			True
		)


	return phase


# ============================================================
# FARMING WORKER
# ============================================================
#
# Every drone owns exactly one row.
#
# It only touches one checkerboard parity:
#
#     harvest
#     East
#     East
#
#
# Phases:
#
#     position
#     synchronization
#     warmup
#     quiet barrier
#     baseline sample
#     start barrier
#     measured run
# ============================================================

def worker(
	row,
	phase,
	start_at,
	warm_end,
	sample_at,
	go_at,
	do_run
):

	size = get_world_size()


	start_x = (
		phase - row
	) % 2


	go_to(
		start_x,
		row
	)


	# ========================================================
	# INITIAL SYNCHRONIZATION
	# ========================================================

	while get_time() < start_at:

		pass


	# ========================================================
	# STEADY-STATE WARMUP
	# ========================================================
	#
	# This deliberately harvests/regrows Grass several times.
	#
	# Therefore any initial get_companion optimization has
	# effectively aged out before measurement.

	while get_time() < warm_end:

		if can_harvest():

			harvest()


		move(
			East
		)

		move(
			East
		)


	# ========================================================
	# QUIET PERIOD
	# ========================================================
	#
	# Nobody harvests here.
	#
	# This allows all drones to finish their final warmup
	# operation before anybody snapshots inventory.

	while get_time() < sample_at:

		pass


	# ========================================================
	# COMMON BASELINE
	# ========================================================

	start_hay = num_items(
		Items.Hay
	)


	target_hay = (
		start_hay
		+ TARGET
	)


	# ========================================================
	# FINAL START BARRIER
	# ========================================================
	#
	# Everyone has read the same stable inventory value before
	# anyone resumes harvesting.

	while get_time() < go_at:

		pass


	# Baseline simulation ends at exactly the same point that
	# the measured simulation begins producing Hay.

	if not do_run:

		return


	# ========================================================
	# MEASURED ACHIEVEMENT LOOP
	# ========================================================

	while num_items(
		Items.Hay
	) < target_hay:

		if can_harvest():

			harvest()


		move(
			East
		)

		move(
			East
		)


# ============================================================
# DEPLOY 32 ROW WORKERS
# ============================================================

def deploy(
	phase,
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


	# ========================================================
	# CHILD DRONES
	# ========================================================

	for row in range(
		1,
		size
	):

		handle = spawn_drone(
			worker,
			row,
			phase,
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


	# ========================================================
	# COORDINATOR = ROW ZERO WORKER
	# ========================================================

	worker(
		0,
		phase,
		start_at,
		warm_end,
		sample_at,
		go_at,
		do_run
	)


	# ========================================================
	# JOIN
	# ========================================================

	for handle in handles:

		wait_for(
			handle
		)


# ============================================================
# ENTRYPOINT
# ============================================================

phase = prime()


deploy(
	phase,
	RUN
)