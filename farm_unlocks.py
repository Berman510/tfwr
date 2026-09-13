import farm_config


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
	# Trees occupy roughly half the checkerboard.

	tree_count = (
		area // 2
	)


	add_entity_cost(
		reserve,
		Entities.Tree,
		tree_count
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
	# Pumpkins can die while the mega-pumpkin is forming.
	#
	# Reserve 3 complete fields to leave lots of repair
	# headroom.

	add_entity_cost(
		reserve,
		Entities.Pumpkin,
		area * 3
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

			maze_substance = (
				size
				* 2 ** (
					maze_level - 1
				)
			)


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