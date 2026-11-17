import gymnasium as gym
import numpy as np
import torch
import torch.nn as nn
import random
from collections import deque

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


#----------------TEST CODE----------------
env = gym.make("CartPole-v1")
buffer = ReplayBuffer()
q_net = QNetwork()
optimizer = torch.optim.Adam(q_net.parameters(), lr=1e-3)

state, info = env.reset(seed=0)
test_state = state.copy()             # a fixed state to watch Q-values change
for _ in range(200):
    action = env.action_space.sample()
    next_state, reward, terminated, truncated, info = env.step(action)
    buffer.push(state, action, reward, next_state, terminated)
    state = next_state
    if terminated or truncated:
        state, info = env.reset()
env.close()

with torch.no_grad():
    print("Q-values before:", q_net(torch.tensor(test_state, dtype=torch.float32)))

for update in range(1, 501):
    loss = train_step(q_net, q_net, optimizer, buffer)    # naive: same net as target
    if update % 100 == 0:
        print(f"Update {update}: loss = {loss:.4f}")

with torch.no_grad():
    print("Q-values after: ", q_net(torch.tensor(test_state, dtype=torch.float32)))