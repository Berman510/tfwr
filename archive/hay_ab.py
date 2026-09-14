# ============================================================
# HAY STATIC-LAYOUT BENCHMARK
# ============================================================
#
# LAYOUT:
#
#   0 = checkerboard
#       32 source rows
#       1 drone per row
#       16 Grass sources per row
#
#   1 = alternating source rows
#       16 source rows
#       2 drones per row
#       32 Grass sources per row
#
#   2 = one source row every four rows
#       8 source rows
#       4 drones per row
#       32 Grass sources per row
#
#
# RUN:
#
#   False = setup + deploy + synchronize only
#   True  = identical setup, then farm TARGET Hay
#
#
# sim_h2.py subtracts the RUN=False time from RUN=True.
#
# This removes:
#
#   clear
#   companion scanning
#   planning
#   companion planting
#   drone spawning
#   drone positioning
#   synchronization
#
# from the measured achievement time.
# ============================================================


SYNC_DELAY = 5


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
# SCAN ONE ROW
# ============================================================
#
# Record:
#
# (
#     source_x,
#     source_y,
#     companion_entity,
#     target_x,
#     target_y
# )
#
# At this stage EVERYTHING is still Grass.
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


	for x in range(size):

		if get_entity_type() == Entities.Grass:

			companion = get_companion()


			if companion != None:

				pos = companion[1]


				results.append(
					(
						x,
						row,
						companion[0],
						pos[0],
						pos[1]
					)
				)


		if x < size - 1:

			move(
				East
			)


	return results


# ============================================================
# PARALLEL SCAN STRIPE
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
# SCAN ENTIRE 32x32 FIELD
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
# SOURCE TEST
# ============================================================

def is_source(
	layout,
	phase,
	x,
	y
):

	# --------------------------------------------------------
	# CHECKERBOARD
	# --------------------------------------------------------

	if layout == 0:

		return (
			(x + y) % 2
			== phase
		)


	# --------------------------------------------------------
	# EVERY OTHER ROW
	# --------------------------------------------------------

	if layout == 1:

		return (
			y % 2
			== phase
		)


	# --------------------------------------------------------
	# EVERY FOURTH ROW
	# --------------------------------------------------------

	return (
		y % 4
		== phase
	)


# ============================================================
# NUMBER OF PHASE OFFSETS
# ============================================================

def phase_count(
	layout
):

	if layout == 2:

		return 4


	return 2


# ============================================================
# BUILD OPTIMAL STATIC PLAN FOR ONE PHASE
# ============================================================
#
# We group requests by TARGET first.
#
# Then, for every target, we select whichever requested
# companion entity satisfies the largest number of Grass
# sources.
#
# Example:
#
# target (10, 4):
#
#     Bush   -> 3 sources
#     Tree   -> 1 source
#     Carrot -> 2 sources
#
# We plant Bush and boost all 3 Bush-requesting sources.
#
#
# This is better than first-request-wins and costs nothing
# during the achievement window.
# ============================================================

