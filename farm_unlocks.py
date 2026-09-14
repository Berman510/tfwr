import farm_config
import farm_maze


# ============================================================
# AUTOMATIC UPGRADE MANAGER
# ============================================================
#
# Auto Unlocks gives us:
#
#     unlock(Unlocks.X)
#
# Costs gives us:
#
#     get_cost(Unlocks.X)
#
#
# IMPORTANT:
#
# Upgrade levels do NOT have separate constants.
#
# For example:
#
#     Unlocks.Expand
#
# represents EVERY level of Expand.
#
# Calling:
#
#     unlock(Unlocks.Expand)
#
# purchases the next available Expand level.
#
#
# This manager spends only surplus resources.
#
# Before buying anything, it reserves enough inventory for:
#
#     - normal crop rotation
#     - pumpkin replacement headroom
#     - Gold reserve
#     - Bone reserve
#     - Maze fuel when Gold is low
#     - Dinosaur fuel when Bones are low
#
# ============================================================


# ============================================================
# UPGRADE PRIORITY
# ============================================================
#
# Earlier entries have higher priority.
#
#
# Speed:
#     Helps essentially everything.
#
# Megafarm:
#     More parallel drones.
#
# Expand:
#     Larger full-field harvests.
#
# Fertilizer / Watering:
#     Faster crop production.
#
# Polyculture:
#     Large bonus for eligible crops.
#
# Mazes / Dinosaurs:
#     Improves special-resource production.
#
# Sunflowers:
#     Improves Power production.
#
# Crop upgrades:
#     Improve ordinary yields.
#
#
# Expand appears ONLY ONCE.
#
# If another Expand level is affordable, the next call to
# unlock(Unlocks.Expand) automatically buys that next level.

UPGRADE_PRIORITY = [
	Unlocks.Speed,
	Unlocks.Megafarm,
	Unlocks.Expand,

	Unlocks.Fertilizer,
	Unlocks.Watering,

	Unlocks.Polyculture,

	Unlocks.Mazes,
	Unlocks.Dinosaurs,

	Unlocks.Sunflowers,

	Unlocks.Trees,
	Unlocks.Grass,

	Unlocks.Carrots,
	Unlocks.Pumpkins,
	Unlocks.Cactus
]


# ============================================================
# DICTIONARY HELPERS
# ============================================================

def add_amount(
	values,
	item,
	amount
):

	if item in values:

		values[item] = (
			values[item]
			+ amount
		)

	else:

		values[item] = amount


def set_minimum(
	values,
	item,
	amount
):

	if item not in values:

		values[item] = amount

		return


	if values[item] < amount:

		values[item] = amount


# ============================================================
# ADD ENTITY COST TO OPERATING RESERVE
# ============================================================

def add_entity_cost(
	reserve,
	entity,
	count
):

	cost = get_cost(
		entity
	)


	if cost == None:

		return


	for item in cost:

		add_amount(
			reserve,
			item,
			cost[item] * count
		)


# ============================================================
# NORMAL FARM OPERATING RESERVE
# ============================================================

def build_normal_reserve():
	# Reserve enough resources to run approximately one full
	# normal rotation after automatic research has finished.

	size = get_world_size()

	area = (
		size
		* size
	)


	reserve = {}


	# --------------------------------------------------------
	# TREES
	# --------------------------------------------------------
	#
	# Wood phase: Trees on half the checkerboard.
	# Hay phase: Trees on a third of the companion half.

	tree_count = (
		area // 2
		+ area // 6
	)


	add_entity_cost(
		reserve,
		Entities.Tree,
		tree_count
	)


	# --------------------------------------------------------
	# BUSHES
	# --------------------------------------------------------
	#
	# Wood phase: Bushes on the other half of the checkerboard.
	# Hay phase: Bushes as companions (fallback for the rest).

	add_entity_cost(
		reserve,
		Entities.Bush,
		area
	)


	# --------------------------------------------------------
	# CARROTS
	# --------------------------------------------------------

	add_entity_cost(
		reserve,
		Entities.Carrot,
		area
	)


	# --------------------------------------------------------
	# SUNFLOWERS
	# --------------------------------------------------------

	add_entity_cost(
		reserve,
		Entities.Sunflower,
		area
	)


	# --------------------------------------------------------
	# PUMPKINS
	# --------------------------------------------------------
	#
	# The continuous pumpkin phase replants every block after
	# each harvest, plus dead pumpkins: ~11 fields of plantings
	# per +20M Pumpkins (pumpkin_run: 14,208 for +25M).
	#
	# Reserve 12 complete fields.

	add_entity_cost(
		reserve,
		Entities.Pumpkin,
		area * 12
	)


	# --------------------------------------------------------
	# CACTUS
	# --------------------------------------------------------

	add_entity_cost(
		reserve,
		Entities.Cactus,
		area
	)


	# --------------------------------------------------------
	# MAZE STARTER BUSH
	# --------------------------------------------------------

	add_entity_cost(
		reserve,
		Entities.Bush,
		1
	)


	# --------------------------------------------------------
	# SAFETY MULTIPLIER
	# --------------------------------------------------------

	multiplier = farm_config.SETTINGS[
		"unlock_farm_reserve_multiplier"
	]


	for item in reserve:

		reserve[item] = (
			reserve[item]
			* multiplier
		)


	return reserve


# ============================================================
# SPECIAL-FARM RESERVES
# ============================================================

