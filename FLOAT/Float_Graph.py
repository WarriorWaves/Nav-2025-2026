import matplotlib.pyplot as plt

time = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
# Depth values (to be changed obvs)
depth = [0, -1.02, -2.43, -2.52, -2.56, -2.57, -2.48, -1.94, -1.03, -0.17, 0]

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(time, depth, marker='o', color='blue', linewidth=2)
ax.set_title("Depth of a float over time", fontsize=20, pad=20)

ax.set_xlim(0, 100)
ax.set_xticks([0, 20, 40, 60, 80, 100])
ax.set_xlabel("Seconds", fontsize=12, labelpad=10, loc='center')

ax.set_ylim(-3, 0)
ax.set_yticks([0, -0.5, -1, -1.5, -2, -2.5, -3])
ax.set_ylabel("Depth (in meters)", fontsize=12, labelpad=20, rotation=90, va='center')

ax.grid(True, which='both', linestyle='--', linewidth=0.5)

plt.tight_layout()
plt.show()