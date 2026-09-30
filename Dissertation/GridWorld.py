import numpy as np
import string

class GridWorld:
    def __init__(self, rows=5, cols=4, start_state=(1, 1), goal_state=(3, 2)):
        #top left corner 0, 0
        self.rows = rows
        self.cols = cols
        self.start_state = start_state
        self.goal_state = goal_state
        self.state = start_state
        #north, south, east west
        #moving n/s changes row value (n lowers, s increases), e/w changes column (e increases, w lowers)
        self.moves=[(-1, 0), (1, 0), (0, 1), (0, -1)]  # Up, Down, Left, Right
        self.moves__names = ['N', 'S', 'E', 'W']

    def reset(self):
        self.state = self.start_state
        return self.state
    #action will take numbers, for moves array indices: N: 0, S: 1, E: 2, W: 3
    def step(self, action):
        dr, dc = self.moves[action] #delta row/column takes (dr, dc) from moves array
        curr_r, curr_c = self.state
        new_r, new_c = curr_r + dr, curr_c + dc
        #check if new state within bounds, else do not update
        if 0 <= new_r < self.rows and 0 <= new_c < self.cols:
            self.state = (new_r, new_c)

        reward = 10 if self.state == self.goal_state else -1
        done = self.state == self.goal_state
        return self.state, reward, done

    def render(self):
        grid = np.zeros((self.rows, self.cols))
        grid[self.goal_state] = 2  # Mark the goal state
        grid[self.state] = 1       # Mark the current state
        print(grid)

    def state_to_index(self, state):
        #curr r * cols + curr c
        return state[0] * self.cols + state[1]

#NOT in gridworld, as this involves Q (out of scope)
#depending on epsilon, chooses an action
def choose_action(Q, s, epsilon, num_acts):
    #explore random actions
    #picks a random index 0-num_acts-1 picking a NESW action
    if np.random.rand() < epsilon:
        return np.random.choice(num_acts) 
    #exploit the best action we have so far
    else:
        return np.argmax(Q[s])

def update_Q(Q, s, a, r, s_next, alpha, gamma):
    best_next_action = np.argmax(Q[s_next])
    #temp difference target = reward + discounted(gamma) future reward
    td_target = r + gamma * Q[s_next][best_next_action]
    td_error = td_target - Q[s][a]
    Q[s][a] += alpha * td_error

#suggested num_eps=1000, alpha=0.1, gamma=0.9, epsilon=0.1, max_steps=100
def train(env, num_eps, alpha, gamma, epsilon, max_steps):
    num_states = env.rows * env.cols
    num_actions = len(env.moves)
    Q = np.zeros((num_states, num_actions))

    for ep in range(num_eps):
        state = env.reset()
        s = env.state_to_index(state)

        for step in range(max_steps):
            a = choose_action(Q, s, epsilon, num_actions)
            next_state, r, done = env.step(a)
            s_next = env.state_to_index(next_state)

            update_Q(Q, s, a, r, s_next, alpha, gamma)

            s = s_next

            if done:
                break

    return Q


env = GridWorld()

num_states = env.rows * env.cols
num_actions = len(env.moves)
#each state has a row, and each action has a column. Ex: F: -1, -1, -1, -1 for NESW moves from F
Q = np.zeros((num_states, num_actions))

#print(Q)

#testing starting w same start point F
s = env.state_to_index((1, 1))
#force exploitation
print(choose_action(Q, s, epsilon=0.0, num_acts=num_actions)) #should print 0 since we only have 0 in Q
#force exploration
print(choose_action(Q, s, epsilon=1.0, num_acts=num_actions)) #should choose random 0-3

alpha, gamma = 1.0, 1.0
#start w F
s = env.state_to_index((1, 1))
#select going south
a = 1       
#to J                          
s_next = env.state_to_index((2, 1))  # J = 9
r = -1

update_Q(Q, s, a, r, s_next, alpha, gamma)
#should be -1.0
print(Q[s, a])

#check alpha
Q2 = np.zeros((20, 4))
update_Q(Q2, s, a, r, s_next, alpha=0.5, gamma=1.0)
print(Q2[s, a])   # should print -0.5, half the full update

#check training
Q_trained = train(env, num_eps=1000, alpha=0.1, gamma=0.9, epsilon=0.1, max_steps=100)

#make letter list for readability
letters = string.ascii_uppercase[:len(Q_trained)]

#print each array w ccorresponding state letter
for s in range(len(Q_trained)):
    print(f"{letters[s]}: {Q_trained[s]}")

policy = np.argmax(Q_trained, axis=1)
action_symbols = ['N', 'S', 'E', 'W']

for r in range(env.rows):
    row_str = ""
    for c in range(env.cols):
        s = env.state_to_index((r, c))
        label = letters[s]
        if (r, c) == env.goal_state:
            row_str += f" {label}:G "
        else:
            row_str += f" {label}:{action_symbols[policy[s]]} "
    print(row_str)

#--------------TEST BASIC ENV------------------
#print(env.reset())
#print(env.step(1))
#print(env.step(1))
#test bounds
#print(env.step(0))
#print(env.step(0))
#print(env.step(0))

#test given path to goal
#state = env.reset()
#print("Start:", state)

#state, reward, done = env.step(1)
# print("F->J:", state, reward, done)
# 
# state, reward, done = env.step(1)
# print("J->N:", state, reward, done)
# 
#state, reward, done = env.step(2)
# print("N->O:", state, reward, done)