def build_plan(
	records,
	layout,
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
		# NOT A SOURCE IN THIS LAYOUT
		# ----------------------------------------------------

		if not is_source(
			layout,
			phase,
			sx,
			sy
		):

			continue


		# ----------------------------------------------------
		# TARGET WOULD DESTROY ANOTHER SOURCE
		# ----------------------------------------------------

		if is_source(
			layout,
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
			] = []


		entity_groups[
			entity
		].append(
			(
				sx,
				sy
			)
		)


	tasks = []

	accepted = 0


	# --------------------------------------------------------
	# CHOOSE BEST ENTITY PER TARGET
	# --------------------------------------------------------

	for key in groups:

		entity_groups = groups[
			key
		]


		best_entity = None

		best_sources = None

		best_count = 0


		for entity in entity_groups:

			sources = entity_groups[
				entity
			]


			count = len(
				sources
			)


			if count > best_count:

				best_count = count

				best_entity = entity

				best_sources = sources


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
# CHOOSE BEST PHASE
# ============================================================

def choose_plan(
	records,
	layout
):

	best_phase = 0

	best_tasks = []

	best_count = -1


	for phase in range(
		phase_count(
			layout
		)
	):

		result = build_plan(
			records,
			layout,
			phase
		)


		tasks = result[0]

		count = result[1]


		if count > best_count:

			best_phase = phase

			best_tasks = tasks

			best_count = count


	return (
		best_phase,
		best_tasks,
		best_count
	)


# ============================================================
# PLACE ONE COMPANION
# ============================================================

def place_task(
	task
):

	entity = task[0]

	x = task[1]

	y = task[2]


	go_to(
		x,
		y
	)


	if get_entity_type() != None:

		harvest()


	# Carrots require Soil.
	#
	# Bushes and Trees can grow on Grassland.

	if entity == Entities.Carrot:

		if get_ground_type() != Grounds.Soil:

			till()


	plant(
		entity
	)


# ============================================================
# PRIME STATIC LAYOUT
# ============================================================

def prime(
	layout
):

	clear()


	# --------------------------------------------------------
	# READ COMPANION PREFERENCES WHILE THE WHOLE FIELD IS GRASS
	# --------------------------------------------------------

	records = scan_all()


	# --------------------------------------------------------
	# CHOOSE THE BEST PHASE OFFSET
	# --------------------------------------------------------

	choice = choose_plan(
		records,
		layout
	)


	phase = choice[0]

	tasks = choice[1]


	# --------------------------------------------------------
	# PLANT COMPANIONS
	# --------------------------------------------------------
	#
	# Setup duration is outside the achievement window, so
	# doing this serially keeps the setup deterministic.

	for task in tasks:

		place_task(
			task
		)


	return phase


# ============================================================
# BUILD 32 WORKER SPECS
# ============================================================
#
# Spec:
#
# (
#     row,
#     starting_x,
#     movement_step
# )
#
#
# CHECKERBOARD:
#
#     32 rows
#     1 drone each
#     step = 2
#
#
# R2:
#
#     16 rows
#     2 drones each
#     offsets 0 / 16
#     step = 1
#
#
# R4:
#
#     8 rows
#     4 drones each
#     offsets 0 / 8 / 16 / 24
#     step = 1
# ============================================================

def worker_specs(
	layout,
	phase
):

	size = get_world_size()

	specs = []


	# --------------------------------------------------------
	# CHECKERBOARD
	# --------------------------------------------------------

	if layout == 0:

		for row in range(
			size
		):

			start_x = (
				phase - row
			) % 2


			specs.append(
				(
					row,
					start_x,
					2
				)
			)


		return specs


	# --------------------------------------------------------
	# ALTERNATING ROWS
	# --------------------------------------------------------

	if layout == 1:

		for row in range(
			size
		):

			if row % 2 == phase:

				specs.append(
					(
						row,
						0,
						1
					)
				)


				specs.append(
					(
						row,
						size // 2,
						1
					)
				)


		return specs


	# --------------------------------------------------------
	# ONE SOURCE ROW IN FOUR
	# --------------------------------------------------------

	for row in range(
		size
	):

		if row % 4 == phase:

			for offset in range(
				0,
				size,
				size // 4
			):

				specs.append(
					(
						row,
						offset,
						1
					)
				)


	return specs


# ============================================================
# STATIC WORKER
# ============================================================
#
# Every worker reaches its starting coordinate BEFORE the
# common START_AT timestamp.
#
# Therefore all 32 drones begin the timed section together.
# ============================================================

def worker(
	row,
	start_x,
	step,
	start_at,
	target_hay,
	do_run
):

	go_to(
		start_x,
		row
	)


	# --------------------------------------------------------
	# SYNCHRONIZATION BARRIER
	# --------------------------------------------------------

	while get_time() < start_at:

		pass


	# Baseline run ends here.

	if not do_run:

		return


	# --------------------------------------------------------
	# ACHIEVEMENT WINDOW
	# --------------------------------------------------------

	while num_items(
		Items.Hay
	) < target_hay:

		if can_harvest():

			harvest()


		for i in range(
			step
		):

			move(
				East
			)


# ============================================================
# DEPLOY ALL 32 DRONES
# ============================================================

def deploy(
	layout,
	phase,
	start_hay,
	do_run
):

	specs = worker_specs(
		layout,
		phase
	)


	start_at = (
		get_time()
		+ SYNC_DELAY
	)


	target_hay = (
		start_hay
		+ TARGET
	)


	handles = []


	# --------------------------------------------------------
	# CHILD DRONES
	# --------------------------------------------------------

	for index in range(
		1,
		len(specs)
	):

		spec = specs[
			index
		]


		handle = spawn_drone(
			worker,
			spec[0],
			spec[1],
			spec[2],
			start_at,
			target_hay,
			do_run
		)


		if handle != None:

			handles.append(
				handle
			)


	# --------------------------------------------------------
	# COORDINATOR BECOMES WORKER ZERO
	# --------------------------------------------------------

	first = specs[0]


	worker(
		first[0],
		first[1],
		first[2],
		start_at,
		target_hay,
		do_run
	)


	# --------------------------------------------------------
	# JOIN
	# --------------------------------------------------------

	for handle in handles:

		wait_for(
			handle
		)


# ============================================================
# ENTRYPOINT
# ============================================================

phase = prime(
	LAYOUT
)


# Priming can harvest ordinary Grass while replacing target
# squares. Ignore all of that Hay.

start_hay = num_items(
	Items.Hay
)


deploy(
	LAYOUT,
	phase,
	start_hay,
	RUN
)
