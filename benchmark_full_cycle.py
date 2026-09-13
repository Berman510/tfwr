import farm_maze
import farm_dinosaurs
import farm_rotation
import farm_telemetry


# ============================================================
# FULL SCHEDULER-CYCLE PROFILER
# ============================================================
#
# Profiles:
#
#   Maze batch, IF currently needed
#
#   Dinosaur run, IF currently needed
#
#   Wood (continuous)
#   Hay (continuous)
#   Carrots
#   Sunflowers
#   Pumpkins
#   Cactus
#
#
# Auto Unlocks are intentionally excluded.
#
# That keeps benchmark runs comparable.
# ============================================================


farm_telemetry.start_session(
	"FULL FARM CYCLE"
)


farm_maze.manage()


farm_dinosaurs.manage()


farm_rotation.run_cycle()


farm_telemetry.end_session()


farm_telemetry.report()


# ============================================================
# PERSISTENT SUMMARY
# ============================================================

while True:

	print(
		"FULL PROFILE COMPLETE\n",
		"Total:",
		farm_telemetry.elapsed_time(),
		"sec\n",
		"Bottleneck:",
		farm_telemetry.bottleneck_label(),
		farm_telemetry.bottleneck_time(),
		"sec\n",
		farm_telemetry.bottleneck_share(),
		"%"
	)