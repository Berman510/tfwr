# ============================================================
# FARM CONFIGURATION
# ============================================================


SETTINGS = {

	# --------------------------------------------------------
	# NORMAL FARM
	# --------------------------------------------------------

	"water_level": 0.5,


	# --------------------------------------------------------
	# TIMING
	# --------------------------------------------------------

	"timing_enabled": True,


	# --------------------------------------------------------
	# AUTO UNLOCKS
	# --------------------------------------------------------

	"auto_unlock_enabled": True,

	# Before buying an upgrade, reserve enough resources to
	# run the normal crop rotation.
	#
	# 2.0 means:
	#
	#     keep approximately twice the currently-calculated
	#     planting cost of a normal rotation in reserve.
	#
	# This matters because crop upgrades can also increase
	# planting costs.
	"unlock_farm_reserve_multiplier": 2.0,


	# --------------------------------------------------------
	# MAZES / GOLD
	# --------------------------------------------------------

	"mazes_enabled": True,

	"gold_floor": 100000,


	# --------------------------------------------------------
	# DINOSAURS / BONES
	# --------------------------------------------------------

	"dinosaurs_enabled": True,

	"bone_floor": 100000,

	# Skip ahead along the Hamiltonian cycle toward the next
	# Apple when it is provably safe. False = plain cycle.
	"dinosaur_shortcuts": True,

	# Stop taking shortcuts once the tail covers this fraction
	# of the field, then run the plain cycle. Shortcuts only pay
	# off early, while moves are still expensive.
	"dinosaur_shortcut_max_fill": 0.25
}


# ============================================================
# CROP HATS
# ============================================================

CROP_HATS = {
	Entities.Grass: Hats.Straw_Hat,
	Entities.Tree: Hats.Tree_Hat,
	Entities.Carrot: Hats.Carrot_Hat,
	Entities.Sunflower: Hats.Sunflower_Hat,
	Entities.Pumpkin: Hats.Pumpkin_Hat,
	Entities.Cactus: Hats.Cactus_Hat
}


# All cosmetic crop hats remain disabled.

HAT_ENABLED = {
	Entities.Grass: False,
	Entities.Tree: False,
	Entities.Carrot: False,
	Entities.Sunflower: False,
	Entities.Pumpkin: False,
	Entities.Cactus: False
}


# ============================================================
# FERTILIZER
# ============================================================

FERTILIZE = {
	Entities.Grass: True,
	Entities.Tree: True,
	Entities.Carrot: True,
	Entities.Sunflower: True,
	Entities.Pumpkin: True,
	Entities.Cactus: True
}