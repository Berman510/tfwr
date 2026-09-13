# ============================================================
# SUNFLOWER HARVEST BENCHMARK TARGET
# ============================================================
#
# MODE:
#
#   0 = setup only
#
#   1 = CURRENT
#       Current production-style coordinate ordering.
#
#   2 = SNAKE
#       Order equal-petal sunflowers spatially:
#
#           row 0  -> East
#           row 1  -> West
#           row 2  -> East
#           ...
#
#       Then divide the spatial route evenly among drones.
#
#   3 = ROUTE
#       Start with the Snake layout, divide it evenly among
#       drones, then nearest-neighbor optimize each drone's
#       small local route.
#
#
# All modes:
#
#   - use exactly the same seeded sunflower field
#   - scan exactly once
#   - harvest petals 15 -> 7
#   - preserve the >= 10 sunflower bonus boundary
#
#
# This file intentionally imports nothing.
# ============================================================


# ============================================================
# MOVEMENT
# ============================================================

def go_to(
	x,
	y
):

	size = get_world_size()


	current_x = get_pos_x()


	east_steps = (
		x - current_x
	) % size

	west_steps = (
		current_x - x
	) % size


	if east_steps <= west_steps:

		for i in range(
			east_steps
		):

			move(
				East
			)

	else:

		for i in range(
			west_steps
		):

			move(
				West
			)


	current_y = get_pos_y()


	north_steps = (
		y - current_y
	) % size

	south_steps = (
		current_y - y
	) % size


	if north_steps <= south_steps:

		for i in range(
			north_steps
		):

			move(
				North
			)

	else:

		for i in range(
			south_steps
		):

			move(
				South
			)


# ============================================================
# PREPARE ONE ROW
# ============================================================

def prepare_row(
	row
):

	size = get_world_size()


	go_to(
		0,
		row
	)


	for x in range(size):

		# clear() leaves Grass.
		#
		# Harvest it before turning the tile into soil.

		if get_entity_type() != None:

			harvest()


		if get_ground_type() != Grounds.Soil:

			till()


		plant(
			Entities.Sunflower
		)


		if x < size - 1:

			move(
				East
			)


# ============================================================
# MATURITY CHECK
# ============================================================

def mature_row(
	row
):

	size = get_world_size()

	ready = True


	go_to(
		0,
		row
	)


	for x in range(size):

		if get_entity_type() != Entities.Sunflower:

			ready = False


		elif not can_harvest():

			ready = False


		if x < size - 1:

			move(
				East
			)


	return ready


# ============================================================
# PREPARE STRIPE
# ============================================================

def prep_stripe(
	start,
	count,
	size
):

	row = start


	while row < size:

		prepare_row(
			row
		)


		row = (
			row + count
		)


# ============================================================
# MATURITY STRIPE
# ============================================================

def mature_stripe(
	start,
	count,
	size
):

	ready = True

	row = start


	while row < size:

		if not mature_row(
			row
		):

			ready = False


		row = (
			row + count
		)


	return ready


# ============================================================
# PREPARE COMPLETE FIELD
# ============================================================

def prepare_field():

	clear()


	size = get_world_size()

	count = min(
		max_drones(),
		size
	)


	# --------------------------------------------------------
	# PLANT
	# --------------------------------------------------------

	handles = []


	for worker in range(
		1,
		count
	):

		handle = spawn_drone(
			prep_stripe,
			worker,
			count,
			size
		)


		if handle != None:

			handles.append(
				handle
			)


	prep_stripe(
		0,
		count,
		size
	)


	for handle in handles:

		wait_for(
			handle
		)


	# --------------------------------------------------------
	# WAIT FOR MATURITY
	# --------------------------------------------------------

	ready = False


	while not ready:

		ready = True

		handles = []


		for worker in range(
			1,
			count
		):

			handle = spawn_drone(
				mature_stripe,
				worker,
				count,
				size
			)


			if handle != None:

				handles.append(
					handle
				)


		if not mature_stripe(
			0,
			count,
			size
		):

			ready = False


		for handle in handles:

			if not wait_for(
				handle
			):

				ready = False


# ============================================================
# SCAN SUNFLOWERS
# ============================================================

