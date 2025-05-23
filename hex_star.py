from math import sqrt, pi
from queue import PriorityQueue
from itertools import count
from copy import copy

a_star_weight = 1
counter = count()

# Best first search algorithm
# using g(n) + h(n) for f will make this an A* search
def best_first_search(problem, f, h):
    node = problem.root
    frontier = PriorityQueue(0)

    # Priority queue, elements input as tuple (priority, counter, value), using f(node) for priority
    # Counter is used as the tiebreaker between nodes when they have the same f value
    # Nodes are expanded in order they were added when they have the same priority
    frontier.put((f(node, h), -next(counter), node))
    reached = {problem.root: node}

    while not frontier.empty():
        # Pop from the front of the queue
        node = frontier.get(False)[2]

        if problem.is_goal(node.state):
            return node
        for child in expand(problem, node, h):
            s = child.state
            if s not in reached or child.path_cost < reached[s].path_cost:
                reached[s] = child
                frontier.put((f(child, h), -next(counter), child))
    return None


#bidirectional best first search algorithm
#using g(n) + g(n) for f will make this A* search
#h & h2 are two different heuristic functions that calculate distance to the goal node & start node respectively, this is to account for the different directions of the search and apply different functionality to both directions of the search
def inf_bidirectional_search(problem, f, h, h2):
    #state, frontier, and reached declaraiton
    node_f = problem.Node((problem.root.state[0], (0,0)), None, None, 0, problem)
    node_g = problem.Node((problem.goal_loc, (0,pi)), None, None, 0, problem)
    # Priority queue, elements input as tuple (priority, counter, value), using f(node, h/h2) for priority
    # Counter is used as the tiebreaker between nodes when they have the same f value
    # Nodes are expanded in order they were added when they have the same priority
    frontier_f = PriorityQueue(0)
    frontier_f.put((f(node_f, h), -next(counter), node_f))
    frontier_g = PriorityQueue(0)
    frontier_g.put((f(node_g, h2), -next(counter), node_g))
    #Two reached tables are declared each for both directions, both are updated simultaneously to keep the best value for a given state, the second table for each direction is so that searching for a given location is simpler
    reached_f = {node_f.state: node_f}
    reached_g = {node_g.state: node_g}
    reached_f2 = {node_f.state[0]: node_f.state}
    reached_g2 = {node_g.state[0]: node_g.state}

    #Main Search Loop
    while not frontier_f.empty() and not frontier_g.empty():
        #selects whichever direction has a lower f cost and performs proceed function for that direction
        #also checks if a mutual state has been reached, if so, runs termination function
        if frontier_f.queue[0][0] < frontier_g.queue[0][0]:
            node_f = frontier_f.get(False)[2]
            if node_f.state[0] in reached_g2:
                return Termination("f", problem, node_f, reached_g, reached_g2)
            inf_bidirectional_proceed(problem, node_f, frontier_f, reached_f, reached_f2, h)
        else:
            node_g = frontier_g.get(False)[2]
            if node_g.state[0] in reached_f2:
                return Termination("b", problem, node_g, reached_f, reached_f2)
            inf_bidirectional_proceed(problem, node_g, frontier_g, reached_g, reached_g2, h2)
    return solution

#runs the bi-join nodes differently based on directional literal passed in
def Termination(dir, problem, node, reached, reached2):
    print("meeting point: ", node.state[0])
    if dir == "f":
        return bi_join_nodes(node, reached[reached2[node.state[0]]])
    else:
        return bi_join_nodes(reached[reached2[node.state[0]]], node)

#proceed function, expands the current node places it in frontier & reached or replaces it if the path cost is better than current node in the table
def inf_bidirectional_proceed(problem, node, frontier, reached, reached2, h):
    for child in expand(problem, node, h):
        s = child.state
        if s not in reached or child.path_cost < reached[s].path_cost:
            reached[s] = child
            reached2[s[0]] = s
            frontier.put((f(child, h), -next(counter), child))
    return None

#bi-join nodes function takes the current node from the front end search, uses it as the root for the current back end node, then iterates down the back end node to form one cohesive path.
def bi_join_nodes(child_f, child_b):
    current_node = child_b.parent
    next_node_b = current_node.parent
    parent_node = child_f
    current_node.parent = parent_node
    if next_node_b is None:
        return current_node
    while next_node_b is not None:
        parent_node = current_node
        current_node = next_node_b
        next_node_b = next_node_b.parent
        current_node.parent = parent_node
    return current_node

