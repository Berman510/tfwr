# ============================================================
# SUNFLOWER SPATIAL ORDERING
# ============================================================
#
# Production strategy:
#
#     Within each equal-petal bucket, order coordinates in a
#     serpentine / snake traversal:
#
#         row 0 -> East
#         row 1 -> West
#         row 2 -> East
#         row 3 -> West
#
# Fixed-seed benchmark:
#
#     Current: 30.01 sec
#     Snake:   25.99 sec
#
#     Improvement: 13.4%
#     Wins: 5 / 5 seeds
#
# ============================================================


# ============================================================
# SORT POINTS IN ONE ROW BY X
# ============================================================

def sort_row(
	points
):

	for i in range(
		1,
		len(points)
	):

		current = points[i]

		current_x = current[0]

		j = (
			i - 1
		)


		while j >= 0:

			if points[j][0] <= current_x:

				break


			points[
				j + 1
			] = points[j]


			j = (
				j - 1
			)


		points[
			j + 1
		] = current


# ============================================================
# SERPENTINE ORDER
# ============================================================

def order(
	points,
	size
):

	rows = []


	for y in range(size):

		rows.append(
			[]
		)


	for point in points:

		rows[
			point[1]
		].append(
			point
		)


	result = []


	for y in range(size):

		row_points = rows[y]


		sort_row(
			row_points
		)


		if y % 2 == 0:

			for point in row_points:

				result.append(
					point
				)


		else:

			index = (
				len(row_points) - 1
			)


			while index >= 0:

				result.append(
					row_points[index]
				)


				index = (
					index - 1
				)


	return result