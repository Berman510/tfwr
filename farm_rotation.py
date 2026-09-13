import farm_common
import farm_megafarm
import farm_polyculture
import farm_telemetry
import farm_wood
import farm_hay
import cact_sort
import farm_sunflower


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
		"wood"
	)

	farm_wood.farm()

	farm_telemetry.phase_end(
		"wood",
		start
	)


	start = farm_telemetry.phase_start(
		"hay"
	)

	farm_hay.farm()

	farm_telemetry.phase_end(
		"hay",
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

	farm_sunflower.farm()

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