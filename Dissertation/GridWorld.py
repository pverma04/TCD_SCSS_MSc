import numpy as np

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


def choose_action(Q, s, epsilon, num_acts):
    #explore random actions
    if np.random.rand() < epsilon:
        return np.random.choice(num_acts)  
    #exploit the best action we have so far
    else:
        return np.argmax(Q[s])


env = GridWorld()

num_states = env.rows * env.cols
num_actions = len(env.moves)
#each state has a row, and each action has a column. Ex: F: -1, -1, -1, -1 for NESW moves from F
Q = np.zeros((num_states, num_actions))

#print(Q)

#testing starting w same start point F
s = env.state_to_index((1, 1))
#force exploitation
print(choose_action(Q, s, epsilon=0.0, num_acts=num_actions))
#force exploration
print(choose_action(Q, s, epsilon=1.0, num_acts=num_actions))

#--------------TEST------------------
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