def scan_stripe(
	start,
	count,
	size
):

	results = []

	row = start


	while row < size:

		go_to(
			0,
			row
		)


		for x in range(size):

			if get_entity_type() == Entities.Sunflower:

				if can_harvest():

					results.append(
						(
							measure(),
							x,
							row
						)
					)


			if x < size - 1:

				move(
					East
				)


		row = (
			row + count
		)


	return results


# ============================================================
# COMPLETE PARALLEL SCAN
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


		for entry in more:

			results.append(
				entry
			)


	return results


# ============================================================
# PETAL BUCKETS
# ============================================================

def make_buckets(
	entries
):

	buckets = {
		7: [],
		8: [],
		9: [],
		10: [],
		11: [],
		12: [],
		13: [],
		14: [],
		15: []
	}


	for entry in entries:

		petals = entry[0]


		buckets[
			petals
		].append(
			(
				entry[1],
				entry[2]
			)
		)


	return buckets


# ============================================================
# HARVEST POINT
# ============================================================

def harvest_point(
	point
):

	go_to(
		point[0],
		point[1]
	)


	if get_entity_type() == Entities.Sunflower:

		if can_harvest():

			harvest()


# ============================================================
# WORKER FOR A POINT LIST
# ============================================================

def point_worker(
	worker,
	count,
	points
):

	total = len(
		points
	)


	start = (
		total
		* worker
		// count
	)


	end = (
		total
		* (
			worker + 1
		)
		// count
	)


	for index in range(
		start,
		end
	):

		harvest_point(
			points[index]
		)


# ============================================================
# PARALLEL POINT HARVEST
# ============================================================

def run_points(
	points
):

	total = len(
		points
	)


	if total == 0:

		return


	count = min(
		max_drones(),
		total
	)


	handles = []


	for worker in range(
		1,
		count
	):

		handle = spawn_drone(
			point_worker,
			worker,
			count,
			points
		)


		if handle != None:

			handles.append(
				handle
			)


	point_worker(
		0,
		count,
		points
	)


	for handle in handles:

		wait_for(
			handle
		)


# ============================================================
# SORT ONE ROW'S POINTS BY X
# ============================================================

def sort_row_points(
	points
):

	for i in range(
		1,
		len(points)
	):

		current = points[i]

		current_x = current[0]

		j = (
			i - 1
		)


		while j >= 0:

			if points[j][0] <= current_x:

				break


			points[
				j + 1
			] = points[j]


			j = (
				j - 1
			)


		points[
			j + 1
		] = current


# ============================================================
# SERPENTINE SPATIAL ORDER
# ============================================================

def snake_order(
	points,
	size
):

	rows = []


	for y in range(size):

		rows.append(
			[]
		)


	for point in points:

		rows[
			point[1]
		].append(
			point
		)


	result = []


	for y in range(size):

		row_points = rows[y]


		sort_row_points(
			row_points
		)


		if y % 2 == 0:

			for point in row_points:

				result.append(
					point
				)


		else:

			index = (
				len(row_points) - 1
			)


			while index >= 0:

				result.append(
					row_points[index]
				)


				index = (
					index - 1
				)


	return result


# ============================================================
# TOROIDAL DISTANCE
# ============================================================

def distance(
	x1,
	y1,
	x2,
	y2,
	size
):

	dx = abs(
		x2 - x1
	)

	dy = abs(
		y2 - y1
	)


	dx = min(
		dx,
		size - dx
	)

	dy = min(
		dy,
		size - dy
	)


	return (
		dx + dy
	)


# ============================================================
# GREEDY LOCAL ROUTE
# ============================================================

def nearest_route(
	points,
	start_x,
	start_y,
	size
):

	total = len(
		points
	)


	if total < 2:

		return points


	used = []


	for i in range(total):

		used.append(
			False
		)


	result = []

	current_x = start_x
	current_y = start_y


	for step in range(total):

		best_index = -1

		best_distance = (
			size * 2 + 1
		)


		for index in range(total):

			if not used[index]:

				point = points[
					index
				]


				value = distance(
					current_x,
					current_y,
					point[0],
					point[1],
					size
				)


				if value < best_distance:

					best_distance = value

					best_index = index


		if best_index < 0:

			break


		best_point = points[
			best_index
		]


		result.append(
			best_point
		)


		used[
			best_index
		] = True


		current_x = best_point[0]
		current_y = best_point[1]


	return result