#maybe try bi-linked list for optimization
def expand(problem, node, h):
    s = node.state
    nodes = []
    for action in problem.actions(s):
        s_new = problem.result(s, action)
        cost = node.path_cost + problem.action_cost(s, action)
        new_node = problem.Node(s_new, node, action, cost, problem)
        if problem.heuristic_consistent_flag:
            problem.heuristic_consistent_flag = check_h_consistency(problem, new_node, h)
        nodes.append(new_node)
        # Keep track of the number of expanded states   
        problem.num_expanded_states += 1
    
        problem.num_generated_nodes += len(nodes)
    
    return nodes

def time_to_goal(node):
    problem = node.problem
    goal_loc = problem.goal_loc
    agent_loc = node.state[problem.state_dict['agent']]
    v, theta_a = node.state[problem.state_dict['velocity']]
    a = problem.a_max
    s = problem.hex_manhattan_distance(goal_loc, agent_loc) * sqrt(3) * problem.hex_size
    return problem.get_travel_time(v, a, s)

def time_to_start(node):
    problem = node.problem
    goal_loc = problem.root.state[0]
    agent_loc = node.state[problem.state_dict['agent']]
    v, theta_a = node.state[problem.state_dict['velocity']]
    a = problem.d_max
    s = problem.hex_manhattan_distance(goal_loc, agent_loc) * sqrt(3) * problem.hex_size
    return problem.get_travel_time(v, a, s)

def check_h_consistency(problem, node, h):
    heuristic_is_consistent = h(node.parent) <= problem.action_cost(node.parent.state, node.action) + h(node)
    if not heuristic_is_consistent:
                hn = h(node)
                hp = h(node.parent)
                ac = problem.action_cost(node.parent.state, node.action)
                print("h is inconsistent")
                print(f'ac:        {ac}')
                print(f'h(parent): {hp}')
                print(f'h(node):   {hn}')
                print(f'{hp} <= {ac} + {hn}  is false')
                print(node.state)
                print(node.parent.state)
    return heuristic_is_consistent

#h'(n) = (1-alpha)*h(n)
#alpha = x/y
#x = map size
#y = number of obstacles

def f(node, h = time_to_goal):
    return g(node) + a_star_weight * h(node)

def f2(node, h = time_to_start):
    return g(node) + a_star_weight * h(node)

def g(node):
    return node.path_cost

