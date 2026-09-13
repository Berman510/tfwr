import farm_config
import farm_dinosaurs


# ============================================================
# DINOSAUR BENCHMARK TARGET
# ============================================================
#
# Run through sim_dino.py.
#
# MODE:
#
#   1 = CYCLE
#       Plain Hamiltonian cycle.
#
#   2 = SHORTCUT 10%
#   3 = SHORTCUT 25%
#   4 = SHORTCUT 50%
#       Safe shortcuts until the tail covers that fraction of
#       the field, then the plain cycle.
#
#
# Unlike the other *_ab targets, this calls the production
# farm_dinosaurs.farm() directly, so the benchmark measures
# exactly what main runs.
#
# Prints one summary line per run so sim_dino's report shows
# that yield is unchanged (full field) and whether the
# emergency fallback ever triggered.
# ============================================================


FILLS = {
	2: 0.10,
	3: 0.25,
	4: 0.50
}


if MODE == 1:

	farm_config.SETTINGS["dinosaur_shortcuts"] = False


else:

	farm_config.SETTINGS["dinosaur_shortcuts"] = True

	farm_config.SETTINGS["dinosaur_shortcut_max_fill"] = FILLS[
		MODE
	]


farm_dinosaurs.farm()


stats = farm_dinosaurs.LAST_RUN

tiles = (
	get_world_size()
	* get_world_size()
)


# 2^(level - 1) x apples^2. The multiplier is only confirmed at
# Dinosaurs level 6 (32).

full_bones = (
	2 ** (
		num_unlocked(Unlocks.Dinosaurs) - 1
	)
	* (tiles - 1)
	* (tiles - 1)
)


bones = num_items(
	Items.Bone
)


quick_print(
	"  apples at switch:",
	stats["apples_at_switch"],
	"| shortcut-phase moves:",
	stats["shortcut_phase_moves"],
	"| shortcut moves:",
	stats["shortcut_moves"],
	"| emergency moves:",
	stats["emergency_moves"],
	"| bones:",
	bones,
	"| full field:",
	bones >= full_bones
)
