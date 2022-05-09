import salabim as sim
import datetime
import time

date = datetime.datetime.today().date()
# date = datetime.datetime.strptime("2022-05-07", "%Y-%m-%d").date()


label_lines = """\
jan feb mar apr may jun   *
jul aug sep oct nov dec   *
  1   2   3   4   5   6   7
  8   9  10  11  12  13  14
 15  16  17  18  19  20  21
 22  23  24  25  26  27  28
 29  30  31 sun mon tue wed
  *   *   *   * thu fri sat""".splitlines()

pieces = """\
 x  |  x | x  |xxx |xx  |xx  |xx  |xxx |xxx |xxxx|
xx  |xxx |xx  |x   | xxx|x   |x   | x  |x   |    |
x   |x   |xx  |x   |    |x   |xx  | x  |    |    |
    |    |    |    |    |x   |         |    |    |""".splitlines()


class Piece:
    def __init__(self, id):
        self.sub_pieces = []
        self.id = id


class SubPiece:
    def __init__(self, id, displacements=None):
        self.id = id
        self.displacements = displacements
        self.match =  False

    def __repr__(self):
        return self.id


class Board:
    def __init__(self, date):
        self.sub_pieces = {}
        self.date = date
        day = str(date.day)
        month = "jan feb mar apr may jun jul aug sep oct nov dec".split()[date.month - 1]
        weekday = "mon tue wed thu fri sat sun".split()[date.weekday()]
        for xy, label in env.labels.items():
            if label in (day, month, weekday):
                self.sub_pieces[xy] = env.occupied
            else:
                self.sub_pieces[xy] = env.free

    def sub_piece(self, xy):
        return self.sub_pieces.get(xy, env.out_of_board)

    def display(self):
        for sub_piece in env.all_sub_pieces:
            sub_piece.ao.visible = False

        for sub_piece, (x, y) in self.piecify().items():
            sub_piece.ao.visible = True
            if sub_piece.match:
                sub_piece.ao.fillcolor='50%gray'
            else:
                sub_piece.ao.fillcolor='black'
            sub_piece.ao.x = env.origin_x + x * env.grid_size + env.grid_size / 2
            sub_piece.ao.y = env.origin_y + (env.dim_y - 1 - y) * env.grid_size + env.grid_size / 2

    def dump(self):
        for y in range(env.dim_y):
            for x in range(env.dim_x):
                print(f"{self.sub_piece((x,y)).id:5}", end="")
            print()
        print()

    def piecify(self):
        locations = {}
        for xy, sub_piece in self.sub_pieces.items():
            if sub_piece.displacements and sub_piece not in locations:
                locations[sub_piece] = xy
        return locations

    def get_number_of_mismatches(self):
        locations = self.piecify()
        previous_locations = env.previous_board.piecify()
        number_of_mismatches = 0
        for sub_piece, xy in locations.items():
            if previous_locations.get(sub_piece) == xy:
                sub_piece.match = True
            else:
                sub_piece.match = False
                number_of_mismatches += 1
                
        return number_of_mismatches

    def check_vertical_bar_sub_piece(self):  # a vertical bar should not "fall down"
        for (x, y), sub_piece in self.sub_pieces.items():
            if sub_piece == env.vertical_bar_sub_piece:
                return not self.sub_piece((x, y + 4)) == env.occupied
        return True

    def save(self):
        with open("calendar puzzle solution.txt", "w") as outfile:
            print(self.date.strftime("%Y-%m-%d"), file=outfile)
            for xy, sub_piece in self.sub_pieces.items():
                print(*xy, sub_piece.id, file=outfile)

    def copy(self):
        board = Board(date=self.date)
        board.sub_pieces = self.sub_pieces.copy()
        return board

    @classmethod
    def read(cls):
        try:
            with open("calendar puzzle solution.txt", "r") as infile:
                date_str = infile.readline().strip()
                date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                board = cls(date)
                for line in infile.readlines():
                    x, y, id = line.split()
                    board.sub_pieces[(int(x), int(y))] = id_to_sub_piece(id)
        except FileNotFoundError:
            board = cls(datetime.datetime(2000, 1, 1).date())
        return board


def id_to_sub_piece(id):
    if id == "occ":
        return env.occupied
    for sub_piece in env.all_sub_pieces:
        if sub_piece.id == id:
            return sub_piece


def add_tuple(tuple0, tuple1):
    return tuple0[0] + tuple1[0], tuple0[1] + tuple1[1]


def sub_tuple(tuple0, tuple1):
    return tuple0[0] - tuple1[0], tuple0[1] - tuple1[1]


def create_display():
    env.labels = {}
    for y, label_line in enumerate(label_lines):
        for x, label in enumerate(label_line.split()):
            if label != "*":
                env.labels[(x, y)] = label
                sim.AnimateRectangle(
                    spec=(-env.grid_size / 2, -env.grid_size / 2, env.grid_size / 2, env.grid_size / 2),
                    fillcolor="50%gray",
                    linecolor="white",
                    linewidth=env.line_width,
                    x=env.origin_x + x * env.grid_size + env.grid_size / 2,
                    y=env.origin_y + (env.dim_y - 1 - y) * env.grid_size + env.grid_size / 2,
                    text_anchor="c",
                    text=label,
                    textcolor="white",
                    fontsize=env.font_size,
                )

    env.an_info = sim.AnimateText(x=env.origin_x, y=env.origin_y + env.dim_y * env.grid_size, fontsize=env.font_size_info)


