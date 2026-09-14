# ============================================================
# FARM TELEMETRY / PROFILER
# ============================================================
#
# Benchmark sessions collect:
#
#   - phase runtime
#   - coordinator ticks
#   - resource deltas
#
#   - sub-phase runtime
#
#   - planned drone utilization
#   - actual observed active drones
#   - available drone capacity
#
#   - algorithm-specific counters / metrics
#
# Child drones have independent module state, so telemetry
# aggregation always happens on the coordinator.
# ============================================================


# ============================================================
# TRACKED RESOURCES
# ============================================================

RESOURCE_ITEMS = [
	Items.Hay,
	Items.Wood,
	Items.Carrot,
	Items.Pumpkin,
	Items.Cactus,
	Items.Power,
	Items.Weird_Substance,
	Items.Gold,
	Items.Bone,
	Items.Water,
	Items.Fertilizer
]


RESOURCE_NAMES = {
	Items.Hay: "Hay",
	Items.Wood: "Wood",
	Items.Carrot: "Carrot",
	Items.Pumpkin: "Pumpkin",
	Items.Cactus: "Cactus",
	Items.Power: "Power",
	Items.Weird_Substance: "Weird Substance",
	Items.Gold: "Gold",
	Items.Bone: "Bone",
	Items.Water: "Water",
	Items.Fertilizer: "Fertilizer"
}


# ============================================================
# STATE
# ============================================================

STATE = {
	"active": False,

	"name": "",

	"start_time": 0,
	"start_ticks": 0,

	"end_time": 0,
	"end_ticks": 0,

	"start_items": {},
	"end_items": {},

	"phases": {},
	"phase_order": [],

	"current_phase": None,

	"subphases": {},
	"subphase_order": [],

	"counters": {},
	"metrics": {}
}


# ============================================================
# INVENTORY SNAPSHOT
# ============================================================

def inventory_snapshot():

	values = {}


	for item in RESOURCE_ITEMS:

		values[item] = num_items(
			item
		)


	return values


# ============================================================
# DRONE STATS
# ============================================================

def new_drone_stats():

	return {
		"operations": 0,

		"capacity": 1,

		"planned_workers": 0,
		"theoretical_workers": 0,

		"peak_active": 1,

		"active_samples": 0,
		"active_sum": 0,

		"full_active_samples": 0,
		"plan_met_samples": 0,

		"full_capacity_operations": 0,
		"work_limited_operations": 0,
		"underfilled_operations": 0,

		"active_below_plan_samples": 0
	}


# ============================================================
# RESET
# ============================================================

def reset():

	STATE["active"] = False

	STATE["name"] = ""

	STATE["start_time"] = 0
	STATE["start_ticks"] = 0

	STATE["end_time"] = 0
	STATE["end_ticks"] = 0

	STATE["start_items"] = {}
	STATE["end_items"] = {}

	STATE["phases"] = {}
	STATE["phase_order"] = []

	STATE["current_phase"] = None

	STATE["subphases"] = {}
	STATE["subphase_order"] = []

	STATE["counters"] = {}
	STATE["metrics"] = {}


# ============================================================
# SESSION START
# ============================================================

def start_session(
	name
):

	reset()


	STATE["active"] = True

	STATE["name"] = name

	STATE["start_items"] = inventory_snapshot()

	STATE["start_time"] = get_time()

	STATE["start_ticks"] = get_tick_count()


# ============================================================
# SESSION END
# ============================================================

def end_session():

	if not STATE["active"]:

		return


	STATE["end_items"] = inventory_snapshot()

	STATE["end_time"] = get_time()

	STATE["end_ticks"] = get_tick_count()

	STATE["current_phase"] = None

	STATE["active"] = False


# ============================================================
# ACTIVE
# ============================================================

def active():

	return STATE["active"]


# ============================================================
# PHASE START
# ============================================================

def phase_start(
	label
):

	if not STATE["active"]:

		return None


	start_active = num_drones()

	capacity = max_drones()


	STATE["phases"][label] = {
		"seconds": 0,
		"ticks": 0,

		"deltas": {},

		"start_active": start_active,
		"end_active": 0,

		"drone_stats": new_drone_stats()
	}


	stats = STATE["phases"][
		label
	]["drone_stats"]


	stats["capacity"] = capacity

	stats["peak_active"] = start_active


	if label not in STATE["phase_order"]:

		STATE["phase_order"].append(
			label
		)


	STATE["current_phase"] = label


	return {
		"time": get_time(),
		"ticks": get_tick_count(),
		"items": inventory_snapshot()
	}


