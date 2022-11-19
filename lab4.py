import re
from typing import List


input_filepath = './input.txt'
grid_size = 10
max_countries_amount = 20
initial_city_balance = 1_000_000
representative_portion = 1_000


def read_lines(filepath):
    with open(filepath, 'r') as file:
        data = file.read()
    return data.split('\n')


def parse_country(line):
    args = line.split(' ')
    if len(args) != 5:
        raise Exception("Error at line {%s}: invalid number of tokens" % line)
    name_pattern = re.compile("[A-Z][a-z]{1,24}$")
    if not name_pattern.match(args[0]):
        raise Exception("Error at line {%s}: invalid country name" % line)
    for i in range(1, 5):
        if int(args[i]) <= 0 or int(args[i]) >= (grid_size + 1):
            raise Exception("Error at line {%s}: invalid country coordinates" % line)

    country = {
        "name": args[0],
        "ll": {
            "x": int(args[1]),
            "y": int(args[2])
        },
        "ur": {
            "x": int(args[3]),
            "y": int(args[4])
        }
    }
    return country


def parse_input():
    cases = []

    lines = read_lines(input_filepath)
    line_index = 0
    case = 0
    while line_index < len(lines):
        counties_len = int(lines[line_index])
        if counties_len == 0:
            return cases
        if counties_len > max_countries_amount or counties_len < 1:
            raise Exception("Error in input for case %i: invalid amount of countries" % (case + 1))
        line_index += 1

        countries_list = []
        for j in range(counties_len):
            parsed = parse_country(lines[line_index])
            countries_list.append(parsed)
            line_index += 1
        case += 1
        cases.append(countries_list)

    return cases


class City:
    def __init__(self, country_name: str, countries_list: list, x: int, y: int):
        self.country_name = country_name
        self.x = x
        self.y = y
        self.balance = {city_data["name"]: 0 for city_data in countries_list}
        self.balance[country_name] = initial_city_balance
        self.balance_per_day = {city_data["name"]: 0 for city_data in countries_list}
        self.neighbours: List['City'] = []
        self.full = False

    def set_neighbours(self, neighbours: List['City']) -> None:
        self.neighbours = neighbours

    def transfer_to_neighbours(self) -> None:
        for motif in self.balance:
            balance_of_motif = self.balance[motif]
            amount_to_transfer = balance_of_motif // representative_portion
            if amount_to_transfer > 0:
                for neighbour in self.neighbours:
                    self.balance[motif] -= amount_to_transfer
                    neighbour.add_balance_in_motif(motif, amount_to_transfer)

    def add_balance_in_motif(self, motif: str, amount: int) -> None:
        self.balance_per_day[motif] += amount

    def finalize_balance_per_day(self) -> None:
        for motif in self.balance_per_day:
            self.balance[motif] += self.balance_per_day[motif]
            self.balance_per_day[motif] = 0

        if not self.full:
            for motif in self.balance_per_day:
                if self.balance[motif] == 0:
                    return
            self.full = True

class Country:
    def __init__(self, name: str):
        self.name = name
        self.cities: List[City] = []
        self.full = False
        self.day_of_full = -1

    def __eq__(self, other):
        return self.day_of_full == other.day_of_full

    def __lt__(self, other):
        return self.day_of_full < other.day_of_full

    def append_city(self, city: City) -> None:
        self.cities.append(city)

    def check_fullness(self, day) -> None:
        if self.full:
            return
        for city in self.cities:
            if city.full is False:
                return
        self.full = True
        self.day_of_full = day

    def has_foreign_neighbours(self) -> bool:
        for city in self.cities:
            for neighbour in city.neighbours:
                if neighbour.country_name != self.name:
                    return True

    def only_country_mode(self) -> None:
        self.full = True
        self.day_of_full = 0

class Map:
    def __init__(self, countries_data):
        self.countries = []
        self.grid: List[List[City]] = [[None] * (grid_size + 2) for i in range((grid_size + 2))]
        self.__initialize_grid(countries_data)
        self.__validate_foreign_neighbours()

    def simulate_euro_diffusion(self) -> None:
        if len(self.countries) == 1:
            self.countries[0].day_of_full = 0
            return

        full = False
        day = 1
        while not full:
            for x in range(grid_size + 1):
                for y in range(grid_size + 1):
                    if self.grid[x][y] is not None:
                        city = self.grid[x][y]
                        city.transfer_to_neighbours()

            for x in range(grid_size + 1):
                for y in range(grid_size + 1):
                    if self.grid[x][y] is not None:
                        city = self.grid[x][y]
                        city.finalize_balance_per_day()

            full = True
            for country in self.countries:
                country.check_fullness(day)
                if country.full is False:
                    full = False

            day += 1

        self.countries.sort()

    def __initialize_grid(self, countries_data) -> None:
        for country_data in countries_data:
            country = Country(country_data["name"])
            for x in range(country_data["ll"]["x"], country_data["ur"]["x"] + 1):
                for y in range(country_data["ll"]["y"], country_data["ur"]["y"] + 1):
                    if self.grid[x][y] is not None:
                        raise Exception("%s intersects with %s on [%i, %i]" %
                                        (self.grid[x][y].country_name, country.name, x, y))
                    city = City(country.name, countries_data, x, y)
                    self.grid[x][y] = city
                    country.append_city(city)
            self.countries.append(country)

        for row in self.grid:
            for city in row:
                if city is not None:
                    neighbours_list = self.__get_neighbours(city.x, city.y)
                    city.set_neighbours(neighbours_list)

    def __get_neighbours(self, x, y) -> List[City]:
        neighbours = []
        if self.grid[x][y + 1] is not None:
            neighbours.append(self.grid[x][y + 1])
        if self.grid[x][y - 1] is not None:
            neighbours.append(self.grid[x][y - 1])
        if self.grid[x + 1][y] is not None:
            neighbours.append(self.grid[x + 1][y])
        if self.grid[x - 1][y] is not None:
            neighbours.append(self.grid[x - 1][y])
        return neighbours

    def __validate_foreign_neighbours(self) -> None:
        if len(self.countries) <= 1:
            return
        for country in self.countries:
            if not country.has_foreign_neighbours():
                raise Exception("%s has no connection with other countries" % country.name)

if __name__ == "__main__":
    cases = []
    try:
        cases = parse_input()
    except Exception as e:
        print(e)
        exit()

    for i, countries_list in enumerate(cases):
        print("\nCase Number %i" % (i + 1))

        try:
            europe_map = Map(countries_list)
            europe_map.simulate_euro_diffusion()
            for country in europe_map.countries:
                print(country.name, country.day_of_full)

        except Exception as e:
            print(e)
