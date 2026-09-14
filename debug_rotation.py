import farm_config
import farm_rotation


# ============================================================
# VISUAL DEBUG HARNESS
# ============================================================
#
# Run THIS file manually when you want to watch the farm logic
# closely.
#
# It does NOT permanently change your actual 12x12 world.
#
# Debug 2 changes are temporary and disappear when execution
# stops.
# ============================================================


# ------------------------------------------------------------
# DEBUG SETTINGS
# ------------------------------------------------------------

DEBUG_WORLD_SIZE = 6

# 1.0 = normal base drone speed
# 0.5 = half base speed
# 2.0 = twice base speed
#
# I recommend 1.0 first; 0.5 is useful when debugging
# Polyculture or cactus swaps.
DEBUG_SPEED = 1.0


# ============================================================
# APPLY DEBUG ENVIRONMENT
# ============================================================

set_world_size(
	DEBUG_WORLD_SIZE
)

set_execution_speed(
	DEBUG_SPEED
)


# The continuous Wood / Hay gain targets are sized for a 32x32
# farm and can't be reached on a tiny debug world, so cap each
# phase at a short watchable window instead.

farm_config.SETTINGS["continuous_phase_max_seconds"] = 20


quick_print(
	"[DEBUG]",
	"world:",
	get_world_size(),
	"x",
	get_world_size(),
	"max drones:",
	max_drones()
)


# ============================================================
# RUN EXACTLY ONE NORMAL ROTATION
# ============================================================
#
# Wood (continuous, capped above)
# Hay (continuous, capped above)
# Carrots
# Sunflowers
# Pumpkins
# Cactus
#
# The script exits afterward, which automatically restores:
#
#   - full world size
#   - maximum execution speed

farm_rotation.run_cycle()


quick_print(
	"[DEBUG]",
	"rotation complete"
)