# ============================================================
# PHASE END
# ============================================================

def phase_end(
	label,
	start
):

	if start == None:

		return


	end_items = inventory_snapshot()

	end_time = get_time()

	end_ticks = get_tick_count()


	deltas = {}


	for item in RESOURCE_ITEMS:

		deltas[item] = (
			end_items[item]
			- start["items"][item]
		)


	entry = STATE["phases"][
		label
	]


	entry["seconds"] = (
		end_time
		- start["time"]
	)

	entry["ticks"] = (
		end_ticks
		- start["ticks"]
	)

	entry["deltas"] = deltas

	entry["end_active"] = num_drones()


	if STATE["current_phase"] == label:

		STATE["current_phase"] = None


# ============================================================
# SUB-PHASE START
# ============================================================

def subphase_start(
	label
):

	if not STATE["active"]:

		return None


	if STATE["current_phase"] == None:

		return None


	return {
		"phase": STATE["current_phase"],
		"label": label,
		"time": get_time(),
		"ticks": get_tick_count()
	}


# ============================================================
# SUB-PHASE END
# ============================================================

def subphase_end(
	label,
	start
):

	if start == None:

		return


	phase = start[
		"phase"
	]


	key = (
		phase
		+ " / "
		+ label
	)


	seconds = (
		get_time()
		- start["time"]
	)

	ticks = (
		get_tick_count()
		- start["ticks"]
	)


	if key not in STATE["subphases"]:

		STATE["subphases"][key] = {
			"phase": phase,
			"label": label,
			"seconds": 0,
			"ticks": 0,
			"calls": 0
		}

		STATE["subphase_order"].append(
			key
		)


	entry = STATE["subphases"][
		key
	]


	entry["seconds"] = (
		entry["seconds"]
		+ seconds
	)

	entry["ticks"] = (
		entry["ticks"]
		+ ticks
	)

	entry["calls"] = (
		entry["calls"]
		+ 1
	)


# ============================================================
# DRONE OPERATION
# ============================================================

def record_drone_operation(
	planned_workers,
	work_units,
	active_snapshot
):

	if not STATE["active"]:

		return


	label = STATE["current_phase"]


	if label == None:

		return


	if label not in STATE["phases"]:

		return


	stats = STATE["phases"][
		label
	]["drone_stats"]


	capacity = max_drones()


	theoretical_workers = min(
		capacity,
		work_units
	)


	stats["operations"] = (
		stats["operations"]
		+ 1
	)


	stats["planned_workers"] = (
		stats["planned_workers"]
		+ planned_workers
	)


	stats["theoretical_workers"] = (
		stats["theoretical_workers"]
		+ theoretical_workers
	)


	stats["active_samples"] = (
		stats["active_samples"]
		+ 1
	)

	stats["active_sum"] = (
		stats["active_sum"]
		+ active_snapshot
	)


	if capacity > stats["capacity"]:

		stats["capacity"] = capacity


	if active_snapshot > stats["peak_active"]:

		stats["peak_active"] = active_snapshot


	if active_snapshot >= capacity:

		stats["full_active_samples"] = (
			stats["full_active_samples"]
			+ 1
		)


	if active_snapshot >= planned_workers:

		stats["plan_met_samples"] = (
			stats["plan_met_samples"]
			+ 1
		)


	if theoretical_workers < capacity:

		stats["work_limited_operations"] = (
			stats["work_limited_operations"]
			+ 1
		)


	elif planned_workers >= capacity:

		stats["full_capacity_operations"] = (
			stats["full_capacity_operations"]
			+ 1
		)


	if planned_workers < theoretical_workers:

		stats["underfilled_operations"] = (
			stats["underfilled_operations"]
			+ 1
		)


	if active_snapshot < planned_workers:

		stats["active_below_plan_samples"] = (
			stats["active_below_plan_samples"]
			+ 1
		)


# ============================================================
# COUNTERS
# ============================================================

def add_counter(
	name,
	amount
):

	if not STATE["active"]:

		return


	if name in STATE["counters"]:

		STATE["counters"][name] = (
			STATE["counters"][name]
			+ amount
		)

	else:

		STATE["counters"][name] = amount


# ============================================================
# METRICS
# ============================================================

def set_metric(
	name,
	value
):

	if not STATE["active"]:

		return


	STATE["metrics"][name] = value