# ============================================================
# ROUTE EACH DRONE'S SPATIAL CHUNK
# ============================================================

def route_order(
	points,
	size
):

	total = len(
		points
	)


	if total < 2:

		return points


	# Start from an already-spatial ordering so that each
	# worker gets a compact geographic chunk.

	spatial = snake_order(
		points,
		size
	)


	count = min(
		max_drones(),
		total
	)


	# Every newly spawned child starts at the coordinator's
	# current position.

	start_x = get_pos_x()

	start_y = get_pos_y()


	result = []


	for worker in range(
		count
	):

		begin = (
			total
			* worker
			// count
		)


		end = (
			total
			* (
				worker + 1
			)
			// count
		)


		chunk = []


		for index in range(
			begin,
			end
		):

			chunk.append(
				spatial[index]
			)


		route = nearest_route(
			chunk,
			start_x,
			start_y,
			size
		)


		for point in route:

			result.append(
				point
			)


	return result


# ============================================================
# SPLIT LIST
# ============================================================

def split_points(
	points,
	first_count
):

	first = []

	second = []


	for index in range(
		len(points)
	):

		if index < first_count:

			first.append(
				points[index]
			)

		else:

			second.append(
				points[index]
			)


	return (
		first,
		second
	)


# ============================================================
# HARVEST COMPLETE SUNFLOWER FIELD
# ============================================================

def harvest_field(
	mode
):

	size = get_world_size()


	# --------------------------------------------------------
	# IDENTICAL SCAN FOR EVERY ALGORITHM
	# --------------------------------------------------------

	entries = scan_all()


	buckets = make_buckets(
		entries
	)


	remaining = len(
		entries
	)


	# --------------------------------------------------------
	# HIGHEST PETAL COUNT FIRST
	# --------------------------------------------------------

	for petals in range(
		15,
		6,
		-1
	):

		points = buckets[
			petals
		]


		count = len(
			points
		)


		if count == 0:

			continue


		# ----------------------------------------------------
		# SPATIAL ORDERING
		# ----------------------------------------------------

		if mode == 2:

			points = snake_order(
				points,
				size
			)


		elif mode == 3:

			# Initial spatial clustering.
			points = snake_order(
				points,
				size
			)


		# ----------------------------------------------------
		# PRESERVE BONUS BOUNDARY
		# ----------------------------------------------------

		bonus_count = 0


		if remaining >= 10:

			bonus_available = (
				remaining - 9
			)


			bonus_count = min(
				count,
				bonus_available
			)


		groups = split_points(
			points,
			bonus_count
		)


		bonus_points = groups[0]

		normal_points = groups[1]


		# ----------------------------------------------------
		# ROUTE OPTIMIZATION
		# ----------------------------------------------------
		#
		# Do this AFTER the bonus split.
		#
		# That guarantees routing never moves a non-bonus
		# sunflower ahead of one that must be harvested while
		# >= 10 flowers remain.

		if mode == 3:

			bonus_points = route_order(
				bonus_points,
				size
			)


			normal_points = route_order(
				normal_points,
				size
			)


		# ----------------------------------------------------
		# HARVEST BONUS GROUP
		# ----------------------------------------------------

		if len(
			bonus_points
		) > 0:

			run_points(
				bonus_points
			)


			remaining = (
				remaining
				- len(
					bonus_points
				)
			)


		# ----------------------------------------------------
		# HARVEST NON-BONUS GROUP
		# ----------------------------------------------------

		if len(
			normal_points
		) > 0:

			run_points(
				normal_points
			)


			remaining = (
				remaining
				- len(
					normal_points
				)
			)


# ============================================================
# ENTRYPOINT
# ============================================================

prepare_field()


if MODE == 1:

	harvest_field(
		1
	)


elif MODE == 2:

	harvest_field(
		2
	)


elif MODE == 3:

	harvest_field(
		3
	)