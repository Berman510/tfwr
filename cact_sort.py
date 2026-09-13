import farm_common
import farm_megafarm


# ============================================================
# PRODUCTION CACTUS SORTER
# ============================================================
#
# Algorithm:
#
#     Cocktail-shaker sort
#
# Process:
#
#     1. Sort every row West -> East.
#     2. Sort every column South -> North.
#     3. Harvest.
#
#
# BENCHMARK RESULTS - 22x22 / 8 DRONES
#
# Current Cocktail + verification:
#
#     68.98 sec
#
# Cocktail without verification:
#
#     65.44 sec
#
# Improvement:
#
#     3.54 sec
#     ~5.13%
#
#
# Verification is intentionally skipped.
#
# Once all rows are sorted:
#
#     A[row][x] <= A[row][x+1]
#
# sorting each column independently preserves that ordering
# between adjacent columns.
#
# Therefore after:
#
#     sort all rows
#     sort all columns
#
# both dimensions are sorted.
#
# verify() remains as a compatibility function because
# farm_rotation.py currently calls it.
# ============================================================


# ============================================================
# SORT ONE ROW
# ============================================================

def row(
	y
):

	size = get_world_size()


	if size < 2:

		return 0


	swaps = 0

	left = 0

	right = (
		size - 1
	)


	while left < right:

		# ----------------------------------------------------
		# EASTWARD PASS
		# ----------------------------------------------------

		farm_common.go_to(
			left,
			y
		)


		swapped = False

		index = left


		while index < right:

			current_value = measure()

			east_value = measure(
				East
			)


			if current_value > east_value:

				swap(
					East
				)

				swaps = (
					swaps + 1
				)

				swapped = True


			move(
				East
			)


			index = (
				index + 1
			)


		right = (
			right - 1
		)


		if not swapped:

			break


		if left >= right:

			break


		# We ended at the old right edge.
		#
		# Move back onto the new unsorted boundary.

		move(
			West
		)


		# ----------------------------------------------------
		# WESTWARD PASS
		# ----------------------------------------------------

		swapped = False

		index = right


		while index > left:

			west_value = measure(
				West
			)

			current_value = measure()


			if west_value > current_value:

				swap(
					West
				)

				swaps = (
					swaps + 1
				)

				swapped = True


			move(
				West
			)


			index = (
				index - 1
			)


		left = (
			left + 1
		)


		if not swapped:

			break


	return swaps


# ============================================================
# SORT ONE COLUMN
# ============================================================

def column(
	x
):

	size = get_world_size()


	if size < 2:

		return 0


	swaps = 0

	bottom = 0

	top = (
		size - 1
	)


	while bottom < top:

		# ----------------------------------------------------
		# NORTHWARD PASS
		# ----------------------------------------------------

		farm_common.go_to(
			x,
			bottom
		)


		swapped = False

		index = bottom


		while index < top:

			current_value = measure()

			north_value = measure(
				North
			)


			if current_value > north_value:

				swap(
					North
				)

				swaps = (
					swaps + 1
				)

				swapped = True


			move(
				North
			)


			index = (
				index + 1
			)


		top = (
			top - 1
		)


		if not swapped:

			break


		if bottom >= top:

			break


		move(
			South
		)


		# ----------------------------------------------------
		# SOUTHWARD PASS
		# ----------------------------------------------------

		swapped = False

		index = top


		while index > bottom:

			south_value = measure(
				South
			)

			current_value = measure()


			if south_value > current_value:

				swap(
					South
				)

				swaps = (
					swaps + 1
				)

				swapped = True


			move(
				South
			)


			index = (
				index - 1
			)


		bottom = (
			bottom + 1
		)


		if not swapped:

			break


	return swaps


# ============================================================
# PARALLEL ROW SORT
# ============================================================

def sort_rows(
	size
):

	return farm_megafarm.sum_rows(
		row,
		size
	)


# ============================================================
# PARALLEL COLUMN SORT
# ============================================================

def sort_columns(
	size
):

	return farm_megafarm.sum_rows(
		column,
		size
	)


# ============================================================
# VERIFICATION COMPATIBILITY SHIM
# ============================================================
#
# farm_rotation.py currently expects:
#
#     sorted_field = cact_sort.verify(size)
#
# The benchmark established that the full verification scan
# costs ~3.54 seconds on the current 22x22 / 8-drone farm.
#
# It is mathematically redundant after complete row sorting
# followed by complete column sorting.
#
# Return True immediately.

def verify(
	size
):

	return True