def create_pieces():
    env.occupied = SubPiece("occ")
    env.free = SubPiece("free")
    env.out_of_board = SubPiece("out")
    env.all_pieces = []
    env.all_sub_pieces = []

    for piece_number in range(len(pieces[0]) // 5):
        piece = Piece(id=f"{piece_number}")
        env.all_pieces.append(piece)
        displacements = [(x, y) for y, line in enumerate(pieces) for x in range(4) if line[piece_number * 5 + x] == "x"]
        sub_piece_number = 0
        for _ in range(4):
            for _ in range(2):
                displacements.sort(key=lambda pair: (pair[1], pair[0]))
                displacements = tuple(sub_tuple(pair, displacements[0]) for pair in displacements)  # shift to (0,0)

                if not any(displacements == sub_piece.displacements for sub_piece in piece.sub_pieces):
                    sub_piece = SubPiece(id=f"{piece_number}.{sub_piece_number}", displacements=displacements)
                    env.all_sub_pieces.append(sub_piece)
                    piece.sub_pieces.append(sub_piece)
                    lines = []
                    for x, y in displacements:
                        for line in (((x, y), (x + 1, y)), ((x + 1, y), (x + 1, y + 1)), ((x, y + 1), (x + 1, y + 1)), ((x, y), (x, y + 1))):
                            if line in lines:
                                lines.remove(line)
                            else:
                                lines.append(line)

                    polygon = []
                    scale = env.grid_size
                    point = (0, 0)
                    while lines:
                        for line in lines:
                            if line[0] == point or line[1] == point:
                                point = line[line[0] == point]
                                lines.remove(line)
                                polygon.append(scale * (point[0] - 0.5))
                                polygon.append(-scale * (point[1] - 0.5))
                                break

                    sub_piece.polygon = polygon

                    sub_piece.ao = sim.AnimatePolygon(spec=polygon, fillcolor="black", linecolor="white", linewidth=env.line_width, visible=False)

                    if displacements == ((0, 0), (0, 1), (0, 2), (0, 3)):
                        env.vertical_bar_sub_piece = sub_piece

                    sub_piece_number += 1
                displacements = [(-x, y) for x, y in displacements]  # mirror
            displacements = [(y, -x) for x, y in displacements]  # rotate

    env.unused_pieces = env.all_pieces.copy()


env = sim.Environment()

env.dim_x = len(label_lines[0].split())
env.dim_y = len(label_lines)

if env.height() < env.width():
    env.grid_size = (env.height() - 80) / env.dim_y
else:
    env.grid_size = (env.width() - 20) / env.dim_x

env.origin_x = 10
env.origin_y = 10
env.line_width = 3
env.font_size = 30
env.font_size_info = 15

if env.grid_size < 51:  # iPhone
    env.line_width = 2
    env.font_size = 20
    env.font_size_info = 9


create_display()
create_pieces()


class Solver(sim.Component):
    def process(self):
        def solve():
            if len(env.unused_pieces) == 0:
                if env.board.check_vertical_bar_sub_piece():
                    number_of_mismatches = env.board.get_number_of_mismatches()
                    if number_of_mismatches < env.minimum_number_of_mismatches:
                        env.minimum_number_of_mismatches = number_of_mismatches
                        env.min_boards = []
                    if number_of_mismatches == env.minimum_number_of_mismatches:
                        env.min_boards.append(env.board.copy())
                    env.an_info.text = f"solution number={env.solution_number:5d} number of iterations={env.iterations:7d} mismatches={number_of_mismatches:2d}/{env.minimum_number_of_mismatches:2d}"
                    env.board.display()
                    yield self.hold(1)
                    env.solution_number += 1
                return
            for piece in env.unused_pieces[:]:
                for first, sub_piece in env.board.sub_pieces.items():
                    if sub_piece == env.free:
                        break

                for sub_piece in piece.sub_pieces:
                    if all(env.board.sub_piece(add_tuple(first, pair)) == env.free for pair in sub_piece.displacements):
                        for pair in sub_piece.displacements:
                            env.board.sub_pieces[add_tuple(first, pair)] = sub_piece
                        env.unused_pieces.remove(piece)

                        env.iterations += 1

                        yield from solve()
                        env.unused_pieces.append(piece)

                        for pair in sub_piece.displacements:
                            env.board.sub_pieces[add_tuple(first, pair)] = env.free

        env.iterations = 0
        env.solution_number = 0
        env.min_boards = []
        env.minimum_number_of_mismatches = 100
        env.board = Board(date)

        yield from solve()
        env.board = sim.Pdf(env.min_boards, 1)()
        env.board.get_number_of_mismatches()  # to set the colour of matching sub_pieces    
        env.board.save()
        env.an_info.text = f"final solution / mismatches={env.minimum_number_of_mismatches} / number of min_boards={len(env.min_boards)}"
        print(f"{time.perf_counter()-env.t0:7.3f} seconds")
        env.main().activate()


env.previous_board = Board.read()

env.t0 = time.perf_counter()

ended = False
if date == env.previous_board.date:
    env.board = env.previous_board
    env.an_info.text = f"stored solution"
else:
    env.animate(True)
    env.synced(False)
    Solver()
    try:
        env.run(sim.inf)
    except sim.SimulationStopped:
        ended = True

if not ended:
    env.board.display()
    env.animate(True)
    env.synced(True)

    try:
        env.run(sim.inf)
    except sim.SimulationStopped:
        pass

print("ended")

