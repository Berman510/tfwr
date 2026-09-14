import farm_telemetry


# ============================================================
# MEGAFARM COORDINATION
# ============================================================


# ============================================================
# WORKER COUNT
# ============================================================

def worker_count(
	work_count
):

	available = (
		max_drones()
		- num_drones()
		+ 1
	)


	if available < 1:

		available = 1


	count = min(
		available,
		work_count
	)


	farm_telemetry.max_metric(
		"megafarm max workers scheduled",
		count
	)


	return count


# ============================================================
# SPAWN TELEMETRY
# ============================================================

def record_spawn(
	handle
):

	farm_telemetry.add_counter(
		"megafarm spawn attempts",
		1
	)


	if handle != None:

		farm_telemetry.add_counter(
			"megafarm successful spawns",
			1
		)

	else:

		farm_telemetry.add_counter(
			"megafarm failed spawns",
			1
		)


# ============================================================
# OPERATION TELEMETRY
# ============================================================

def record_operation(
	planned_workers,
	work_units
):

	farm_telemetry.add_counter(
		"megafarm operations",
		1
	)

	farm_telemetry.add_counter(
		"megafarm work units",
		work_units
	)


	farm_telemetry.record_drone_operation(
		planned_workers,
		work_units,
		num_drones()
	)


# ============================================================
# RUN ROWS
# ============================================================

def run_rows(
	worker,
	size
):

	count = worker_count(
		size
	)


	def stripe(
		start
	):

		row = start


		while row < size:

			worker(
				row
			)

			row = (
				row + count
			)


	handles = []
	failed = []


	for start in range(
		1,
		count
	):

		handle = spawn_drone(
			stripe,
			start
		)

		record_spawn(
			handle
		)


		if handle != None:

			handles.append(
				handle
			)

		else:

			failed.append(
				start
			)


	record_operation(
		count,
		size
	)


	stripe(
		0
	)


	for start in failed:

		farm_telemetry.add_counter(
			"megafarm serial fallbacks",
			1
		)

		stripe(
			start
		)


	for handle in handles:

		wait_for(
			handle
		)


# ============================================================
# RUN ROWS WITH ARGUMENT
# ============================================================

def run_rows_with_arg(
	worker,
	size,
	arg
):

	count = worker_count(
		size
	)


	def stripe(
		start
	):

		row = start


		while row < size:

			worker(
				row,
				arg
			)

			row = (
				row + count
			)


	handles = []
	failed = []


	for start in range(
		1,
		count
	):

		handle = spawn_drone(
			stripe,
			start
		)

		record_spawn(
			handle
		)


		if handle != None:

			handles.append(
				handle
			)

		else:

			failed.append(
				start
			)


	record_operation(
		count,
		size
	)


	stripe(
		0
	)


	for start in failed:

		farm_telemetry.add_counter(
			"megafarm serial fallbacks",
			1
		)

		stripe(
			start
		)


	for handle in handles:

		wait_for(
			handle
		)


# ============================================================
# BOOLEAN ROWS
# ============================================================

def run_rows_bool(
	worker,
	size
):

	count = worker_count(
		size
	)


	def stripe(
		start
	):

		stripe_ready = True

		row = start


		while row < size:

			if not worker(
				row
			):

				stripe_ready = False


			row = (
				row + count
			)


		return stripe_ready


	handles = []
	failed = []


	for start in range(
		1,
		count
	):

		handle = spawn_drone(
			stripe,
			start
		)

		record_spawn(
			handle
		)


		if handle != None:

			handles.append(
				handle
			)

		else:

			failed.append(
				start
			)


	record_operation(
		count,
		size
	)


	all_ready = stripe(
		0
	)


	for start in failed:

		farm_telemetry.add_counter(
			"megafarm serial fallbacks",
			1
		)


		if not stripe(
			start
		):

			all_ready = False


	for handle in handles:

		if not wait_for(
			handle
		):

			all_ready = False


	return all_ready


# ============================================================
# BOOLEAN ROWS WITH ARGUMENT
# ============================================================

def run_rows_bool_with_arg(
	worker,
	size,
	arg
):

	count = worker_count(
		size
	)


	def stripe(
		start
	):

		stripe_ready = True

		row = start


		while row < size:

			if not worker(
				row,
				arg
			):

				stripe_ready = False


			row = (
				row + count
			)


		return stripe_ready


	handles = []
	failed = []


	for start in range(
		1,
		count
	):

		handle = spawn_drone(
			stripe,
			start
		)

		record_spawn(
			handle
		)


		if handle != None:

			handles.append(
				handle
			)

		else:

			failed.append(
				start
			)


	record_operation(
		count,
		size
	)


	all_ready = stripe(
		0
	)


	for start in failed:

		farm_telemetry.add_counter(
			"megafarm serial fallbacks",
			1
		)


		if not stripe(
			start
		):

			all_ready = False


	for handle in handles:

		if not wait_for(
			handle
		):

			all_ready = False


	return all_ready


# ============================================================
# COLLECT ROW LISTS
# ============================================================

