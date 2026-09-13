# ============================================================
# WOOD MASTER RUNNER
# ============================================================
#
# Goal:
#
#     Gather 1,000,000,000 Wood within 60 seconds.
#
#
# Proven simulation:
#
#     Tree / Bush checkerboard
#     pre-watered
#
#     Average:     53.98 sec
#     Best:        53.14 sec
#     Worst:       54.97 sec
#     Throughput:  ~1.111B Wood / minute
#
#
# Layout:
#
#     T B T B T B ...
#     B T B T B T ...
#     T B T B T B ...
#
# Trees never have an orthogonally adjacent Tree.
#
#
# Runtime:
#
#     32 drones
#     one drone per row
#     every tile produces Wood
#
#
# Water is applied BEFORE the warmup.
# No Water operations occur during the timed window.
#
# No fertilizer.
# No Polyculture.
# ============================================================


TARGET = 1000000000

WARMUP = 15

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
# CROP FOR COORDINATE
# ============================================================
#
# Even parity = Tree
# Odd parity  = Bush
#
# On an even 32x32 toroidal world this guarantees that no
# Tree has an orthogonally adjacent Tree, including across
# world-wrap boundaries.
# ============================================================

def crop_for(
	x,
	y
):

	if (
		(x + y) % 2
		== 0
	):

		return Entities.Tree


	return Entities.Bush


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


	for x in range(
		size
	):

		entity = crop_for(
			x,
			row
		)


		current = get_entity_type()


		if current != None:

			harvest()


		plant(
			entity
		)


		if x < size - 1:

			move(
				East
			)


	return 1


# ============================================================
# PREPARE FIELD
# ============================================================

def prepare_field():

	clear()


	size = get_world_size()


	handles = []


	for row in range(
		1,
		size
	):

		handle = spawn_drone(
			prepare_row,
			row
		)


		if handle != None:

			handles.append(
				handle
			)


	prepare_row(
		0
	)


	for handle in handles:

		wait_for(
			handle
		)


# ============================================================
# WATER ONE ROW
# ============================================================
#
# Match the winning benchmark:
#
#     bring every tile to ~full water
#
# No watering occurs after this preparation phase.
# ============================================================

def water_row(
	row
):

	size = get_world_size()

	failed = 0


	go_to(
		0,
		row
	)


	for x in range(
		size
	):

		while get_water() < 0.99:

			if not use_item(
				Items.Water
			):

				break


		if get_water() < 0.99:

			failed = (
				failed + 1
			)


		if x < size - 1:

			move(
				East
			)


	return failed


# ============================================================
# PRE-WATER FIELD
# ============================================================

def prewater():

	size = get_world_size()


	handles = []


	for row in range(
		1,
		size
	):

		handle = spawn_drone(
			water_row,
			row
		)


		if handle != None:

			handles.append(
				handle
			)


	failed = water_row(
		0
	)


	for handle in handles:

		failed = (
			failed
			+ wait_for(
				handle
			)
		)


	return failed


# ============================================================
# HARVEST + REPLANT CURRENT TILE
# ============================================================

def cycle_tile(
	row
):

	x = get_pos_x()


	entity = crop_for(
		x,
		row
	)


	if can_harvest():

		harvest()


		plant(
			entity
		)


# ============================================================
# ROW WORKER
# ============================================================
#
# Each drone owns exactly one complete row.
#
# Sequence:
#
#     position
#       ↓
#     synchronization
#       ↓
#     15-second warmup
#       ↓
#     quiet barrier
#       ↓
#     snapshot shared Wood
#       ↓
#     final go barrier
#       ↓
#     measured +1B Wood
# ============================================================

def row_worker(
	row,
	start_at,
	warm_end,
	sample_at,
	go_at
):

	go_to(
		0,
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

		cycle_tile(
			row
		)


		move(
			East
		)


	# ========================================================
	# QUIET PERIOD
	# ========================================================
	#
	# Inventory must remain stable while all independent drone
	# memories take their baseline snapshot.

	while get_time() < sample_at:

		pass


	# ========================================================
	# COMMON BASELINE
	# ========================================================

	start_wood = num_items(
		Items.Wood
	)


	target_wood = (
		start_wood
		+ TARGET
	)


	# ========================================================
	# FINAL START BARRIER
	# ========================================================

	while get_time() < go_at:

		pass


	# ========================================================
	# MEASURED RUN
	# ========================================================

	while num_items(
		Items.Wood
	) < target_wood:

		cycle_tile(
			row
		)


		move(
			East
		)


# ============================================================
# MAIN
# ============================================================

quick_print(
	""
)

quick_print(
	"<<< WOOD_RUN_BEGIN >>>"
)

quick_print(
	"[WOOD]",
	"preparing Tree/Bush checkerboard"
)


prepare_field()


size = get_world_size()


quick_print(
	"[WOOD]",
	"world:",
	size,
	"x",
	size,
	"drones:",
	max_drones()
)


if size != 32:

	quick_print(
		"[WOOD WARNING]",
		"validated for 32x32"
	)


if max_drones() != 32:

	quick_print(
		"[WOOD WARNING]",
		"validated for 32 drones"
	)


# ============================================================
# PRE-WATER
# ============================================================

quick_print(
	"[WOOD]",
	"pre-watering field"
)


water_failures = prewater()


quick_print(
	"[WOOD]",
	"under-watered tiles:",
	water_failures
)


if water_failures > 0:

	quick_print(
		"[WOOD WARNING]",
		"not enough Water for validated configuration"
	)


# ============================================================
# TIMELINE
# ============================================================

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


# ============================================================
# SPAWN CHILD WORKERS
# ============================================================

handles = []


for row in range(
	1,
	size
):

	handle = spawn_drone(
		row_worker,
		row,
		start_at,
		warm_end,
		sample_at,
		go_at
	)


	if handle != None:

		handles.append(
			handle
		)


quick_print(
	"[WOOD]",
	"workers:",
	len(handles) + 1
)


# ============================================================
# COORDINATOR = ROW ZERO
# ============================================================

run_start = go_at


row_worker(
	0,
	start_at,
	warm_end,
	sample_at,
	go_at
)


# ============================================================
# JOIN
# ============================================================

for handle in handles:

	wait_for(
		handle
	)


run_end = get_time()


elapsed = (
	run_end - run_start
)


# ============================================================
# RESULT
# ============================================================

quick_print(
	"[WOOD]",
	"1B window:",
	elapsed,
	"seconds"
)


quick_print(
	"[WOOD]",
	"equivalent Wood/min:",
	(
		TARGET
		* 60
		/ elapsed
	)
)


if elapsed <= 60:

	quick_print(
		"[WOOD]",
		"PASS"
	)

else:

	quick_print(
		"[WOOD]",
		"MISS"
	)


quick_print(
	"<<< WOOD_RUN_END >>>"
)


print(
	"WOOD RUN COMPLETE\n",
	"Open output.txt"
)