class PathfindingProblem:
    class Node:
        def __init__(self, state, parent, action, path_cost, problem):
            self.state = state
            self.parent = parent
            self.action = action
            self.path_cost = path_cost

            self.problem = problem

            

            # if the new node has a different angle than previous
            # the agent turned, apply the turning penalty and backtrack to update velocities and path costs along the path
            if self.is_turn() and not self.is_zigzag():
                r = 1
                current_node = self.parent
                while not current_node.is_turn() and current_node.is_zigzag():
                    current_node = current_node.parent
                    r += 1
                
                # calculate the max velocity for the turn
                v_max = sqrt(2*r * problem.ay_max)
                if state[1][0] > v_max:
                    # update the velocity in the current node to v_max
                    self.state = (
                        self.state[0],
                        (v_max, self.state[problem.state_dict['velocity']][1])
                    )
                self.update_velocity(problem)

        def update_velocity(self, problem):
            current_node = self
            while current_node.parent:
                new_v = problem.calculate_velocity(current_node.state[problem.state_dict['velocity']][0], problem.d_max, sqrt(3) * problem.hex_size)
                if new_v < current_node.parent.state[problem.state_dict['velocity']][0]:
                    parent_copy = copy(current_node.parent)
                    parent_copy.state = (
                        parent_copy.state[0],
                        (new_v, parent_copy.state[problem.state_dict['velocity']][1])
                    )
                    if parent_copy.parent:
                        parent_path_cost = parent_copy.parent.path_cost
                    else:
                        parent_path_cost = 0

                    parent_copy.path_cost = parent_path_cost + problem.get_travel_time(parent_copy.state[problem.state_dict['velocity']][0], problem.d_max, sqrt(3) * problem.hex_size)
                    current_node.parent = parent_copy
                    if problem.heuristic_consistent_flag:
                        problem.heuristic_consistent_flag = check_h_consistency(problem, parent_copy, time_to_goal)
                    current_node = current_node.parent
                else:
                    break
            
        def is_turn(self):
            return self.parent is not None and self.state[self.problem.state_dict['velocity']][1] != self.parent.state[self.problem.state_dict['velocity']][1]
        def is_zigzag(self):
            return self.parent is not None and self.parent.parent is not None and self.state[self.problem.state_dict['velocity']][1] == self.parent.parent.state[self.problem.state_dict['velocity']][1]

        
        def __str__(self):
            return str(self.state)
    def __init__(self, initial_state, hex_map, obstacle_map, goal_loc, hex_radius, hex_size, acceleration_max, deceleration_max, lat_acceleration_max):
        self.root = self.Node(initial_state, None, None, 0, self)
        self.hex_map = hex_map
        self.obstacle_map = obstacle_map
        self.goal_loc = goal_loc
        self.hex_radius = hex_radius
        self.hex_size = hex_size
        self.a_max = acceleration_max
        self.d_max = deceleration_max
        self.ay_max = lat_acceleration_max

        # for benchmarking
        self.heuristic_consistent_flag = True
        self.num_expanded_states = 0
        self.num_generated_nodes = 0

        # Defines the indices for the components of the state
        self.state_dict = {
            'agent': 0,
            'velocity': 1
        }

        # Defines the directions to the immediate neighborhood and their angle relative to horizontal
        self.neighborhood_angles = {
            (1,0): 0,
            (0,1): pi/3,
            (-1,1): 2*pi/3,
            (-1,0): pi,
            (0,-1): 4*pi/3,
            (1,-1): 5*pi/3   
        }
    def hex_manhattan_distance(self, hex1, hex2):
        #print("\nhex1: ", hex1, type(hex1), "\nhex2: ", hex2, type(hex2))
        q1, r1 = hex1
        q2, r2 = hex2

        dq = abs(q1-q2)
        dr = abs(r1-r2)
        ds = abs(-q1-q2-r1-r2)

        return (dq+dr+ds)/2

    # get the path cost of applying action to state
    def action_cost(self, state, action):
        u = state[self.state_dict['velocity']][0]
        a = self.a_max
        s = sqrt(3) * self.hex_size
        return self.get_travel_time(u, a, s)

    # calculate the travel time given initial velocity u, acceleration a, and distance s
    def get_travel_time(self, u, a, s):
        return (-u + sqrt(u*u + 4 * a * s))/a

    # check if the agent location in the state is the same as the goal location in the problem
    def is_goal(self, state):
        return state[self.state_dict['agent']] == self.goal_loc

    # Add two location tuples element-wise
    def add_locations(self, loc1, loc2):
        return tuple([sum(x) for x in zip(loc1,loc2)])

    # return a list of viable actions from state
    # an action is a direction tuple, eg (1, 0) is the hex to the right of the agent's location
    def actions(self, state):

        # Get the current direction of the agent in state
        # Cast to an int so it can be used to index neighborhood_angles.keys()
        # Coincidently, the values of the 6 directions correspond to their indices when casted this way
        current_angle = int(state[self.state_dict['velocity']][1])

        # Find the index values of the immediate turns in the clockwise (cw) and counter clockwise (ccw) directions
        ccw_turn_idx = current_angle + 1
        cw_turn_idx  = current_angle - 1

        # If these values are out of bounds, cycle to the front or back of the keys list
        if ccw_turn_idx > 5: ccw_turn_idx = 0 
        if cw_turn_idx  < 0: cw_turn_idx  = 5

        # Find the 3 actions corresponding to the straight, cw, ccw movements
        permutations = list(self.neighborhood_angles.keys())
        turns = [ccw_turn_idx, current_angle, cw_turn_idx]
        actions = [permutations[t] for t in turns]

        

        # Remove obstacles and out of bounds locations from the action list
        actions = [a for a in actions 
                   if self.add_locations(a, state[self.state_dict['agent']]) not in self.obstacle_map
                   and self.hex_manhattan_distance(self.add_locations(a, state[self.state_dict['agent']]), (0,0)) <= self.hex_radius
                  ]
        
        return actions

    # returns the result of applying action to state
    # this is done by adding action to agent location in state 
    # agent_loc: (3,4)
    # action: (1,0)
    # result_loc (4,4)

    # also calculate the new velocity and angle after moving to the new location
    def result(self, state, action):

        # add the action tuple to the agent_loc tuple to get the new location
        new_agent_loc = self.add_locations(state[self.state_dict['agent']], action)

        params = {
            'u': state[self.state_dict['velocity']][0],
            'a': self.a_max,
            's': sqrt(3)*self.hex_size
        }
        # get the new velocity after applying action
        new_velocity = self.calculate_velocity(**params)
        new_angle = self.neighborhood_angles[action]

        return (
            new_agent_loc,
            (new_velocity, new_angle)
        )

    # calculate the velocity with initial velocity u, acceleration a, over distance s
    def calculate_velocity(self, u, a, s):
        return sqrt(u*u + 2*a*s)
    
    def get_benchmarks(self):
        return (self.heuristic_consistent_flag, self.num_expanded_states, self.num_generated_nodes)
        