def max_metric(
	name,
	value
):

	if not STATE["active"]:

		return


	if name not in STATE["metrics"]:

		STATE["metrics"][name] = value

		return


	if value > STATE["metrics"][name]:

		STATE["metrics"][name] = value


# ============================================================
# ELAPSED
# ============================================================

def elapsed_time():

	if STATE["end_time"] > 0:

		return (
			STATE["end_time"]
			- STATE["start_time"]
		)


	if STATE["start_time"] > 0:

		return (
			get_time()
			- STATE["start_time"]
		)


	return 0


def elapsed_ticks():

	if STATE["end_ticks"] > 0:

		return (
			STATE["end_ticks"]
			- STATE["start_ticks"]
		)


	if STATE["start_ticks"] > 0:

		return (
			get_tick_count()
			- STATE["start_ticks"]
		)


	return 0


# ============================================================
# TOTAL PHASE TIME
# ============================================================

def total_phase_time():

	total = 0


	for label in STATE["phase_order"]:

		total = (
			total
			+ STATE["phases"][label]["seconds"]
		)


	return total


# ============================================================
# RANK PHASES
# ============================================================

def ranked_phases():

	labels = []


	for label in STATE["phase_order"]:

		labels.append(
			label
		)


	for i in range(
		1,
		len(labels)
	):

		current = labels[i]

		current_time = STATE["phases"][
			current
		]["seconds"]


		j = (
			i - 1
		)


		while j >= 0:

			other = labels[j]

			other_time = STATE["phases"][
				other
			]["seconds"]


			if other_time >= current_time:

				break


			labels[
				j + 1
			] = other

			j = (
				j - 1
			)


		labels[
			j + 1
		] = current


	return labels


# ============================================================
# RANK SUB-PHASES
# ============================================================

def ranked_subphases():

	keys = []


	for key in STATE["subphase_order"]:

		keys.append(
			key
		)


	for i in range(
		1,
		len(keys)
	):

		current = keys[i]

		current_time = STATE["subphases"][
			current
		]["seconds"]


		j = (
			i - 1
		)


		while j >= 0:

			other = keys[j]

			other_time = STATE["subphases"][
				other
			]["seconds"]


			if other_time >= current_time:

				break


			keys[
				j + 1
			] = other

			j = (
				j - 1
			)


		keys[
			j + 1
		] = current


	return keys


# ============================================================
# BOTTLENECK
# ============================================================

def bottleneck_label():

	labels = ranked_phases()


	if len(labels) == 0:

		return "none"


	return labels[0]


def bottleneck_time():

	label = bottleneck_label()


	if label == "none":

		return 0


	return STATE["phases"][
		label
	]["seconds"]


def bottleneck_share():

	total = total_phase_time()


	if total <= 0:

		return 0


	return (
		bottleneck_time()
		* 100
		/ total
	)


# ============================================================
# RESOURCE DELTA
# ============================================================

def session_resource_delta(
	item
):

	if item not in STATE["start_items"]:

		return 0


	if item not in STATE["end_items"]:

		return 0


	return (
		STATE["end_items"][item]
		- STATE["start_items"][item]
	)


# ============================================================
# DRONE REPORT
# ============================================================

def report_phase_drones(
	label
):

	entry = STATE["phases"][
		label
	]

	stats = entry[
		"drone_stats"
	]


	quick_print(
		"   DRONES",
		"start:",
		entry["start_active"],
		"end:",
		entry["end_active"],
		"peak:",
		stats["peak_active"],
		"capacity:",
		stats["capacity"]
	)


	if stats["operations"] == 0:

		quick_print(
			"   DRONES",
			"parallel operations: 0",
			"(serial phase or serial section)"
		)

		return


	average_planned = (
		stats["planned_workers"]
		/ stats["operations"]
	)


	average_active = 0


	if stats["active_samples"] > 0:

		average_active = (
			stats["active_sum"]
			/ stats["active_samples"]
		)


	planner_utilization = 0


	if stats["theoretical_workers"] > 0:

		planner_utilization = (
			stats["planned_workers"]
			* 100
			/ stats["theoretical_workers"]
		)


	quick_print(
		"   DRONES",
		"operations:",
		stats["operations"],
		"avg planned:",
		average_planned,
		"avg observed active:",
		average_active
	)


	quick_print(
		"   DRONES",
		"planner utilization:",
		planner_utilization,
		"%",
		"plan-met samples:",
		stats["plan_met_samples"],
		"/",
		stats["active_samples"]
	)


	quick_print(
		"   DRONES",
		"full-active samples:",
		stats["full_active_samples"],
		"/",
		stats["active_samples"]
	)


	quick_print(
		"   DRONES",
		"full-capacity ops:",
		stats["full_capacity_operations"],
		"work-limited ops:",
		stats["work_limited_operations"],
		"underfilled ops:",
		stats["underfilled_operations"]
	)


	quick_print(
		"   DRONES",
		"active-below-plan snapshots:",
		stats["active_below_plan_samples"]
	)


