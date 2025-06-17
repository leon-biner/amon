with open("powerct_curve.csv", "r") as f:
	lines = f.readlines()
with open("powerct_curve.csv", "w") as f:
	for line in lines:
		f.write(line.strip().replace(' ', '') + '\n')
