# ============================================================
# HAY BOOSTED-ONLY BENCHMARK TARGET
# ============================================================
#
# MODE:
#
#   1 = ALL
#
#       Current winning checkerboard strategy.
#
#       One drone per row.
#       Visit every Grass source on the checkerboard.
#
#
#   2 = BOOST
#
#       Visit ONLY sources with a successfully-placed
#       Polyculture companion.
#
#       Immature boosted sources are skipped and checked
#       again on the next circuit.
#
#
#   3 = WAIT
#
#       Visit ONLY successfully boosted sources.
#
#       When a source is immature, stay there until it becomes
#       harvestable before moving to the next boosted source.
#
#
# RUN:
#
#   False = fully prime, deploy, position and synchronize
#
#   True  = identical setup + farm TARGET Hay
#
#
# sim_bo.py subtracts RUN=False from RUN=True.
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
#
# Scan happens while the ENTIRE field is still Grass.
#
# Record:
#
# (
#     source_x,
#     source_y,
#     requested_entity,
#     target_x,
#     target_y
# )
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
# SCAN FULL FIELD
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
# BUILD PLAN FOR ONE CHECKERBOARD PHASE
# ============================================================
#
# Requests are grouped by target.
#
# If multiple source plants request different companion
# entities on the same target, choose whichever entity boosts
# the largest number of sources.
#
#
# Task:
#
# [
#     entity,
#     target_x,
#     target_y,
#     [
#         (source_x, source_y),
#         ...
#     ]
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
		# SOURCE MUST BELONG TO THIS PHASE
		# ----------------------------------------------------

		if not is_source(
			phase,
			sx,
			sy
		):

			continue


		# ----------------------------------------------------
		# NEVER DESTROY ANOTHER SOURCE
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
	# BEST ENTITY PER TARGET
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

				best_entity = entity

				best_sources = sources

				best_count = count


		if best_entity != None:

			tasks.append(
				[
					best_entity,
					key[0],
					key[1],
					best_sources
				]
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
# CHOOSE BETTER CHECKERBOARD PHASE
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
# PLACE ONE COMPANION TASK
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


	current = get_entity_type()


	# --------------------------------------------------------
	# ALREADY CORRECT
	# --------------------------------------------------------

	if current == entity:

		return True


	# --------------------------------------------------------
	# REMOVE CURRENT TARGET CROP
	# --------------------------------------------------------

	if current != None:

		harvest()


	# --------------------------------------------------------
	# CARROT NEEDS SOIL
	# --------------------------------------------------------

	if entity == Entities.Carrot:

		if get_ground_type() != Grounds.Soil:

			till()


	# --------------------------------------------------------
	# PLANT
	# --------------------------------------------------------

	plant(
		entity
	)


	return (
		get_entity_type()
		== entity
	)


# ============================================================
# SORT X COORDINATES
# ============================================================

def sort_xs(
	values
):

	for i in range(
		1,
		len(values)
	):

		current = values[i]

		j = (
			i - 1
		)


		while j >= 0:

			if values[j] <= current:

				break


			values[
				j + 1
			] = values[j]


			j = (
				j - 1
			)


		values[
			j + 1
		] = current


# ============================================================
# PRIME FARM
# ============================================================
#
# Returns:
#
# (
#     phase,
#     boosted_rows
# )
#
#
# boosted_rows[y] contains the x coordinates of Grass sources
# whose exact companion was successfully installed.
# ============================================================

def prime():

	clear()


	size = get_world_size()


	# --------------------------------------------------------
	# SCAN WHILE ALL 1024 TILES ARE GRASS
	# --------------------------------------------------------

	records = scan_all()


	# --------------------------------------------------------
	# CHOOSE BEST CHECKERBOARD PHASE
	# --------------------------------------------------------

	choice = choose_plan(
		records
	)


	phase = choice[0]

	tasks = choice[1]


	# --------------------------------------------------------
	# EXACT SUCCESSFUL BOOST MAP
	# --------------------------------------------------------

	boosted_rows = []


	for y in range(size):

		boosted_rows.append(
			[]
		)


	# --------------------------------------------------------
	# INSTALL COMPANIONS
	# --------------------------------------------------------
	#
	# Serial is intentional.
	#
	# This is outside the measured achievement window and makes
	# the resulting boosted-source map deterministic.

	for task in tasks:

		success = place_task(
			task
		)


		if success:

			for source in task[3]:

				boosted_rows[
					source[1]
				].append(
					source[0]
				)


	# --------------------------------------------------------
	# SORT SOURCE X COORDINATES
	# --------------------------------------------------------

	for row in boosted_rows:

		sort_xs(
			row
		)


	return (
		phase,
		boosted_rows
	)


# ============================================================
# IDLE UNTIL TARGET REACHED
# ============================================================

def idle_worker(
	target_hay
):

	while num_items(
		Items.Hay
	) < target_hay:

		pass


# ============================================================
# CURRENT ALL-SOURCE WORKER
# ============================================================

def all_worker(
	row,
	phase,
	start_at,
	target_hay,
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


	# --------------------------------------------------------
	# COMMON START BARRIER
	# --------------------------------------------------------

	while get_time() < start_at:

		pass


	if not do_run:

		return


	# --------------------------------------------------------
	# 16 CHECKERBOARD SOURCES
	# --------------------------------------------------------

	while num_items(
		Items.Hay
	) < target_hay:

		for index in range(
			size // 2
		):

			if can_harvest():

				harvest()


			move(
				East
			)

			move(
				East
			)


# ============================================================
# BOOSTED-ONLY WORKER
# ============================================================
#
# This worker visits only sources known to have a successfully
# installed companion.
#
# It still travels East around the toroidal row, but does not
# spend harvest operations on unboosted Grass.
# ============================================================

def boost_worker(
	row,
	xs,
	start_at,
	target_hay,
	do_run,
	wait_mode
):

	size = get_world_size()


	# --------------------------------------------------------
	# NOTHING BOOSTED IN THIS ROW
	# --------------------------------------------------------

	if len(xs) == 0:

		go_to(
			0,
			row
		)


		while get_time() < start_at:

			pass


		if do_run:

			idle_worker(
				target_hay
			)


		return


	# --------------------------------------------------------
	# START ON FIRST BOOSTED SOURCE
	# --------------------------------------------------------

	index = 0

	current_x = xs[0]


	go_to(
		current_x,
		row
	)


	# --------------------------------------------------------
	# COMMON START BARRIER
	# --------------------------------------------------------

	while get_time() < start_at:

		pass


	if not do_run:

		return


	# --------------------------------------------------------
	# ACHIEVEMENT LOOP
	# --------------------------------------------------------

	while num_items(
		Items.Hay
	) < target_hay:

		# ----------------------------------------------------
		# WAIT MODE
		# ----------------------------------------------------

		if wait_mode:

			while not can_harvest():

				if num_items(
					Items.Hay
				) >= target_hay:

					return


			harvest()


		# ----------------------------------------------------
		# SKIP MODE
		# ----------------------------------------------------

		else:

			if can_harvest():

				harvest()


		# ----------------------------------------------------
		# NEXT BOOSTED SOURCE
		# ----------------------------------------------------

		next_index = (
			index + 1
		)


		if next_index >= len(xs):

			next_index = 0


		next_x = xs[
			next_index
		]


		distance = (
			next_x - current_x
		) % size


		# ----------------------------------------------------
		# SINGLE BOOSTED SOURCE SPECIAL CASE
		# ----------------------------------------------------
		#
		# If there is only one source in this row, don't take a
		# pointless full lap around the world.
		#
		# Re-check the same source in place.

		if len(xs) > 1:

			for move_index in range(
				distance
			):

				move(
					East
				)


		current_x = next_x

		index = next_index


# ============================================================
# DEPLOY ALL 32 ROW WORKERS
# ============================================================

def deploy(
	mode,
	phase,
	boosted_rows,
	start_hay,
	do_run
):

	size = get_world_size()


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
	# CHILD ROWS
	# --------------------------------------------------------

	for row in range(
		1,
		size
	):

		if mode == 1:

			handle = spawn_drone(
				all_worker,
				row,
				phase,
				start_at,
				target_hay,
				do_run
			)


		elif mode == 2:

			handle = spawn_drone(
				boost_worker,
				row,
				boosted_rows[row],
				start_at,
				target_hay,
				do_run,
				False
			)


		else:

			handle = spawn_drone(
				boost_worker,
				row,
				boosted_rows[row],
				start_at,
				target_hay,
				do_run,
				True
			)


		if handle != None:

			handles.append(
				handle
			)


	# --------------------------------------------------------
	# COORDINATOR OWNS ROW ZERO
	# --------------------------------------------------------

	if mode == 1:

		all_worker(
			0,
			phase,
			start_at,
			target_hay,
			do_run
		)


	elif mode == 2:

		boost_worker(
			0,
			boosted_rows[0],
			start_at,
			target_hay,
			do_run,
			False
		)


	else:

		boost_worker(
			0,
			boosted_rows[0],
			start_at,
			target_hay,
			do_run,
			True
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

prime_result = prime()


phase = prime_result[0]

boosted_rows = prime_result[1]


# Ignore all Hay harvested while preparing companion targets.

start_hay = num_items(
	Items.Hay
)


deploy(
	MODE,
	phase,
	boosted_rows,
	start_hay,
	RUN
)