# ============================================================
# REPORT
# ============================================================

def report():

	quick_print(
		""
	)

	quick_print(
		"<<< FARM_PROFILE_BEGIN >>>"
	)

	quick_print(
		"PROFILE:",
		STATE["name"]
	)

	quick_print(
		"Elapsed:",
		elapsed_time(),
		"seconds"
	)

	quick_print(
		"Coordinator ticks:",
		elapsed_ticks()
	)

	quick_print(
		"World:",
		get_world_size(),
		"x",
		get_world_size()
	)

	quick_print(
		"Drone capacity:",
		max_drones()
	)


	# ========================================================
	# PHASE RANKING
	# ========================================================

	quick_print(
		""
	)

	quick_print(
		"=== PHASE RANKING ==="
	)


	labels = ranked_phases()

	total = total_phase_time()


	for index in range(
		len(labels)
	):

		label = labels[index]

		entry = STATE["phases"][
			label
		]

		share = 0


		if total > 0:

			share = (
				entry["seconds"]
				* 100
				/ total
			)


		quick_print(
			index + 1,
			label,
			"time:",
			entry["seconds"],
			"share:",
			share,
			"%",
			"ticks:",
			entry["ticks"]
		)


		report_phase_drones(
			label
		)


		for item in RESOURCE_ITEMS:

			delta = entry["deltas"][
				item
			]


			if delta != 0:

				rate = 0


				if entry["seconds"] > 0:

					rate = (
						delta
						/ entry["seconds"]
					)


				quick_print(
					"   RESOURCE",
					RESOURCE_NAMES[item],
					"delta:",
					delta,
					"rate/s:",
					rate
				)


	# ========================================================
	# SUB-PHASE RANKING
	# ========================================================

	quick_print(
		""
	)

	quick_print(
		"=== SUB-PHASE RANKING ==="
	)


	subphase_keys = ranked_subphases()


	if len(subphase_keys) == 0:

		quick_print(
			"(none)"
		)


	for index in range(
		len(subphase_keys)
	):

		key = subphase_keys[index]

		entry = STATE["subphases"][
			key
		]


		quick_print(
			index + 1,
			key,
			"time:",
			entry["seconds"],
			"ticks:",
			entry["ticks"],
			"calls:",
			entry["calls"]
		)


	# ========================================================
	# BOTTLENECK
	# ========================================================

	quick_print(
		""
	)

	quick_print(
		"=== BOTTLENECK ==="
	)

	quick_print(
		bottleneck_label(),
		bottleneck_time(),
		"seconds",
		bottleneck_share(),
		"% of measured phase time"
	)


	# ========================================================
	# COUNTERS
	# ========================================================

	quick_print(
		""
	)

	quick_print(
		"=== ALGORITHM COUNTERS ==="
	)


	if len(
		STATE["counters"]
	) == 0:

		quick_print(
			"(none)"
		)

	else:

		for name in STATE["counters"]:

			quick_print(
				name,
				STATE["counters"][name]
			)


	# ========================================================
	# METRICS
	# ========================================================

	quick_print(
		""
	)

	quick_print(
		"=== METRICS ==="
	)


	if len(
		STATE["metrics"]
	) == 0:

		quick_print(
			"(none)"
		)

	else:

		for name in STATE["metrics"]:

			quick_print(
				name,
				STATE["metrics"][name]
			)


	# ========================================================
	# SESSION RESOURCE DELTAS
	# ========================================================

	quick_print(
		""
	)

	quick_print(
		"=== SESSION RESOURCE DELTAS ==="
	)


	for item in RESOURCE_ITEMS:

		delta = session_resource_delta(
			item
		)


		if delta != 0:

			rate = 0


			if elapsed_time() > 0:

				rate = (
					delta
					/ elapsed_time()
				)


			quick_print(
				RESOURCE_NAMES[item],
				"delta:",
				delta,
				"rate/s:",
				rate
			)


	quick_print(
		"<<< FARM_PROFILE_END >>>"
	)

	quick_print(
		""
	)
