import farm_config


# ============================================================
# SHARED STATE
# ============================================================

STATE = {
	"hat": None
}


# ============================================================
# CLEAR / HAT STATE
# ============================================================

def reset_hat_after_clear():

	STATE["hat"] = Hats.Straw_Hat


def clear_field():

	clear()

	reset_hat_after_clear()


# ============================================================
# HATS
# ============================================================

def wear_hat(hat):
	# Some Hats.* values exist before the hat is unlocked.
	#
	# Never allow a cosmetic hat to crash the program.

	if num_unlocked(hat) == 0:

		return False


	if STATE["hat"] != hat:

		change_hat(
			hat
		)

		STATE["hat"] = hat


	return True


def wear_crop_hat(entity):

	if entity not in farm_config.HAT_ENABLED:

		return


	if not farm_config.HAT_ENABLED[entity]:

		return


	if entity in farm_config.CROP_HATS:

		wear_hat(
			farm_config.CROP_HATS[
				entity
			]
		)


# ============================================================
# MOVEMENT
# ============================================================

def go_to(
	x,
	y
):
	# Normal farm movement wraps around.
	#
	# Always take the shorter wraparound direction.

	size = get_world_size()


	# --------------------------------------------------------
	# X AXIS
	# --------------------------------------------------------

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


	# --------------------------------------------------------
	# Y AXIS
	# --------------------------------------------------------

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
# COSTS
# ============================================================

def can_afford(
	entity,
	count
):
	# Query the live cost instead of hard-coding crop costs.
	#
	# This automatically adapts as upgrades increase costs.

	cost = get_cost(
		entity
	)


	if cost == None:

		return True


	for item in cost:

		required = (
			cost[item]
			* count
		)


		if num_items(item) < required:

			return False


	return True


def plant_if_affordable(
	entity
):

	if not can_afford(
		entity,
		1
	):

		return False


	return plant(
		entity
	)


# ============================================================
# PARALLEL-SAFE SHARED ITEM CHECK
# ============================================================

def shared_item_available(
	item
):
	# Inventory is shared by all drones.
	#
	# Example race with two drones:
	#
	#     Drone A sees 1 fertilizer.
	#     Drone B sees 1 fertilizer.
	#
	#     A consumes it.
	#     B attempts to consume it -> warning.
	#
	#
	# Require at least one item for every currently-active
	# drone before allowing another use.
	#
	# This may leave a tiny reserve while Megafarm is active,
	# but avoids noisy failed-use races.
	#
	# With one active drone, the final item can still be used.

	active_drones = num_drones()


	if active_drones < 1:

		active_drones = 1


	return (
		num_items(item)
		>= active_drones
	)


# ============================================================
# FREE HAY AFTER clear()
# ============================================================

def harvest_reset_grass():

	if get_entity_type() == Entities.Grass:

		harvest()


# ============================================================
# WATER
# ============================================================

def water_if_needed():
	# Water is also a shared inventory item, so protect it from
	# the same depletion race as Fertilizer.

	if get_water() < farm_config.SETTINGS["water_level"]:

		if shared_item_available(
			Items.Water
		):

			use_item(
				Items.Water
			)


# ============================================================
# FERTILIZER
# ============================================================

def fertilizer_enabled(
	entity
):

	if entity not in farm_config.FERTILIZE:

		return False


	return farm_config.FERTILIZE[
		entity
	]


def fertilize_if_enabled(
	entity
):
	# Fertilizer removes 2 seconds of remaining growth per use.
	#
	# Since we're already standing on the plant, continue using
	# fertilizer while:
	#
	#     - the plant is immature
	#     - fertilizer remains safely available
	#
	# The shared-item guard prevents the Megafarm warning that
	# occurred when multiple drones depleted the inventory at
	# the same moment.

	if not fertilizer_enabled(
		entity
	):

		return


	while not can_harvest():

		if not shared_item_available(
			Items.Fertilizer
		):

			return


		if not use_item(
			Items.Fertilizer
		):

			return


# ============================================================
# GROWTH BOOST
# ============================================================

def boost_growth(
	entity
):
	# Water first, then accelerate with fertilizer.

	if not can_harvest():

		water_if_needed()


	fertilize_if_enabled(
		entity
	)


# ============================================================
# GROUND
# ============================================================

def make_soil():

	if get_ground_type() != Grounds.Soil:

		till()


def make_grassland():

	if get_ground_type() != Grounds.Grassland:

		till()


# ============================================================
# TIMING
# ============================================================

def timing_start():

	return (
		get_time(),
		get_tick_count()
	)


def timing_end(
	label,
	start
):

	if not farm_config.SETTINGS["timing_enabled"]:

		return


	elapsed_time = (
		get_time()
		- start[0]
	)

	elapsed_ticks = (
		get_tick_count()
		- start[1]
	)


	quick_print(
		"[TIMING]",
		label,
		"time:",
		elapsed_time,
		"coordinator ticks:",
		elapsed_ticks
	)