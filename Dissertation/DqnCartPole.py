import gymnasium as gym
import numpy as np
import torch
import torch.nn as nn

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

# quick test: feed one CartPole state through an untrained network
env = gym.make("CartPole-v1")
state, info = env.reset(seed=0)

q_net = QNetwork()
q_values = q_net(torch.tensor(state, dtype=torch.float32))

print("State:", state)
print("Q-values:", q_values)
print("Best action:", int(q_values.argmax()))