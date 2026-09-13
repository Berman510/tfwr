import farm_rotation
import farm_telemetry


# ============================================================
# NORMAL ROTATION BENCHMARK
# ============================================================
#
# Profiles exactly one:
#
#   Trees / Hay
#   Carrots
#   Sunflowers
#   Pumpkins
#   Cactus
#
#
# Does NOT run:
#
#   Auto Unlocks
#   Mazes
#   Dinosaurs
#
#
# REPORT LOCATION:
#
#     output.txt
#
# in this save / VSCode workspace.
# ============================================================


farm_telemetry.start_session(
	"NORMAL CROP ROTATION"
)


farm_rotation.run_cycle()


farm_telemetry.end_session()


farm_telemetry.report()


# The benchmark time has already been captured.
#
# This one-second smoke print happens afterward, so it does
# not affect the measurements.

print(
	"PROFILE COMPLETE\n",
	"Open output.txt"
)