def collect_rows(
	worker,
	size
):

	count = worker_count(
		size
	)


	def stripe(
		start
	):

		results = []

		row = start


		while row < size:

			row_results = worker(
				row
			)


			for value in row_results:

				results.append(
					value
				)


			row = (
				row + count
			)


		return results


	handles = []
	failed = []


	for start in range(
		1,
		count
	):

		handle = spawn_drone(
			stripe,
			start
		)

		record_spawn(
			handle
		)


		if handle != None:

			handles.append(
				handle
			)

		else:

			failed.append(
				start
			)


	record_operation(
		count,
		size
	)


	results = stripe(
		0
	)


	for start in failed:

		farm_telemetry.add_counter(
			"megafarm serial fallbacks",
			1
		)


		more = stripe(
			start
		)


		for value in more:

			results.append(
				value
			)


	for handle in handles:

		more = wait_for(
			handle
		)


		for value in more:

			results.append(
				value
			)


	return results


# ============================================================
# SUM NUMERIC ROW RESULTS
# ============================================================

def sum_rows(
	worker,
	size
):

	count = worker_count(
		size
	)


	def stripe(
		start
	):

		total = 0

		row = start


		while row < size:

			total = (
				total
				+ worker(
					row
				)
			)

			row = (
				row + count
			)


		return total


	handles = []
	failed = []


	for start in range(
		1,
		count
	):

		handle = spawn_drone(
			stripe,
			start
		)

		record_spawn(
			handle
		)


		if handle != None:

			handles.append(
				handle
			)

		else:

			failed.append(
				start
			)


	record_operation(
		count,
		size
	)


	total = stripe(
		0
	)


	for start in failed:

		farm_telemetry.add_counter(
			"megafarm serial fallbacks",
			1
		)

		total = (
			total
			+ stripe(
				start
			)
		)


	for handle in handles:

		total = (
			total
			+ wait_for(
				handle
			)
		)


	return total


# ============================================================
# RUN ITEMS
# ============================================================

def run_items(
	worker,
	items
):

	total = len(
		items
	)


	if total == 0:

		return


	count = worker_count(
		total
	)


	def chunk(
		worker_id
	):

		start = (
			total
			* worker_id
			// count
		)

		end = (
			total
			* (
				worker_id + 1
			)
			// count
		)


		for index in range(
			start,
			end
		):

			worker(
				items[index]
			)


	handles = []
	failed = []


	for worker_id in range(
		1,
		count
	):

		handle = spawn_drone(
			chunk,
			worker_id
		)

		record_spawn(
			handle
		)


		if handle != None:

			handles.append(
				handle
			)

		else:

			failed.append(
				worker_id
			)


	record_operation(
		count,
		total
	)


	chunk(
		0
	)


	for worker_id in failed:

		farm_telemetry.add_counter(
			"megafarm serial fallbacks",
			1
		)

		chunk(
			worker_id
		)


	for handle in handles:

		wait_for(
			handle
		)


# ============================================================
# SUM NUMERIC ITEM RESULTS
# ============================================================

def sum_items(
	worker,
	items
):

	total_items = len(
		items
	)


	if total_items == 0:

		return 0


	count = worker_count(
		total_items
	)


	def chunk(
		worker_id
	):

		result = 0


		start = (
			total_items
			* worker_id
			// count
		)

		end = (
			total_items
			* (
				worker_id + 1
			)
			// count
		)


		for index in range(
			start,
			end
		):

			result = (
				result
				+ worker(
					items[index]
				)
			)


		return result


	handles = []
	failed = []


	for worker_id in range(
		1,
		count
	):

		handle = spawn_drone(
			chunk,
			worker_id
		)

		record_spawn(
			handle
		)


		if handle != None:

			handles.append(
				handle
			)

		else:

			failed.append(
				worker_id
			)


	record_operation(
		count,
		total_items
	)


	result = chunk(
		0
	)


	for worker_id in failed:

		farm_telemetry.add_counter(
			"megafarm serial fallbacks",
			1
		)

		result = (
			result
			+ chunk(
				worker_id
			)
		)


	for handle in handles:

		result = (
			result
			+ wait_for(
				handle
			)
		)


	return result


# ============================================================
# STRIPE ROWS
# ============================================================

def stripe_rows(
	start,
	count,
	size
):

	rows = []

	row = start


	while row < size:

		rows.append(
			row
		)

		row = (
			row + count
		)


	return rows


# ============================================================
# RUN CONTINUOUS STRIPES WITH ARGUMENT
# ============================================================
#
# For long-running workers that loop over their own rows until
# a shared stop condition (inventory target / deadline), e.g.
# farm_wood and farm_hay.
#
#     worker(rows, arg)
#
# receives every row that drone owns.
#
# Rows of a stripe whose spawn failed go to the coordinator,
# so no row is left unfarmed. (Running them serially afterward
# would be useless: the stop condition is already met.)

def run_stripes_with_arg(
	worker,
	size,
	arg
):

	count = worker_count(
		size
	)


	coordinator_rows = stripe_rows(
		0,
		count,
		size
	)


	handles = []


	for start in range(
		1,
		count
	):

		rows = stripe_rows(
			start,
			count,
			size
		)


		handle = spawn_drone(
			worker,
			rows,
			arg
		)

		record_spawn(
			handle
		)


		if handle != None:

			handles.append(
				handle
			)

		else:

			farm_telemetry.add_counter(
				"megafarm serial fallbacks",
				1
			)


			for row in rows:

				coordinator_rows.append(
					row
				)


	record_operation(
		count,
		size
	)


	worker(
		coordinator_rows,
		arg
	)


	for handle in handles:

		wait_for(
			handle
		)
