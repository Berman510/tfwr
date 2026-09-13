# ============================================================
# MASTER ACROBAT RUNNER
# ============================================================
#
# Achievement (Steam schema DO_1000_FLIPS):
#
#     "Do 1000 flips."
#
#     Tracked by the increment-only "flips" stat, so flips add
#     up across runs.
#
#
# do_a_flip() always takes 1 sec and is not affected by speed
# upgrades, so the only way to go faster is more drones.
#
#
# USE_DRONES:
#
#   True  = split TARGET_FLIPS across every free drone
#           (32 drones -> ~33 flips each, ~35 sec)
#
#   False = one drone does every flip (~17.5 min). Use this if
#           the parallel run doesn't unlock the achievement,
#           i.e. flips by spawned drones don't count.
#
#
# Run it in the REAL game, not simulate(): simulated flips
# are unlikely to count toward Steam stats. Stop main first so
# every drone is free.
#
# This file intentionally imports nothing.
# ============================================================


TARGET_FLIPS = 1050

USE_DRONES = True


# ============================================================
# WORKER
# ============================================================

def flip_worker(
	count
):

	for i in range(count):

		do_a_flip()


	return count


# ============================================================
# PLAN
# ============================================================

drones = 1


if USE_DRONES:

	drones = (
		max_drones()
		- num_drones()
		+ 1
	)


	if drones < 1:

		drones = 1


per_drone = (
	(TARGET_FLIPS + drones - 1)
	// drones
)


quick_print(
	""
)

quick_print(
	"<<< ACROBAT_RUN_BEGIN >>>"
)

quick_print(
	"MASTER ACROBAT"
)

quick_print(
	"Target flips:",
	TARGET_FLIPS
)

quick_print(
	"Use drones:",
	USE_DRONES
)

quick_print(
	"Planned drones:",
	drones,
	"| flips per drone:",
	per_drone
)


# ============================================================
# RUN
# ============================================================

start = get_time()

handles = []


for k in range(1, drones):

	handle = spawn_drone(
		flip_worker,
		per_drone
	)


	if handle != None:

		handles.append(
			handle
		)


# If any spawn failed, the coordinator makes up the difference.

own = (
	TARGET_FLIPS
	- per_drone * len(handles)
)


if own < per_drone:

	own = per_drone


quick_print(
	"[ACROBAT] workers:",
	len(handles) + 1,
	"| coordinator flips:",
	own
)


total = flip_worker(
	own
)


for handle in handles:

	total = (
		total
		+ wait_for(handle)
	)


elapsed = (
	get_time()
	- start
)


# ============================================================
# RESULT
# ============================================================

quick_print(
	"[ACROBAT] total flips:",
	total,
	"| seconds:",
	elapsed
)


if total >= 1000:

	quick_print(
		"[ACROBAT] 1000+ flips done - check for the Master Acrobat unlock"
	)

else:

	quick_print(
		"[ACROBAT] fewer than 1000 flips - run again"
	)


quick_print(
	"<<< ACROBAT_RUN_END >>>"
)


print(
	"ACROBAT RUN COMPLETE\n",
	"Flips:",
	total,
	"\n",
	"Open output.txt"
)
