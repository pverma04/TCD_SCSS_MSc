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

    print("Reward:", reward)
    print("Old Q-value:", current_q)
    print("New Q-value:", new_q)

    #new state for next
    discrete_state = next_discrete_state

    total_reward += reward
    episode_over = terminated or truncated

print("Episode reward:", total_reward)

env.close()