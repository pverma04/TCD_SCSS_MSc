import gymnasium as gym
import numpy as np
import matplotlib.pyplot as plt


#updates
# - episodes 1000 -> 5000
# - epsilon decays to min by 10% of training (was 80%): random actions can't
#   build momentum; zero-initialized Q-table explores via optimism
# - alpha decays 0.1 -> 0.01 to stop late overwrites of a good policy
# - keep best Q-table: greedy check every 250 eps (20 eps, seeds 20000+)
# - no globals; seeded train function; greedy evaluate() on seeds 10000+
# - 5 seeds, mean ± std plot, demo uses best run's table
#
#results (5 seeds, 5000 eps): goal rate 100% all seeds, reward -142.6 ± 4.2

def discretize(state):
    return tuple(
        int(np.digitize(value, edges))
        for value, edges in zip(state, bin_edges)
    )

def choose_action(q_table, discrete_state, epsilon, env):
    if np.random.random() < epsilon:
        return env.action_space.sample() # explore
    values = q_table[discrete_state] # exploit
    best = np.flatnonzero(values == values.max())
    return int(np.random.choice(best)) # random tie-break

def train_mountaincar(number_of_episodes=5000, seed=0):
    np.random.seed(seed)
    env = gym.make("MountainCar-v0")
    env.action_space.seed(seed)
    q_table = np.zeros(bins + (number_of_actions,))   #fresh table each run
    episode_rewards = []
    episode_successes = []

    best_q = q_table.copy()
    best_score = -np.inf
    for episode in range(number_of_episodes):
        state, info = env.reset(seed=seed if episode == 0 else None)
        discrete_state = discretize(state)

        epsilon = max(epsilon_min, 1.0 - episode / (0.1 * number_of_episodes))
        alpha = max(0.01, 0.1 * (1 - episode / number_of_episodes))

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
        episode_successes.append(terminated)
        if (episode + 1) % 250 == 0:
            score, _ = evaluate(q_table, n_episodes = 20, seed = 20000)
            if score > best_score:
                best_score, best_q = score, q_table.copy()

    env.close()
    return episode_rewards, episode_successes, best_q

def evaluate(q_table, n_episodes=100, seed=10_000):
    # test the learned policy: no exploration, no Q-updates
    env = gym.make("MountainCar-v0")
    rewards, successes = [], []
    for i in range(n_episodes):
        state, info = env.reset(seed=seed + i)    #same 100 starts for every table
        discrete_state = discretize(state)
        total_reward = 0
        episode_over = False
        while not episode_over:
            action = choose_action(q_table, discrete_state, 0.0, env)
            state, reward, terminated, truncated, info = env.step(action)
            discrete_state = discretize(state)
            total_reward += reward
            episode_over = terminated or truncated
        rewards.append(total_reward)
        successes.append(terminated)
    env.close()
    return np.mean(rewards), np.mean(successes)

#num bins for position and velocity
bins = (20, 20)

#get bounds + action count from a temporary env, then close it
temp_env = gym.make("MountainCar-v0")
lower_bounds = temp_env.observation_space.low
upper_bounds = temp_env.observation_space.high
number_of_actions = temp_env.action_space.n
temp_env.close()

#bin boundaries
bin_edges = [
    np.linspace(low, high, count + 1)[1:-1]
    for low, high, count in zip(lower_bounds, upper_bounds, bins)
]

gamma = 0.99        #discount factor
epsilon_min = 0.02

#train + evaluate several seeds
n_runs = 5
results = []
for run in range(n_runs):
    rewards, successes, q = train_mountaincar(5000, seed=run)
    eval_reward, eval_goal_rate = evaluate(q)
    results.append((rewards, q, eval_reward, eval_goal_rate))
    print(f"Run {run + 1}/{n_runs} | train goals (last 100): {sum(successes[-100:])} "
          f"| greedy eval: reward {eval_reward:.1f}, goal rate {eval_goal_rate * 100:.0f}%")

all_runs = [r[0] for r in results]
best_q = max(results, key=lambda r: r[2])[1]
eval_rewards = [r[2] for r in results]
eval_rates = [r[3] for r in results]
print(f"\nGreedy eval across runs: reward {np.mean(eval_rewards):.1f} ± {np.std(eval_rewards):.1f}, "
      f"goal rate {np.mean(eval_rates) * 100:.0f}% ± {np.std(eval_rates) * 100:.0f}%")


#display the best run's policy
env = gym.make("MountainCar-v0", render_mode="human")
for episode in range(3):
    state, info = env.reset()
    discrete_state = discretize(state)
    total_reward = 0
    episode_over = False
    while not episode_over:
        action = choose_action(best_q, discrete_state, 0.0, env)
        next_state, reward, terminated, truncated, info = env.step(action)
        discrete_state = discretize(next_state)
        total_reward += reward
        episode_over = terminated or truncated
    print(f"Visual episode {episode + 1}: reward = {total_reward}, reached goal = {terminated}")
env.close()


#reward plot: mean ± std across runs
window = 100
rolling_runs = np.array([
    np.convolve(run, np.ones(window) / window, mode='valid')
    for run in all_runs
])
mean = rolling_runs.mean(axis=0)
std = rolling_runs.std(axis=0)
x = np.arange(window, window + len(mean))

plt.plot(x, mean, label=f"Mean of {n_runs} runs")
plt.fill_between(x, np.clip(mean - std, -200, None), mean + std, alpha=0.2, label="±1 std")
plt.xlabel("Training episode")
plt.ylabel("Reward (100-episode rolling average)")
plt.title("MountainCar Q-learning progress")
plt.ylim(-205, -100)
plt.legend()
plt.grid(True)
plt.show()