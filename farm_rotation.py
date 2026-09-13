import farm_common
import farm_megafarm
import farm_polyculture
import farm_telemetry
import cact_sort
import sun_sort


# ============================================================
# FULL-FIELD ROTATION
# ============================================================


def move_to_row_start(
	row
):

	farm_common.go_to(
		0,
		row
	)


# ============================================================
# GENERIC SOIL PREPARATION
# ============================================================

def prepare_soil_row(
	row,
	entity
):

	size = get_world_size()

	row_ready = True


	move_to_row_start(
		row
	)


	for x in range(size):

		farm_common.harvest_reset_grass()

		farm_common.make_soil()


		if farm_common.plant_if_affordable(
			entity
		):

			farm_common.boost_growth(
				entity
			)


		if get_entity_type() != entity:

			row_ready = False

		elif not can_harvest():

			row_ready = False


		if x < size - 1:

			move(
				East
			)


	return row_ready


# ============================================================
# GENERIC SOIL REPAIR
# ============================================================

def check_soil_row(
	row,
	entity
):

	size = get_world_size()

	row_ready = True


	move_to_row_start(
		row
	)


	for x in range(size):

		farm_common.make_soil()

		current = get_entity_type()


		if current != entity:

			if current != None:

				harvest()


			if farm_common.plant_if_affordable(
				entity
			):

				farm_common.boost_growth(
					entity
				)


		elif not can_harvest():

			farm_common.boost_growth(
				entity
			)


		if get_entity_type() != entity:

			row_ready = False

		elif not can_harvest():

			row_ready = False


		if x < size - 1:

			move(
				East
			)


	return row_ready


# ============================================================
# HARVEST ROW
# ============================================================

def harvest_row(
	row
):

	size = get_world_size()


	move_to_row_start(
		row
	)


	for x in range(size):

		if can_harvest():

			harvest()


		if x < size - 1:

			move(
				East
			)


# ============================================================
# PREPARE SOIL FIELD
# ============================================================

def prepare_soil_field(
	entity,
	cost_multiplier
):

	size = get_world_size()


	required_plants = (
		size
		* size
		* cost_multiplier
	)


	if not farm_common.can_afford(
		entity,
		required_plants
	):

		farm_telemetry.add_counter(
			"crop phases skipped for cost",
			1
		)

		return (
			0,
			False
		)


	farm_common.clear_field()

	farm_common.wear_crop_hat(
		entity
	)


	ready = farm_megafarm.run_rows_bool_with_arg(
		prepare_soil_row,
		size,
		entity
	)


	return (
		size,
		ready
	)


# ============================================================
# WAIT FOR SOIL FIELD
# ============================================================

def wait_for_soil_field(
	entity,
	size
):

	passes = 0


	while not farm_megafarm.run_rows_bool_with_arg(
		check_soil_row,
		size,
		entity
	):

		passes = (
			passes + 1
		)


	return passes


# ============================================================
# HARVEST FULL FIELD
# ============================================================

def harvest_entire_field(
	size
):

	farm_megafarm.run_rows(
		harvest_row,
		size
	)


# ============================================================
# TREE CHECKERBOARD
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


def tree_count_for_world(
	size
):

	if size % 2 == 0:

		return (
			size
			* size
			// 2
		)


	effective = (
		size - 1
	)


	return (
		effective
		* effective
		// 2
	)


# ============================================================
# TREE / HAY PREPARATION
# ============================================================

def prepare_wood_hay_row(
	row
):

	size = get_world_size()

	row_ready = True


	move_to_row_start(
		row
	)


	for x in range(size):

		farm_common.harvest_reset_grass()

		farm_common.make_grassland()


		if is_tree_tile(
			x,
			row,
			size
		):

			if farm_common.plant_if_affordable(
				Entities.Tree
			):

				farm_common.boost_growth(
					Entities.Tree
				)


			if get_entity_type() != Entities.Tree:

				row_ready = False

			elif not can_harvest():

				row_ready = False


		else:

			if get_entity_type() != Entities.Grass:

				row_ready = False


			elif not can_harvest():

				farm_common.boost_growth(
					Entities.Grass
				)


				if not can_harvest():

					row_ready = False


		if x < size - 1:

			move(
				East
			)


	return row_ready


