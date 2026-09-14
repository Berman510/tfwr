import farm_common
import farm_megafarm
import farm_telemetry


# ============================================================
# POLYCULTURE
# ============================================================
#
# Architecture:
#
#     SCAN
#         All drones inspect source plants.
#
#     PLAN
#         Coordinator resolves targets globally.
#
#         Accepted tasks and rejected sources are placed
#         directly into coordinate grids.
#
#         The grids are then flattened in snake order:
#
#             row 0 -> East
#             row 1 -> West
#             row 2 -> East
#             ...
#
#         This replaces the previous insertion-sort planner.
#
#     FUSED EXECUTE
#         Place companion, then immediately harvest all
#         sources using that target.
#
#     REJECT CLEANUP
#         Only rejected sources require a separate harvest.
#
# ============================================================


# ============================================================
# RESULT ENCODING
# ============================================================

COUNT_BASE = 10000

PLACE_BASE = (
	COUNT_BASE
	* COUNT_BASE
)


# ============================================================
# ENABLED
# ============================================================

def enabled():

	return (
		num_unlocked(
			Unlocks.Polyculture
		) > 0
	)


# ============================================================
# CARROT SOURCE TILE
# ============================================================

def is_carrot_source(
	x,
	y
):

	return (
		(x + y) % 2 == 0
	)


# ============================================================
# CARROT SCAN
# ============================================================

