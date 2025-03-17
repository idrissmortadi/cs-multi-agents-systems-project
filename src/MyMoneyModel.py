from mesa import Agent, Model
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid


def compute_gini(model):
    """
    Calculate the Gini coefficient of the model population.

    The Gini coefficient is a measure of inequality in a distribution, with 0 representing
    perfect equality (everyone has the same wealth) and 1 representing perfect inequality
    (one person has all wealth, others have none). It's commonly used to measure wealth
    or income inequality.

    Args:
        model: The model instance to calculate Gini coefficient for

    Returns:
        float: Gini coefficient for the entire population
    """
    agent_wealths = [agent.wealth for agent in model.agents]
    x = sorted(agent_wealths)
    N = model.num_agents
    B = sum(xi * (N - i) for i, xi in enumerate(x)) / (N * sum(x)) if sum(x) > 0 else 0
    return 1 + (1 / N) - 2 * B


def compute_gini_by_ethnicity(model):
    """
    Calculate the Gini coefficient for each ethnicity group in the model.

    Args:
        model: The model instance to calculate ethnicity-specific Gini coefficients for

    Returns:
        dict: Gini coefficients for each ethnicity group
    """
    gini_by_ethnicity = {}

    for ethnicity in model.ethnicities:
        agents = [agent for agent in model.agents if agent.ethnicity == ethnicity]
        if not agents:
            gini_by_ethnicity[ethnicity] = 0
            continue

        wealths = [agent.wealth for agent in agents]
        x = sorted(wealths)
        N = len(agents)

        if N > 0 and sum(x) > 0:
            B = sum(xi * (N - i) for i, xi in enumerate(x)) / (N * sum(x))
            gini = 1 + (1 / N) - 2 * B
        else:
            gini = 0

        gini_by_ethnicity[ethnicity] = gini

    return gini_by_ethnicity


class MoneyAgent(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.wealth = 1
        self.ethnicity = self.random.choice(self.model.ethnicities)

    def step_agent(self):
        self.move()
        if self.wealth > 0:
            self.give_money()

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

    def give_money(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        # cellmates.pop(cellmates.index(self))
        if len(cellmates) > 1:
            other = self.random.choice(cellmates)
            other.wealth += 1
            self.wealth -= 1


class MoneyModel(Model):
    def __init__(self, n=10, width=10, height=10, seed=None, grid_type="MultiGrid"):
        super().__init__(seed=seed)
        self.grid_type = grid_type
        self.ethnicities = ["Mixed", "Green", "Blue"]

        if grid_type == "MultiGrid":
            self.grid = MultiGrid(width, height, torus=True)
        else:
            raise ValueError("Unknown grid type")

        self.num_agents = n

        # Randomly put agents in the grid
        for i in range(self.num_agents):
            a = MoneyAgent(self)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            if self.grid_type == "SingleGrid":
                while self.grid.get_cell_list_contents((x, y)):
                    x = self.random.randrange(self.grid.width)
                    y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))

        self.datacollector = DataCollector(
            model_reporters={
                "Gini": compute_gini,
                "Gini_Mixed": lambda m: compute_gini_by_ethnicity(m).get("Mixed", 0),
                "Gini_Green": lambda m: compute_gini_by_ethnicity(m).get("Green", 0),
                "Gini_Blue": lambda m: compute_gini_by_ethnicity(m).get("Blue", 0),
            },
            agent_reporters={"Wealth": "wealth", "Ethnicity": "ethnicity"},
        )

    def step(self):
        self.datacollector.collect(self)
        # self.agents.shuffle_do("step_agent")
        ethnicities = self.agents.groupby("ethnicity", result_type="agentset")
        ethnicities.do(
            lambda x: x.shuffle_do("step_agent")
        )

    def get_all_ethnicities(self):
        return [a.ethnicity for a in self.agents]

    def get_all_wealth(self):
        return [a.wealth for a in self.agents]