# ============================================================
# TREE / HAY READINESS
# ============================================================

def check_wood_hay_row(
	row
):

	size = get_world_size()

	row_ready = True


	move_to_row_start(
		row
	)


	for x in range(size):

		farm_common.make_grassland()

		entity = get_entity_type()


		if is_tree_tile(
			x,
			row,
			size
		):

			if entity != Entities.Tree:

				if entity != None:

					harvest()


				if farm_common.plant_if_affordable(
					Entities.Tree
				):

					farm_common.boost_growth(
						Entities.Tree
					)


			elif not can_harvest():

				farm_common.boost_growth(
					Entities.Tree
				)


			if get_entity_type() != Entities.Tree:

				row_ready = False

			elif not can_harvest():

				row_ready = False


		else:

			if entity != Entities.Grass:

				if entity != None:

					harvest()


				row_ready = False


			else:

				if not can_harvest():

					farm_common.boost_growth(
						Entities.Grass
					)


				if not can_harvest():

					row_ready = False


		if x < size - 1:

			move(
				East
			)


	return row_ready


# ============================================================
# WOOD / HAY
# ============================================================

def farm_wood_hay():

	size = get_world_size()


	tree_count = tree_count_for_world(
		size
	)


	if not farm_common.can_afford(
		Entities.Tree,
		tree_count
	):

		return


	start = farm_telemetry.subphase_start(
		"prepare / grow"
	)


	farm_common.clear_field()


	ready = farm_megafarm.run_rows_bool(
		prepare_wood_hay_row,
		size
	)


	passes = 0


	if not ready:

		while not farm_megafarm.run_rows_bool(
			check_wood_hay_row,
			size
		):

			passes = (
				passes + 1
			)


	farm_telemetry.subphase_end(
		"prepare / grow",
		start
	)


	farm_telemetry.add_counter(
		"wood/hay readiness passes",
		passes
	)


	if farm_polyculture.enabled():

		farm_polyculture.harvest_wood_hay_field(
			size
		)


	else:

		start = farm_telemetry.subphase_start(
			"harvest"
		)


		harvest_entire_field(
			size
		)


		farm_telemetry.subphase_end(
			"harvest",
			start
		)


# ============================================================
# CARROTS
# ============================================================

def farm_carrots():

	start = farm_telemetry.subphase_start(
		"prepare / grow"
	)


	size, ready = prepare_soil_field(
		Entities.Carrot,
		1
	)


	if size == 0:

		farm_telemetry.subphase_end(
			"prepare / grow",
			start
		)

		return


	passes = 0


	if not ready:

		passes = wait_for_soil_field(
			Entities.Carrot,
			size
		)


	farm_telemetry.subphase_end(
		"prepare / grow",
		start
	)


	farm_telemetry.add_counter(
		"carrot readiness passes",
		passes
	)


	if farm_polyculture.enabled():

		farm_polyculture.harvest_carrot_field(
			size
		)


	else:

		start = farm_telemetry.subphase_start(
			"harvest"
		)


		harvest_entire_field(
			size
		)


		farm_telemetry.subphase_end(
			"harvest",
			start
		)


# ============================================================
# SUNFLOWERS
# ============================================================

def scan_sunflower_row(
	row
):

	size = get_world_size()

	results = []


	move_to_row_start(
		row
	)


	for x in range(size):

		if get_entity_type() == Entities.Sunflower:

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


	return results


def harvest_sunflower_point(
	point
):

	x = point[0]

	y = point[1]


	farm_common.go_to(
		x,
		y
	)


	if get_entity_type() == Entities.Sunflower:

		if can_harvest():

			harvest()