def add_special_reserves(
	reserve
):

	size = get_world_size()

	area = (
		size
		* size
	)


	# --------------------------------------------------------
	# GOLD FLOOR
	# --------------------------------------------------------
	#
	# Do not let automatic research spend the Gold reserve that
	# the Maze system is explicitly trying to maintain.

	set_minimum(
		reserve,
		Items.Gold,
		farm_config.SETTINGS["gold_floor"]
	)


	# --------------------------------------------------------
	# BONE FLOOR
	# --------------------------------------------------------

	set_minimum(
		reserve,
		Items.Bone,
		farm_config.SETTINGS["bone_floor"]
	)


	# --------------------------------------------------------
	# MAZE FUEL
	# --------------------------------------------------------
	#
	# If we're currently short on Gold, reserve enough
	# Weird Substance for at least one full-size maze.

	if (
		farm_config.SETTINGS["mazes_enabled"]
		and
		num_items(Items.Gold)
		<
		farm_config.SETTINGS["gold_floor"]
	):

		maze_level = num_unlocked(
			Unlocks.Mazes
		)


		if maze_level > 0:

			# One maze per drone for the split method, one full
			# maze for the single method.
			maze_substance = farm_maze.substance_reserve()


			set_minimum(
				reserve,
				Items.Weird_Substance,
				maze_substance
			)


	# --------------------------------------------------------
	# DINOSAUR FUEL
	# --------------------------------------------------------
	#
	# If Bones are below target, reserve enough resources for
	# one board's worth of Apples using the ACTUAL Apple cost.

	if (
		farm_config.SETTINGS["dinosaurs_enabled"]
		and
		num_items(Items.Bone)
		<
		farm_config.SETTINGS["bone_floor"]
	):

		apple_cost = get_cost(
			Entities.Apple
		)


		if apple_cost != None:

			for item in apple_cost:

				add_amount(
					reserve,
					item,
					apple_cost[item] * area
				)


# ============================================================
# COMPLETE OPERATING RESERVE
# ============================================================

def build_reserve():

	reserve = build_normal_reserve()

	add_special_reserves(
		reserve
	)


	return reserve


# ============================================================
# STOCKPILE FLOORS
# ============================================================

def floor_for(
	item
):

	if item == Items.Gold:

		return farm_config.SETTINGS["gold_floor"]


	if item == Items.Bone:

		return farm_config.SETTINGS["bone_floor"]


	return 0


# ============================================================
# CHECK WHETHER AN UPGRADE IS AFFORDABLE
# ============================================================

def can_purchase(
	upgrade,
	reserve
):
	# For an upgradable unlock, get_cost(upgrade) gives us the
	# cost associated with the research-tree button for that
	# unlock.
	#
	# Calling unlock(upgrade) then has exactly the same effect
	# as pressing that button.
	#
	# So:
	#
	#     Unlocks.Expand
	#
	# works for Expand level 1, 2, 3, 4, etc.
	#
	# There is no:
	#
	#     Unlocks.Expand_2

	cost = get_cost(
		upgrade
	)


	# A maxed or otherwise unavailable upgrade may return None.

	if cost == None:

		return False


	if len(cost) == 0:

		return False


	for item in cost:

		reserved = 0


		if item in reserve:

			reserved = reserve[
				item
			]


		# ----------------------------------------------------
		# FLOOR SAVED FOR THIS UPGRADE
		# ----------------------------------------------------
		#
		# gold_floor / bone_floor exist to stockpile for
		# upgrades. When this upgrade costs at least the whole
		# floor, the floor IS the savings for it, so don't
		# reserve it on top. Otherwise a 100M-Gold upgrade
		# with a 100M gold_floor would need 200M Gold.
		#
		# Cheaper upgrades still can't dip into the floor.

		floor = floor_for(
			item
		)


		if (
			floor > 0
			and
			cost[item] >= floor
		):

			reserved = 0


		required = (
			cost[item]
			+ reserved
		)


		if num_items(item) < required:

			return False


	return True


# ============================================================
# TRY ONE UPGRADE
# ============================================================

def try_upgrade(
	upgrade
):

	reserve = build_reserve()


	if not can_purchase(
		upgrade,
		reserve
	):

		return False


	old_level = num_unlocked(
		upgrade
	)


	if unlock(
		upgrade
	):

		new_level = num_unlocked(
			upgrade
		)


		quick_print(
			"[UNLOCK]",
			upgrade,
			"level:",
			old_level,
			"->",
			new_level
		)


		return True


	return False


# ============================================================
# AUTOMATIC UPGRADE PASS
# ============================================================

def manage():
	# Called only from main.py between complete crop rotations.
	#
	# This is important because Expand clears the farm.

	if not farm_config.SETTINGS["auto_unlock_enabled"]:

		return 0


	purchased = 0

	made_progress = True


	# --------------------------------------------------------
	# PURCHASE LOOP
	# --------------------------------------------------------
	#
	# After every successful purchase:
	#
	#     1. Stop scanning.
	#     2. Rebuild all costs/reserves.
	#     3. Restart from highest priority.
	#
	# This matters because an upgrade may change:
	#
	#     - world size
	#     - crop costs
	#     - available drones
	#     - special-resource costs

	while made_progress:

		made_progress = False


		for upgrade in UPGRADE_PRIORITY:

			if try_upgrade(
				upgrade
			):

				purchased = (
					purchased + 1
				)

				made_progress = True

				# Re-evaluate the world from scratch.
				break


	return purchased
