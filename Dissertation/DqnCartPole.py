import gymnasium as gym
import numpy as np
import torch
import torch.nn as nn
import random
from collections import deque
import copy
import matplotlib.pyplot as plt

#Q network instead of Qtable
# FIXED: input = 4 state values (position, velocity, angle, angular velocity)
# output = 2 Q-values (one per action)
class QNetwork(nn.Module):
    def __init__(self, n_inputs = 4, n_actions = 2, hidden = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_inputs, hidden), # layer 1: 4 -> 64 neurons - 64 widely used, use for now
            nn.ReLU(),
            nn.Linear(hidden, hidden), # layer 2: 64 -> 64 neurons
            nn.ReLU(),
            nn.Linear(hidden, n_actions), # output: 64 -> 2 Q-values
        )

    def forward(self, x):
        return self.net(x)

class ReplayBuffer:
    def __init__(self, capacity=50_000):
        self.buffer = deque(maxlen = capacity) # oldest entries drop off when full

    def push(self, state, action, reward, next_state, terminated):
        self.buffer.append((state, action, reward, next_state, terminated))

    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size) # random, no repeats
        states, actions, rewards, next_states, terminateds = zip(*batch)
        return (
            torch.tensor(np.array(states), dtype=torch.float32),
            torch.tensor(actions, dtype=torch.int64),
            torch.tensor(rewards, dtype=torch.float32),
            torch.tensor(np.array(next_states), dtype=torch.float32),
            torch.tensor(terminateds, dtype=torch.float32),
        )
    
    def __len__(self):
        return len(self.buffer)

def choose_action(q_net, state, epsilon, env): # epsilon-greedy action selection
    if np.random.random() < epsilon:
        return env.action_space.sample()    #explore
    with torch.no_grad():
        q_values = q_net(torch.tensor(state, dtype = torch.float32))
    
    return int(q_values.argmax())           #exploit

def train_step(q_net, target_net, optimizer, buffer, batch_size=64, gamma=0.99):
    states, actions, rewards, next_states, terminateds = buffer.sample(batch_size)

    # predicted Q-value of current action taken in current state s
    q_values = q_net(states)                                          # shape [64, 2]
    q_taken = q_values.gather(1, actions.unsqueeze(1)).squeeze(1)     # shape [64]

    # Q-learning target: reward + gamma * best next Q (just reward if pole fell)
    with torch.no_grad():
        next_q = target_net(next_states).max(dim=1).values           # shape [64]
        targets = rewards + gamma * next_q * (1 - terminateds)

    # loss = average squared error between prediction and target
    loss = nn.functional.mse_loss(q_taken, targets)

    # gradient descent: backprop + update the weights
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    return loss.item()

def train_dqn(number_of_episodes = 500, seed = 0):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    env = gym.make("CartPole-v1")
    env.action_space.seed(seed)

    q_net = QNetwork()
    target_net = QNetwork()
    target_net.load_state_dict(q_net.state_dict())
    optimizer = torch.optim.Adam(q_net.parameters(), lr = 1e-3)
    buffer = ReplayBuffer()

    batch_size = 64
    warmup_steps = 1000       # collect this many steps before training starts
    target_sync_every = 500   # env steps between target-network syncs
    epsilon_min = 0.05

    episode_rewards = []
    total_steps = 0
    best_score = -np.inf
    best_weights = copy.deepcopy(q_net.state_dict())

    for episode in range(number_of_episodes):
        state, info = env.reset(seed=seed if episode == 0 else None)
        epsilon = max(epsilon_min, 1.0 - episode / (0.2 * number_of_episodes))
        total_reward = 0
        episode_over = False

        while not episode_over:
            # act and store the experience
            action = choose_action(q_net, state, epsilon, env)
            next_state, reward, terminated, truncated, info = env.step(action)
            buffer.push(state, action, reward, next_state, terminated)

            # learn from a random batch (once the buffer has enough)
            if len(buffer) >= warmup_steps:
                train_step(q_net, target_net, optimizer, buffer, batch_size)

            # sync the target network every N steps
            total_steps += 1
            if total_steps % target_sync_every == 0:
                target_net.load_state_dict(q_net.state_dict())

            state = next_state
            total_reward += reward
            episode_over = terminated or truncated

        episode_rewards.append(total_reward)
        if (episode + 1) % 20 == 0:
            score, _ = evaluate(q_net, n_episodes=10, seed=20_000) #greedy checkpoint
            if score > best_score:
                best_score = score
                best_weights = copy.deepcopy(q_net.state_dict())
            print(f"Episode {episode + 1}: avg reward (last 20) = "
                  f"{np.mean(episode_rewards[-20:]):.1f}, greedy check = {score:.1f}")

    env.close()
    best_net = QNetwork()
    best_net.load_state_dict(best_weights)
    return episode_rewards, best_net, best_score

def evaluate(q_net, n_episodes = 100, seed = 10_000):
    env = gym.make("CartPole-v1")
    rewards = []
    for i in range(n_episodes):
        state, info = env.reset(seed=seed + i)
        total_reward = 0
        episode_over = False
        while not episode_over:
            action = choose_action(q_net, state, 0.0, env)
            state, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            episode_over = terminated or truncated
        rewards.append(total_reward)
    env.close()
    return np.mean(rewards), np.std(rewards)
#----------------TEST CODE----------------
rewards, best_net, best_score = train_dqn(500, seed=0)
eval_mean, eval_std = evaluate(best_net)
print(f"\nBest checkpoint score (10-episode check): {best_score:.1f}")
print(f"Greedy eval of best network (100 episodes): {eval_mean:.1f} ± {eval_std:.1f}")

#----------------REWARD PLOTS-----------------
window = 20
rolling = np.convolve(rewards, np.ones(window) / window, mode='valid')
x = np.arange(window, window + len(rolling))

plt.plot(rewards, alpha=0.3, label="Episode reward")
plt.plot(x, rolling, label=f"{window}-episode rolling average")
plt.xlabel("Training episode")
plt.ylabel("Reward")
plt.title("CartPole DQN progress (seed 0)")
plt.ylim(0, 510)
plt.legend()
plt.grid(True)
plt.show()