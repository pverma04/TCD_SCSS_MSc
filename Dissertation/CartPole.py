import gymnasium as gym
import numpy as np


bins = (6, 12, 12, 12)
#discretization bounds
lower_bounds = np.array([-2.4, -3.0, -0.20944, -3.5])
upper_bounds = np.array([2.4, 3.0, 0.20944, 3.5])

#boundaries
bin_edges = [
    np.linspace(low, high, count + 1)[1:-1]
    for low, high, count in zip(lower_bounds, upper_bounds, bins)
]

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


env = gym.make("CartPole-v1")

state, info = env.reset(seed=42)
discrete_state = discretize(state)

print("Original state:", state)
print("Discrete state:", discrete_state)


number_of_actions = 2

q_table = np.zeros(bins + (number_of_actions,))

#print("Q-table shape:", q_table.shape)
#print("Action values for this state:", q_table[discrete_state])

epsilon = 1.0
alpha = 0.1 #learning rate
gamma = 0.99 #discount factor

#number_of_episodes = 20000
number_of_episodes = 1000
epsilon_min = 0.02

#record total reward from each episode
episode_rewards = []

for episode in range(number_of_episodes):
    #start each with a fresh state
    state, info = env.reset(seed=42 if episode == 0 else None)
    discrete_state = discretize(state)

    #gradually reduce exploration over the first 80% of training
    epsilon = max(
        epsilon_min,
        1.0 - episode / (0.8 * number_of_episodes)
    )

    total_reward = 0
    episode_over = False

    while not episode_over:
        action = choose_action(discrete_state, epsilon)
        #print("Chosen action:", action)

        #apply action.
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

    # Print progress every 500 episodes.
    #if (episode + 1) % 500 == 0:
    if (episode + 1) % 100 == 0:
        average_reward = np.mean(episode_rewards[-100:])

        print(
            f"Episode: {episode + 1}, "
            f"Average reward (last 100): {average_reward:.1f}, "
            f"Epsilon: {epsilon:.3f}"
        )

env.close()

