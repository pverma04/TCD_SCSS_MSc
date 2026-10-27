import numpy as np
import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

episode_rewards = np.load("mountaincar_rewards.npy")

average_rewards = [
    np.mean(episode_rewards[i:i + 100])
    for i in range(0, len(episode_rewards), 100)
]

episode_numbers = [
    min(i + 100, len(episode_rewards))
    for i in range(0, len(episode_rewards), 100)
]

plt.plot(episode_numbers, average_rewards)
plt.xlabel("Training episode")
plt.ylabel("Average reward per 100 episodes")
plt.title("MountainCar Q-learning progress")
plt.grid(True)
plt.ylim(-205, -100)
plt.savefig("mountaincar_progress.png", dpi=150, bbox_inches="tight")
plt.show()
plt.close("all")