def farm_sunflowers():

	# --------------------------------------------------------
	# PLANT / GROW
	# --------------------------------------------------------

	start = farm_telemetry.subphase_start(
		"prepare / grow"
	)


	size, ready = prepare_soil_field(
		Entities.Sunflower,
		1
	)


	if size == 0:

		farm_telemetry.subphase_end(
			"prepare / grow",
			start
		)

		return


	passes = 0


	if not ready:

		passes = wait_for_soil_field(
			Entities.Sunflower,
			size
		)


	farm_telemetry.subphase_end(
		"prepare / grow",
		start
	)


	farm_telemetry.add_counter(
		"sunflower readiness passes",
		passes
	)


	# --------------------------------------------------------
	# SCAN
	# --------------------------------------------------------

	start = farm_telemetry.subphase_start(
		"scan / measure"
	)


	entries = farm_megafarm.collect_rows(
		scan_sunflower_row,
		size
	)


	farm_telemetry.subphase_end(
		"scan / measure",
		start
	)


	farm_telemetry.add_counter(
		"sunflowers measured",
		len(entries)
	)


	# --------------------------------------------------------
	# BUILD PETAL BUCKETS
	# --------------------------------------------------------

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

		buckets[
			entry[0]
		].append(
			(
				entry[1],
				entry[2]
			)
		)


	# --------------------------------------------------------
	# HARVEST
	# --------------------------------------------------------

	start = farm_telemetry.subphase_start(
		"harvest"
	)


	remaining = len(
		entries
	)


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
		# SPATIAL SNAKE ORDER
		# ----------------------------------------------------
		#
		# All points in this bucket have identical petal count,
		# so changing their order cannot violate sunflower
		# priority.
		#
		# We reorder BEFORE splitting the >=10 bonus boundary.
		# Since every point has equal petals, any subset of the
		# bucket is valid for the remaining bonus harvests.

		points = sun_sort.order(
			points,
			size
		)


		# ----------------------------------------------------
		# BONUS BOUNDARY
		# ----------------------------------------------------

		bonus_count = 0


		if remaining >= 10:

			available_bonus = (
				remaining - 9
			)


			bonus_count = min(
				count,
				available_bonus
			)


		bonus_points = []

		normal_points = []


		for index in range(
			count
		):

			if index < bonus_count:

				bonus_points.append(
					points[index]
				)

			else:

				normal_points.append(
					points[index]
				)


		# ----------------------------------------------------
		# BONUS GROUP
		# ----------------------------------------------------

		if len(
			bonus_points
		) > 0:

			farm_megafarm.run_items(
				harvest_sunflower_point,
				bonus_points
			)


			farm_telemetry.add_counter(
				"sunflower bonus parallel harvests",
				len(
					bonus_points
				)
			)


			remaining = (
				remaining
				- len(
					bonus_points
				)
			)


		# ----------------------------------------------------
		# NON-BONUS GROUP
		# ----------------------------------------------------

		if len(
			normal_points
		) > 0:

			farm_megafarm.run_items(
				harvest_sunflower_point,
				normal_points
			)


			farm_telemetry.add_counter(
				"sunflower nonbonus parallel harvests",
				len(
					normal_points
				)
			)


			remaining = (
				remaining
				- len(
					normal_points
				)
			)


	farm_telemetry.subphase_end(
		"harvest",
		start
	)


# ============================================================
# PUMPKINS
# ============================================================

def check_pumpkin_row(
	row
):

	size = get_world_size()

	row_ready = True


	move_to_row_start(
		row
	)


	for x in range(size):

		farm_common.make_soil()

		entity = get_entity_type()


		if entity == Entities.Dead_Pumpkin:

			if farm_common.plant_if_affordable(
				Entities.Pumpkin
			):

				farm_common.boost_growth(
					Entities.Pumpkin
				)


		elif entity != Entities.Pumpkin:

			if entity != None:

				harvest()


			if farm_common.plant_if_affordable(
				Entities.Pumpkin
			):

				farm_common.boost_growth(
					Entities.Pumpkin
				)


		elif not can_harvest():

			farm_common.boost_growth(
				Entities.Pumpkin
			)


		if get_entity_type() != Entities.Pumpkin:

			row_ready = False

		elif not can_harvest():

			row_ready = False


		if x < size - 1:

			move(
				East
			)


	return row_ready


def pumpkin_is_merged(
	size
):

	farm_telemetry.add_counter(
		"pumpkin merge checks",
		1
	)


	farm_common.go_to(
		0,
		0
	)


	if get_entity_type() != Entities.Pumpkin:

		return False


	first_id = measure()


	farm_common.go_to(
		size - 1,
		size - 1
	)


	if get_entity_type() != Entities.Pumpkin:

		return False


	last_id = measure()


	return (
		first_id == last_id
	)


