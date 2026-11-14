import gymnasium as gym
import numpy as np
import matplotlib.pyplot as plt

#Why use discretization? 
    #Cart pole gives 4 cont. measurements, and divide these into bins 
    #to represent states in a finite Qtable
#Q-update?
    #after each action, adjust Q val using reward recieved and estimated future reward
    #alpha controls how much estimate changes
    #gamma controls how much future rewards matter
    #on failure, target is just reward  
#epsilon decrease?
    #early on, try random actions to get an idea
    #later reduce to chose learned best more often (more exploiting)
    #small min to continue exploration as well


#bins = (6, 12, 12, 12)
bins = (1, 1, 6, 12) #or (3, 3, 6, 6)
#discretization bounds
#lower_bounds = np.array([-2.4, -3.0, -0.20944, -3.5])
lower_bounds = [-2.4, -2.0, -0.21, -2.0] #tighter bounds
#upper_bounds = np.array([2.4, 3.0, 0.20944, 3.5])
upper_bounds = [2.4, 2.0, 0.21, 2.0]

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


number_of_actions = 2
gamma = 0.99
epsilon_min = 0.02

#new choose_action, takes q_table as parameter instead of using the last one (was a global variable) 
# allows keeping all 5 runs
def choose_action(q_table, discrete_state, epsilon, env):
    if np.random.random() < epsilon:
        return env.action_space.sample()
    values = q_table[discrete_state]
    best = np.flatnonzero(values == values.max())
    return int(np.random.choice(best))

def train_cartpole(number_of_episodes=5000, seed=0):
    np.random.seed(seed)                  # seeds epsilon checks + tie-breaking in choose_action
    env = gym.make("CartPole-v1")
    env.action_space.seed(seed)           # seeds random exploration actions
    q_table = np.zeros(bins + (number_of_actions,))   # fresh table each run
    episode_rewards = []

    for episode in range(number_of_episodes):
        # seed only the first reset; later resets continue the same random stream
        state, info = env.reset(seed=seed if episode == 0 else None)
        discrete_state = discretize(state)

        epsilon = max(epsilon_min, 1.0 - episode / (0.5 * number_of_episodes))
        alpha = max(0.02, 0.2 * (1 - episode / number_of_episodes))

        total_reward = 0
        episode_over = False

        while not episode_over:
            action = choose_action(q_table, discrete_state, epsilon, env)
            next_state, reward, terminated, truncated, info = env.step(action)
            next_discrete_state = discretize(next_state)

            current_q = q_table[discrete_state + (action,)]
            if terminated:
                target = reward
            else:
                target = reward + gamma * np.max(q_table[next_discrete_state])
            q_table[discrete_state + (action,)] = current_q + alpha * (target - current_q)

            discrete_state = next_discrete_state
            total_reward += reward
            episode_over = terminated or truncated

        episode_rewards.append(total_reward)

    env.close()
    return episode_rewards, q_table

n_runs = 5
all_runs = []
results = []

for run in range(n_runs):
    rewards, q = train_cartpole(5000, seed = run)
    results.append((rewards, q))
    print(f"Finished run {run + 1}/{n_runs}, final 100-episode avg: {np.mean(rewards[-100:]):.1f}")
all_runs = [r[0] for r in results] #reward lists for plotting
best_q = max(results, key=lambda r: np.mean(r[0][-100:]))[1] #best run's Q table

env = gym.make("CartPole-v1", render_mode="human") #new env to displays the cart and pole.


#watch for three eps
for episode in range(3):
    state, info = env.reset()
    discrete_state = discretize(state)

    total_reward = 0
    episode_over = False

    while not episode_over:
        #epsilon=0 means use the learned policy without exploration
        action = choose_action(best_q, discrete_state, epsilon=0.0, env=env)

        next_state, reward, terminated, truncated, info = env.step(action)

        discrete_state = discretize(next_state)
        total_reward += reward
        episode_over = terminated or truncated

    print(f"Visual episode {episode + 1}: reward = {total_reward}")

env.close()

window = 100
rolling_runs = np.array([
    np.convolve(run, np.ones(window) / window, mode='valid')
    for run in all_runs
])

mean = rolling_runs.mean(axis=0)
std = rolling_runs.std(axis=0)
x = np.arange(window, window + len(mean))

plt.plot(x, mean, label=f"Mean of {n_runs} runs")
plt.fill_between(x, mean - std, mean + std, alpha=0.2, label="±1 std")
plt.xlabel("Training episode")
plt.ylabel("Reward (100-episode rolling average)")
plt.title("CartPole Q-learning progress")
plt.legend()
plt.grid(True)
plt.show()