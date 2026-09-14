# ============================================================
# HAY MASTER RUNNER
# ============================================================
#
# Goal:
#
#     Gather 200,000,000 Hay within 60 seconds.
#
#
# Proven benchmark:
#
#     FIXED companion checkerboard
#
#     Average:     ~33.36 sec
#     Worst seed:  ~33.71 sec
#     Throughput:  ~359.7M Hay / minute
#
#
# Layout:
#
#     G C G C G C ...
#     C G C G C G ...
#     G C G C G C ...
#
#     G = Grass source
#     C = static Bush / Tree / Carrot
#
#
# Runtime:
#
#     32 drones
#     one drone per row
#     each drone harvests its 16 Grass source tiles
#
#
# No:
#
#     water
#     fertilizer
#     get_companion()
#     dynamic planning
#
# ============================================================


TARGET = 200000000

WARMUP = 10

SYNC_DELAY = 5

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
# SOURCE TILE
# ============================================================

def is_source(
	x,
	y
):

	return (
		(x + y) % 2
		== PHASE
	)


# ============================================================
# AFFORDABILITY
# ============================================================

def can_afford(
	entity
):

	cost = get_cost(
		entity
	)


	for item in cost:

		if num_items(
			item
		) < cost[item]:

			return False


	return True


# ============================================================
# PREFERRED STATIC COMPANION
# ============================================================
#
# Spread Bush / Tree / Carrot evenly across the companion
# half of the checkerboard.
#
# Trees can never be orthogonally adjacent because every
# companion occupies the same checkerboard parity.
# ============================================================

def preferred_companion(
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
# CHOOSE AFFORDABLE COMPANION
# ============================================================
#
# The benchmark survived occasional failed Carrot plants and
# still produced ~360M/min.
#
# For the real run we do better:
#
#     preferred crop
#         ↓
#     first fallback
#         ↓
#     second fallback
#
# This maximizes occupied companion tiles even if one crop is
# expensive at the current upgrade level.
# ============================================================

def choose_companion(
	x,
	y
):

	preferred = preferred_companion(
		x,
		y
	)


	if can_afford(
		preferred
	):

		return preferred


	# --------------------------------------------------------
	# PREFERRED CARROT
	# --------------------------------------------------------

	if preferred == Entities.Carrot:

		if can_afford(
			Entities.Bush
		):

			return Entities.Bush


		if can_afford(
			Entities.Tree
		):

			return Entities.Tree


	# --------------------------------------------------------
	# PREFERRED TREE
	# --------------------------------------------------------

	elif preferred == Entities.Tree:

		if can_afford(
			Entities.Bush
		):

			return Entities.Bush


		if can_afford(
			Entities.Carrot
		):

			return Entities.Carrot


	# --------------------------------------------------------
	# PREFERRED BUSH
	# --------------------------------------------------------

	else:

		if can_afford(
			Entities.Tree
		):

			return Entities.Tree


		if can_afford(
			Entities.Carrot
		):

			return Entities.Carrot


	return None


# ============================================================
# PLANT ONE COMPANION
# ============================================================

def prepare_companion(
	x,
	y
):

	go_to(
		x,
		y
	)


	entity = choose_companion(
		x,
		y
	)


	if entity == None:

		return False


	current = get_entity_type()


	# --------------------------------------------------------
	# REMOVE GRASS
	# --------------------------------------------------------

	if current != None:

		harvest()


	# --------------------------------------------------------
	# CARROT GROUND
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
# PREPARE FIELD
# ============================================================
#
# clear() gives us a fresh Grass field.
#
# Leave PHASE parity untouched as Grass.
#
# Replace every opposite-parity tile with a static companion.
# ============================================================

def prepare_field():

	clear()


	size = get_world_size()


	success = 0

	failed = 0


	for y in range(
		size
	):

		for x in range(
			size
		):

			if not is_source(
				x,
				y
			):

				if prepare_companion(
					x,
					y
				):

					success = (
						success + 1
					)

				else:

					failed = (
						failed + 1
					)


	quick_print(
		"[HAY]",
		"field ready",
		"companions:",
		success,
		"failed:",
		failed
	)


# ============================================================
# ROW WORKER
# ============================================================
#
# Every worker:
#
#     owns one row
#     owns 16 Grass tiles
#     moves two tiles between sources
#
#
# All workers use absolute timestamps established before
# spawning.
#
# Sequence:
#
#     position
#     ↓
#     start barrier
#     ↓
#     10-second warmup
#     ↓
#     quiet barrier
#     ↓
#     snapshot Hay
#     ↓
#     final go barrier
#     ↓
#     gather +200M Hay
#
#
# The quiet period ensures no worker is harvesting while the
# shared baseline inventory is sampled.
# ============================================================

def row_worker(
	row,
	start_at,
	warm_end,
	sample_at,
	go_at
):

	size = get_world_size()


	start_x = (
		PHASE - row
	) % 2


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
	#
	# Run long enough that the specially-created initial Grass
	# generation has been harvested several times.
	#
	# The achievement window therefore measures the proven
	# steady-state behavior.

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
	# QUIET BARRIER
	# ========================================================
	#
	# No harvesting occurs here.
	#
	# This gives every drone time to finish any operation that
	# crossed the warm_end boundary.

	while get_time() < sample_at:

		pass


	# ========================================================
	# SHARED INVENTORY BASELINE
	# ========================================================
	#
	# Every drone has its own memory, but inventory is shared.
	#
	# Since nobody harvests during this interval, every worker
	# observes the same Hay count.

	start_hay = num_items(
		Items.Hay
	)


	target_hay = (
		start_hay
		+ TARGET
	)


	# ========================================================
	# FINAL GO BARRIER
	# ========================================================

	while get_time() < go_at:

		pass


	# ========================================================
	# MEASURED RUN
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
# MAIN
# ============================================================

quick_print(
	""
)

quick_print(
	"<<< HAY_RUN_BEGIN >>>"
)

quick_print(
	"[HAY]",
	"preparing fixed companion farm"
)


prepare_field()


size = get_world_size()


quick_print(
	"[HAY]",
	"world:",
	size,
	"x",
	size,
	"drones:",
	max_drones()
)


if size != 32:

	quick_print(
		"[HAY WARNING]",
		"benchmark was validated at 32x32"
	)


if max_drones() != 32:

	quick_print(
		"[HAY WARNING]",
		"benchmark was validated with 32 drones"
	)


# ============================================================
# ABSOLUTE TIMELINE
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
# SPAWN CHILDREN
# ============================================================
#
# 31 children + coordinator = 32 total drones.
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
	"[HAY]",
	"workers:",
	len(handles) + 1
)


# ============================================================
# COORDINATOR BECOMES ROW ZERO
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
# JOIN CHILDREN
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
	"[HAY]",
	"200M window:",
	elapsed,
	"seconds"
)


quick_print(
	"[HAY]",
	"equivalent Hay/min:",
	(
		TARGET
		* 60
		/ elapsed
	)
)


if elapsed <= 60:

	quick_print(
		"[HAY]",
		"PASS"
	)

else:

	quick_print(
		"[HAY]",
		"MISS"
	)


quick_print(
	"<<< HAY_RUN_END >>>"
)


print(
	"HAY RUN COMPLETE\n",
	"Open output.txt"
)