def farm_pumpkins():

	start = farm_telemetry.subphase_start(
		"initial plant / grow"
	)


	size, ready = prepare_soil_field(
		Entities.Pumpkin,
		3
	)


	farm_telemetry.subphase_end(
		"initial plant / grow",
		start
	)


	if size == 0:

		return


	repair_passes = 0


	start = farm_telemetry.subphase_start(
		"repair / merge"
	)


	while True:

		if ready:

			if pumpkin_is_merged(
				size
			):

				break


		repair_passes = (
			repair_passes + 1
		)


		ready = farm_megafarm.run_rows_bool(
			check_pumpkin_row,
			size
		)


	farm_telemetry.subphase_end(
		"repair / merge",
		start
	)


	farm_telemetry.add_counter(
		"pumpkin repair passes",
		repair_passes
	)


	start = farm_telemetry.subphase_start(
		"harvest"
	)


	farm_common.go_to(
		0,
		0
	)


	if can_harvest():

		harvest()


	farm_telemetry.subphase_end(
		"harvest",
		start
	)


# ============================================================
# CACTUS
# ============================================================

def farm_cactus():

	start = farm_telemetry.subphase_start(
		"prepare / grow"
	)


	size, ready = prepare_soil_field(
		Entities.Cactus,
		1
	)


	if size == 0:

		farm_telemetry.subphase_end(
			"prepare / grow",
			start
		)

		return


	passes = 0


	if not ready:

		passes = wait_for_soil_field(
			Entities.Cactus,
			size
		)


	farm_telemetry.subphase_end(
		"prepare / grow",
		start
	)


	farm_telemetry.add_counter(
		"cactus readiness passes",
		passes
	)


	sorted_field = False

	sort_rounds = 0

	row_swaps = 0

	column_swaps = 0


	while not sorted_field:

		sort_rounds = (
			sort_rounds + 1
		)


		# ----------------------------------------------------
		# ROW SORT
		# ----------------------------------------------------

		start = farm_telemetry.subphase_start(
			"row sort"
		)


		row_swaps = (
			row_swaps
			+ cact_sort.sort_rows(
				size
			)
		)


		farm_telemetry.subphase_end(
			"row sort",
			start
		)


		# ----------------------------------------------------
		# COLUMN SORT
		# ----------------------------------------------------

		start = farm_telemetry.subphase_start(
			"column sort"
		)


		column_swaps = (
			column_swaps
			+ cact_sort.sort_columns(
				size
			)
		)


		farm_telemetry.subphase_end(
			"column sort",
			start
		)


		# ----------------------------------------------------
		# VERIFY
		# ----------------------------------------------------
		#
		# cact_sort.verify() is intentionally a zero-cost
		# compatibility shim after our fixed-seed benchmark
		# demonstrated that full verification is redundant.

		start = farm_telemetry.subphase_start(
			"verification"
		)


		sorted_field = cact_sort.verify(
			size
		)


		farm_telemetry.subphase_end(
			"verification",
			start
		)


	farm_telemetry.add_counter(
		"cactus sort rounds",
		sort_rounds
	)

	farm_telemetry.add_counter(
		"cactus row swaps",
		row_swaps
	)

	farm_telemetry.add_counter(
		"cactus column swaps",
		column_swaps
	)


	start = farm_telemetry.subphase_start(
		"chain harvest"
	)


	farm_common.go_to(
		0,
		0
	)


	if can_harvest():

		harvest()


	farm_telemetry.subphase_end(
		"chain harvest",
		start
	)


# ============================================================
# COMPLETE ROTATION
# ============================================================

def run_cycle():

	start = farm_telemetry.phase_start(
		"wood/hay"
	)

	farm_wood_hay()

	farm_telemetry.phase_end(
		"wood/hay",
		start
	)


	start = farm_telemetry.phase_start(
		"carrots"
	)

	farm_carrots()

	farm_telemetry.phase_end(
		"carrots",
		start
	)


	start = farm_telemetry.phase_start(
		"sunflowers"
	)

	farm_sunflowers()

	farm_telemetry.phase_end(
		"sunflowers",
		start
	)


	start = farm_telemetry.phase_start(
		"pumpkins"
	)

	farm_pumpkins()

	farm_telemetry.phase_end(
		"pumpkins",
		start
	)


	start = farm_telemetry.phase_start(
		"cactus"
	)

	farm_cactus()

	farm_telemetry.phase_end(
		"cactus",
		start
	)