def scan_carrot_row(
	row
):

	size = get_world_size()

	results = []


	farm_common.go_to(
		0,
		row
	)


	for x in range(size):

		if is_carrot_source(
			x,
			row
		):

			if get_entity_type() == Entities.Carrot:

				if can_harvest():

					companion = get_companion()


					if companion == None:

						results.append(
							(
								x,
								row,
								Entities.Carrot,
								None,
								-1,
								-1
							)
						)


					else:

						position = companion[1]


						results.append(
							(
								x,
								row,
								Entities.Carrot,
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
# TARGET SAFETY
# ============================================================

def target_is_safe(
	mode,
	x,
	y,
	size
):

	# Carrot source parity -> opposite parity only.
	#
	# mode is kept so other source types can be added later.

	return not is_carrot_source(
		x,
		y
	)


# ============================================================
# SOURCE ITEM
# ============================================================

def source_item(
	record
):

	return (
		record[0],
		record[1],
		record[2]
	)


# ============================================================
# EMPTY COORDINATE GRID
# ============================================================

def make_grid(
	size
):

	grid = []


	for y in range(size):

		row = []


		for x in range(size):

			row.append(
				None
			)


		grid.append(
			row
		)


	return grid


# ============================================================
# FLATTEN TASK GRID IN SNAKE ORDER
# ============================================================

def flatten_task_grid(
	grid,
	tasks,
	size
):

	result = []


	for y in range(size):

		if y % 2 == 0:

			for x in range(size):

				task_index = grid[
					y
				][
					x
				]


				if task_index != None:

					result.append(
						tasks[
							task_index
						]
					)


		else:

			x = (
				size - 1
			)


			while x >= 0:

				task_index = grid[
					y
				][
					x
				]


				if task_index != None:

					result.append(
						tasks[
							task_index
						]
					)


				x = (
					x - 1
				)


	return result


# ============================================================
# FLATTEN SOURCE GRID IN SNAKE ORDER
# ============================================================

def flatten_source_grid(
	grid,
	size
):

	result = []


	for y in range(size):

		if y % 2 == 0:

			for x in range(size):

				source = grid[
					y
				][
					x
				]


				if source != None:

					result.append(
						source
					)


		else:

			x = (
				size - 1
			)


			while x >= 0:

				source = grid[
					y
				][
					x
				]


				if source != None:

					result.append(
						source
					)


				x = (
					x - 1
				)


	return result


# ============================================================
# GLOBAL FUSED PLAN
# ============================================================
#
# Task:
#
# [
#     companion_entity,
#     target_x,
#     target_y,
#     [
#         source,
#         source,
#         ...
#     ]
# ]
#
#
# Instead of:
#
#     create list
#     insertion-sort list spatially
#
# we now:
#
#     create task
#     place task index directly into task_grid[y][x]
#
# and later walk the grid in snake order.
#
# Same applies to rejected sources.
#
# ============================================================

def build_plan(
	records,
	mode,
	size
):

	# --------------------------------------------------------
	# TARGET LOOKUP
	# --------------------------------------------------------
	#
	# Maps target coordinate -> index in tasks.
	#
	# The task itself contains the winning companion entity,
	# so a second target_entities dictionary is unnecessary.

	target_tasks = {}


	# --------------------------------------------------------
	# STORAGE
	# --------------------------------------------------------

	tasks = []

	task_grid = make_grid(
		size
	)

	reject_grid = make_grid(
		size
	)


	# --------------------------------------------------------
	# COUNTERS
	# --------------------------------------------------------

	accepted = 0

	unsafe = 0

	conflicts = 0

	requests = 0


	# --------------------------------------------------------
	# PROCESS REQUESTS
	# --------------------------------------------------------

	for record in records:

		source = source_item(
			record
		)


		source_x = source[0]

		source_y = source[1]


		companion_entity = record[3]


		# ----------------------------------------------------
		# NO COMPANION REQUEST
		# ----------------------------------------------------

		if companion_entity == None:

			reject_grid[
				source_y
			][
				source_x
			] = source

			continue


		requests = (
			requests + 1
		)


		target_x = record[4]

		target_y = record[5]


		# ----------------------------------------------------
		# UNSAFE TARGET
		# ----------------------------------------------------

		if not target_is_safe(
			mode,
			target_x,
			target_y,
			size
		):

			unsafe = (
				unsafe + 1
			)


			reject_grid[
				source_y
			][
				source_x
			] = source

			continue


		key = (
			target_x,
			target_y
		)


		# ----------------------------------------------------
		# NEW TARGET
		# ----------------------------------------------------

		if key not in target_tasks:

			sources = []

			sources.append(
				source
			)


			task_index = len(
				tasks
			)


			tasks.append(
				[
					companion_entity,
					target_x,
					target_y,
					sources
				]
			)


			target_tasks[
				key
			] = task_index


			task_grid[
				target_y
			][
				target_x
			] = task_index


			accepted = (
				accepted + 1
			)


		# ----------------------------------------------------
		# EXISTING TARGET
		# ----------------------------------------------------

		else:

			task_index = target_tasks[
				key
			]


			task = tasks[
				task_index
			]


			# ------------------------------------------------
			# SAME COMPANION ENTITY
			# ------------------------------------------------

			if task[0] == companion_entity:

				task[3].append(
					source
				)


				accepted = (
					accepted + 1
				)


			# ------------------------------------------------
			# CONFLICT
			# ------------------------------------------------

			else:

				conflicts = (
					conflicts + 1
				)


				reject_grid[
					source_y
				][
					source_x
				] = source


	# --------------------------------------------------------
	# O(AREA) SPATIAL FLATTEN
	# --------------------------------------------------------

	ordered_tasks = flatten_task_grid(
		task_grid,
		tasks,
		size
	)


	ordered_rejected = flatten_source_grid(
		reject_grid,
		size
	)


	return (
		ordered_tasks,
		ordered_rejected,
		accepted,
		unsafe,
		conflicts,
		requests
	)


# ============================================================
# PLACE COMPANION
# ============================================================

def place_companion(
	entity,
	x,
	y
):

	farm_common.go_to(
		x,
		y
	)


	current = get_entity_type()


	if current == entity:

		return True


	if not farm_common.can_afford(
		entity,
		1
	):

		return False


	if current != None:

		harvest()


	farm_common.make_soil()


	if farm_common.plant_if_affordable(
		entity
	):

		return True


	return False


# ============================================================
# HARVEST SOURCE
# ============================================================

def harvest_source(
	source
):

	x = source[0]

	y = source[1]

	entity = source[2]


	farm_common.go_to(
		x,
		y
	)


	if get_entity_type() != entity:

		return 0


	if not can_harvest():

		return 0


	harvest()


	return 1


# ============================================================
# FUSED TASK
# ============================================================

def execute_task(
	task
):

	entity = task[0]

	target_x = task[1]

	target_y = task[2]

	sources = task[3]


	placed = place_companion(
		entity,
		target_x,
		target_y
	)


	boosted = 0

	harvested = 0


	for source in sources:

		result = harvest_source(
			source
		)


		harvested = (
			harvested + result
		)


		if placed:

			boosted = (
				boosted + result
			)


	encoded = (
		boosted
		* COUNT_BASE
		+ harvested
	)


	if placed:

		encoded = (
			encoded
			+ PLACE_BASE
		)


	return encoded


# ============================================================
# DECODE FUSED RESULT
# ============================================================

def decode_result(
	encoded
):

	placements = (
		encoded
		// PLACE_BASE
	)


	remainder = (
		encoded
		% PLACE_BASE
	)


	boosted = (
		remainder
		// COUNT_BASE
	)


	harvested = (
		remainder
		% COUNT_BASE
	)


	return (
		placements,
		boosted,
		harvested
	)


# ============================================================
# REJECTED SOURCE HARVEST
# ============================================================

def harvest_rejected(
	source
):

	return harvest_source(
		source
	)


# ============================================================
# TELEMETRY
# ============================================================

def publish_plan(
	prefix,
	records,
	plan,
	result,
	rejected_harvests
):

	tasks = plan[0]

	rejected = plan[1]

	accepted = plan[2]

	unsafe = plan[3]

	conflicts = plan[4]

	requests = plan[5]


	decoded = decode_result(
		result
	)


	placements = decoded[0]

	boosted = decoded[1]

	fused_harvests = decoded[2]


	farm_telemetry.add_counter(
		prefix + " sources",
		len(records)
	)


	farm_telemetry.add_counter(
		prefix + " companion requests",
		requests
	)


	farm_telemetry.add_counter(
		prefix + " planned boosted sources",
		accepted
	)


	farm_telemetry.add_counter(
		prefix + " unsafe target rejects",
		unsafe
	)


	farm_telemetry.add_counter(
		prefix + " target conflicts",
		conflicts
	)


	farm_telemetry.add_counter(
		prefix + " fused tasks",
		len(tasks)
	)


	farm_telemetry.add_counter(
		prefix + " rejected sources",
		len(rejected)
	)


	farm_telemetry.add_counter(
		prefix + " successful companion placements",
		placements
	)


	farm_telemetry.add_counter(
		prefix + " fused source harvests",
		fused_harvests
	)


	farm_telemetry.add_counter(
		prefix + " boosted source harvests",
		boosted
	)


	farm_telemetry.add_counter(
		prefix + " rejected source harvests",
		rejected_harvests
	)


	if len(records) > 0:

		farm_telemetry.set_metric(
			prefix + " planned boost %",
			(
				accepted
				* 100
				/ len(records)
			)
		)


		farm_telemetry.set_metric(
			prefix + " actual boost %",
			(
				boosted
				* 100
				/ len(records)
			)
		)


	if len(tasks) > 0:

		farm_telemetry.set_metric(
			prefix + " placement success %",
			(
				placements
				* 100
				/ len(tasks)
			)
		)


# ============================================================
# EXECUTE ONE POLYCULTURE PASS
# ============================================================

def execute_pass(
	prefix,
	scan_worker,
	mode,
	size
):

	# --------------------------------------------------------
	# SCAN
	# --------------------------------------------------------

	start = farm_telemetry.subphase_start(
		prefix + " scan"
	)


	records = farm_megafarm.collect_rows(
		scan_worker,
		size
	)


	farm_telemetry.subphase_end(
		prefix + " scan",
		start
	)


	# --------------------------------------------------------
	# GRID PLAN
	# --------------------------------------------------------

	start = farm_telemetry.subphase_start(
		prefix + " plan"
	)


	plan = build_plan(
		records,
		mode,
		size
	)


	farm_telemetry.subphase_end(
		prefix + " plan",
		start
	)


	# --------------------------------------------------------
	# FUSED EXECUTION
	# --------------------------------------------------------

	start = farm_telemetry.subphase_start(
		prefix + " fused execute"
	)


	result = farm_megafarm.sum_items(
		execute_task,
		plan[0]
	)


	farm_telemetry.subphase_end(
		prefix + " fused execute",
		start
	)


	# --------------------------------------------------------
	# REJECTED CLEANUP
	# --------------------------------------------------------

	start = farm_telemetry.subphase_start(
		prefix + " rejected harvest"
	)


	rejected_harvests = farm_megafarm.sum_items(
		harvest_rejected,
		plan[1]
	)


	farm_telemetry.subphase_end(
		prefix + " rejected harvest",
		start
	)


	publish_plan(
		prefix,
		records,
		plan,
		result,
		rejected_harvests
	)


# ============================================================
# REMAINING CARROTS
# ============================================================

def harvest_remaining_carrot_row(
	row
):

	size = get_world_size()

	count = 0


	farm_common.go_to(
		0,
		row
	)


	for x in range(size):

		if get_entity_type() == Entities.Carrot:

			if can_harvest():

				harvest()


				count = (
					count + 1
				)


		if x < size - 1:

			move(
				East
			)


	return count


# ============================================================
# CARROT POLYCULTURE
# ============================================================

def harvest_carrot_field(
	size
):

	execute_pass(
		"carrot polyculture",
		scan_carrot_row,
		0,
		size
	)


	start = farm_telemetry.subphase_start(
		"carrot polyculture remaining harvest"
	)


	remaining = farm_megafarm.sum_rows(
		harvest_remaining_carrot_row,
		size
	)


	farm_telemetry.subphase_end(
		"carrot polyculture remaining harvest",
		start
	)


	farm_telemetry.add_counter(
		"carrot polyculture remaining carrots",
		remaining
	)
