import gymnasium as gym
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import faulthandler
faulthandler.enable()


def discretize(state):
    return tuple(
        int(np.digitize(value, edges))
        for value, edges in zip(state, bin_edges)
    )
def choose_action(discrete_state, epsilon):
    if np.random.random() < epsilon:
        #explore
        return env.action_space.sample()

    #exploit
    action_values = q_table[discrete_state]

    #random select if equal benefit
    best_actions = np.flatnonzero(action_values == action_values.max())
    return int(np.random.choice(best_actions))


env = gym.make("MountainCar-v0")

state, info = env.reset(seed=42)

#print("Original state:", state)
#print("Position:", state[0])
#print("Velocity:", state[1])
#print("Action space:", env.action_space)
#print("Lower bounds:", env.observation_space.low)
#print("Upper bounds:", env.observation_space.high)


#num bins for position and velocity
bins = (20, 20)

#use env's actual observation bounds
lower_bounds = env.observation_space.low
upper_bounds = env.observation_space.high

#bin boundaries
bin_edges = [
    np.linspace(low, high, count + 1)[1:-1]
    for low, high, count in zip(lower_bounds, upper_bounds, bins)
]

discrete_state = discretize(state)

#one Q-value per state-action combination
number_of_actions = env.action_space.n
q_table = np.zeros(bins + (number_of_actions,))

#print("Discrete state:", discrete_state)
#print("Q-table shape:", q_table.shape)
#print("Action values for this state:", q_table[discrete_state])

epsilon = 1.0
alpha = 0.1 #learning rate
gamma = 0.99 #discount factor

number_of_episodes = 1000
epsilon_min = 0.02

episode_rewards = []
episode_successes = []

for episode in range(number_of_episodes):
    #start a fresh episode
    state, info = env.reset(seed=42 if episode == 0 else None)
    discrete_state = discretize(state)

    #gradually reduce exploration
    epsilon = max(
        epsilon_min,
        1.0 - episode / (0.8 * number_of_episodes)
    )

    total_reward = 0
    episode_over = False

    while not episode_over:
        action = choose_action(discrete_state, epsilon)

        #apply action
        next_state, reward, terminated, truncated, info = env.step(action)

        #convert to index
        next_discrete_state = discretize(next_state)

        #current estimate
        current_q = q_table[discrete_state + (action,)]

        #calculate target value
        if terminated:
            target = reward
        else:
            best_next_q = np.max(q_table[next_discrete_state])
            target = reward + gamma * best_next_q

        #move current estimate towards target
        new_q = current_q + alpha * (target - current_q)
        q_table[discrete_state + (action,)] = new_q

        #new state for next
        discrete_state = next_discrete_state

        total_reward += reward
        episode_over = terminated or truncated

    episode_rewards.append(total_reward)
    episode_successes.append(terminated)

    #show progress every 100 episodes
    if (episode + 1) % 100 == 0:
        average_reward = np.mean(episode_rewards[-100:])
        goals_reached = sum(episode_successes[-100:])

        print(
            f"Episode: {episode + 1}, "
            f"Average reward (last 100): {average_reward:.1f}, "
            f"Goals reached (last 100): {goals_reached}, "
            f"Epsilon: {epsilon:.3f}"
        )

env.close()

#display the environment
env = gym.make("MountainCar-v0", render_mode="human")

for episode in range(5):
    state, info = env.reset()
    discrete_state = discretize(state)

    total_reward = 0
    episode_over = False

    while not episode_over:
        #use learned values without exploration
        action = choose_action(discrete_state, epsilon=0.0)

        next_state, reward, terminated, truncated, info = env.step(action)

        discrete_state = discretize(next_state)
        total_reward += reward
        episode_over = terminated or truncated

    print(
        f"Visual episode {episode + 1}: "
        f"reward = {total_reward}, "
        f"reached goal = {terminated}"
    )

env.close()
#reward plot
#average rewards in groups of 100 episodes
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
#plt.show()
plt.close()
#print("Graph saved as mountaincar_progress.png")