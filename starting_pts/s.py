heights = 'heights [67'
yaw     = 'yaw [0'
types     = 'types [0'
for _ in range(19):
	heights += ', 67'
	yaw     += ', 0'
	types     += ', 0'
heights += ', 67]'
yaw += ', 0]'
types += ', 0]'
print(heights)
print(yaw)

with open('x5.txt', 'a') as f:
	f.write('\n')
	f.write(heights)
	f.write('\n')
	f.write(yaw)
	f.write('\n')
	f.write(types)
