__author__ = 'Tofu Gang'

from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal as Signal
from src.tile import Tile, PassiveTile, Floor, Player, Box
from pickle import dump, load
from random import shuffle
from enum import Enum

################################################################################

class Level(QObject):
    algorithmStarted = Signal()
    algorithmFinished = Signal()

    DIRECTIONS = {  # (dRow, dColumn)
        Qt.Key_Left: tuple([0, -1]),
        Qt.Key_Right: tuple([0, 1]),
        Qt.Key_Up: tuple([-1, 0]),
        Qt.Key_Down: tuple([1, 0])
    }
    OPPOSITE_DIRECTIONS = {
        Qt.Key_Left: DIRECTIONS[Qt.Key_Right],
        Qt.Key_Right: DIRECTIONS[Qt.Key_Left],
        Qt.Key_Up: DIRECTIONS[Qt.Key_Down],
        Qt.Key_Down: DIRECTIONS[Qt.Key_Up]
    }
    KEY_PLAYER_POS = 'player_pos'
    KEY_BOXES_POS = 'boxes_pos'

    WL = Tile.Type.WALL
    PL = Tile.Type.PLAYER
    PG = Tile.Type.PLAYER_ON_GOAL
    BX = Tile.Type.BOX
    BG = Tile.Type.BOX_ON_GOAL
    GL = Tile.Type.GOAL
    FL = Tile.Type.FLOOR
    BK = Tile.Type.BACKGROUND

    LEVEL = ((BK, BK, BK, BK, BK, BK, BK, BK),
             (BK, WL, WL, WL, WL, BK, BK, BK),
             (BK, WL, FL, GL, WL, BK, BK, BK),
             (BK, WL, FL, FL, WL, WL, WL, BK),
             (BK, WL, BG, PL, FL, FL, WL, BK),
             (BK, WL, FL, FL, BX, FL, WL, BK),
             (BK, WL, FL, FL, WL, WL, WL, BK),
             (BK, WL, WL, WL, WL, BK, BK, BK),
             (BK, BK, BK, BK, BK, BK, BK, BK))

    with open('res/levels/world_01/01', 'wb') as f:
        dump(LEVEL, f)

################################################################################

    def __init__(self, path=None):
        """

        """

        super().__init__()

        if not path:
            with open('res/levels/world_01/01', 'rb') as f:
                self._level = load(f)

        self._player = None
        self._tiles = []
        self._boxes = []

        for rowNumber in range(len(self._level)):
            row = self._level[rowNumber]
            for columnNumber in range(len(row)):
                tileType = row[columnNumber]
                if tileType in (Tile.Type.WALL, Tile.Type.BACKGROUND):
                    tile = PassiveTile(tileType, rowNumber, columnNumber)
                else:
                    if tileType in (Tile.Type.PLAYER, Tile.Type.PLAYER_ON_GOAL):
                        self._player = Player(self, tileType, rowNumber, columnNumber)
                        self._player.setPos(columnNumber*Tile.SIZE, rowNumber*Tile.SIZE)
                    elif tileType in (Tile.Type.BOX, Tile.Type.BOX_ON_GOAL):
                        box = Box(self, tileType, rowNumber, columnNumber)
                        box.setPos(columnNumber*Tile.SIZE, rowNumber*Tile.SIZE)
                        self._boxes.append(box)
                    tile = Floor(tileType, rowNumber, columnNumber)
                tile.setPos(columnNumber*Tile.SIZE, rowNumber*Tile.SIZE)
                self._tiles.append(tile)
        self._origState = self.state()

################################################################################

    @property
    def width(self):
        """

        :return:
        """

        return len(self._level[0])*Tile.SIZE

################################################################################

    @property
    def height(self):
        """

        :return:
        """

        return len(self._level)*Tile.SIZE

################################################################################

    @property
    def player(self):
        """

        :return:
        """

        return self._player

################################################################################

    @property
    def tiles(self):
        """

        :return:
        """

        return self._tiles

################################################################################

    @property
    def boxes(self):
        """

        :return:
        """

        return self._boxes

################################################################################

    def state(self):
        """

        :return:
        """

        return {
            self.KEY_PLAYER_POS: (self.player.row, self.player.column),
            self.KEY_BOXES_POS: tuple((box.row, box.column) for box in self._boxes)
        }

################################################################################

    def goalCoords(self):
        """

        :return:
        """

        return tuple([tuple((tile.row, tile.column)) for tile in self._tiles if tile.isFloor and tile.isGoal])

################################################################################

    def wallsCoords(self):
        """

        :return:
        """

        return tuple([tuple((tile.row, tile.column)) for tile in self._tiles if tile.tileType is Tile.Type.WALL])

################################################################################

    def isSolved(self):
        """

        :return:
        """

        return all(self.tileOnCoords(box.row, box.column).isGoal for box in self._boxes)

################################################################################

    def reset(self, state=None):
        """

        :return:
        """

        if not state:
            state = self._origState

        self._player.setCoords(state[self.KEY_PLAYER_POS][0],
                               state[self.KEY_PLAYER_POS][1])
        [self._boxes[i].setCoords(state[self.KEY_BOXES_POS][i][0],
                                  state[self.KEY_BOXES_POS][i][1])
         for i in range(len(self._boxes))]

################################################################################

    def tileOnCoords(self, row, column):
        """

        :param row:
        :param column:
        :return:
        """

        return [tile for tile in self._tiles if tile.row == row and tile.column == column][0]

################################################################################

    def box(self, row, column):
        """

        :param row:
        :param column:
        :return:
        """

        return [box for box in self._boxes if box.row == row and box.column == column][0]

################################################################################

    def movePlayer(self, dRow, dColumn, animated=False):
        """

        :param dRow:
        :param dColumn:
        """

        if self._player.canBeMoved(dRow, dColumn):
            self._player.move(dRow, dColumn, animated)

################################################################################

    def bfs(self, deterministic=True):
        """

        :param deterministic:
        :return:
        """

        self._createGraph()
        self._graph.bfs(deterministic)

################################################################################

    def dfs(self, deterministic=True):
        """

        :param deterministic:
        :return:
        """

        self._createGraph()
        self._graph.dfs(deterministic)

################################################################################

    def _createGraph(self):
        """

        :return:
        """

        self._graph = Graph(self.state(), self.goalCoords(), self.wallsCoords())
        self._graph.started.connect(self.algorithmStarted)
        self._graph.finished.connect(self._playSolution)
        self._graph.finished.connect(self.algorithmFinished)

################################################################################

    def _playSolution(self):
        """

        :return:
        """

        self.reset()
        self._player.moveFinished.connect(self._nextStep)
        self._nextStep()

################################################################################

    def _nextStep(self):
        """

        :return:
        """

        step = self._graph.solutionStep()
        if step:
            dRow = step[0]
            dColumn = step[1]
            self.movePlayer(dRow, dColumn, animated=True)
        else:
            self._player.moveFinished.disconnect(self._nextStep)

################################################################################

class Graph(QThread):

    class Algorithms(Enum):
        BFS = 'BFS'
        DFS = 'DFS'

################################################################################

    def __init__(self, state, goal, walls):
        """

        :param level:
        """

        super().__init__()
        self._state = state
        self._goal = goal
        self._walls = walls
        self._frontier = []
        self._explored = []
        self._solution = []
        self._algorithm = None
        self._deterministic = True

################################################################################

    def _playerCanBeMoved(self, dRow, dColumn):
        """

        :param dRow:
        :param dColumn:
        :return:
        """

        row = self._state[Level.KEY_PLAYER_POS][0]
        column = self._state[Level.KEY_PLAYER_POS][1]
        rowTo = row+dRow
        columnTo = column+dColumn
        if tuple((rowTo, columnTo)) in self._walls:
            return False
        elif tuple((rowTo, columnTo)) in self._state[Level.KEY_BOXES_POS]:
            boxRowTo = rowTo+dRow
            boxColumnTo = columnTo+dColumn
            if tuple((boxRowTo, boxColumnTo)) in self._walls:
                return False
            elif tuple((boxRowTo, boxColumnTo)) in self._state[Level.KEY_BOXES_POS]:
                return False
            else:
                return True
        else:
            return True

################################################################################

    def _movePlayer(self, dRow, dColumn):
        """

        :param dRow:
        :param dColumn:
        :return:
        """

        row = self._state[Level.KEY_PLAYER_POS][0]
        column = self._state[Level.KEY_PLAYER_POS][1]
        rowTo = row+dRow
        columnTo = column+dColumn
        if tuple((rowTo, columnTo)) in self._state[Level.KEY_BOXES_POS]:
            boxRowTo = rowTo+dRow
            boxColumnTo = columnTo+dColumn
            temp = list(self._state[Level.KEY_BOXES_POS])
            temp.remove(tuple((rowTo, columnTo)))
            temp.append(tuple((boxRowTo, boxColumnTo)))
            self._state[Level.KEY_BOXES_POS] = tuple(temp)
        self._state[Level.KEY_PLAYER_POS] = tuple((rowTo, columnTo))

################################################################################

    def _isSolved(self):
        """

        :return:
        """

        return all(boxCoords in self._goal for boxCoords in self._state[Level.KEY_BOXES_POS])

################################################################################

    def _reset(self):
        """

        :return:
        """

        self._frontier.clear()
        self._explored.clear()
        self._solution.clear()

################################################################################

    def bfs(self, deterministic):
        """

        :param deterministic:
        :return:
        """

        self._algorithm = self.Algorithms.BFS
        self._deterministic = deterministic
        self.start()

################################################################################

    def dfs(self, deterministic):
        """

        :param deterministic:
        :return:
        """

        self._algorithm = self.Algorithms.DFS
        self._deterministic = deterministic
        self.start()

################################################################################

    def solutionStep(self):
        """

        :return:
        """

        if len(self._solution) > 1:
            node = self._solution.pop(0)
            if len(self._solution) > 0:
                nodeNext = self._solution[0]
                dRow = nodeNext.state[Level.KEY_PLAYER_POS][0]-node.state[Level.KEY_PLAYER_POS][0]
                dColumn = nodeNext.state[Level.KEY_PLAYER_POS][1]-node.state[Level.KEY_PLAYER_POS][1]
                return tuple([dRow, dColumn])
            else:
                return None
        else:
            return None

################################################################################

    def run(self):
        """

        :return:
        """

        self._reset()
        root = Node(self._state.copy())
        self._frontier.append(root)

        while len(self._frontier) > 0:
            node = self._frontier.pop()
            self._state = node.state.copy()
            self._explored.append(node)
            directions = list(Level.DIRECTIONS)
            if not self._deterministic:
                shuffle(directions)
            for direction in directions:
                dRow = Level.DIRECTIONS[direction][0]
                dColumn = Level.DIRECTIONS[direction][1]
                if self._playerCanBeMoved(dRow, dColumn):
                    self._movePlayer(dRow, dColumn)
                    child = Node(self._state.copy(), node)
                    if child.state not in (node.state for node in self._frontier+self._explored):
                        if self._isSolved():
                            node = child
                            while node:
                                self._solution.append(node)
                                node = node.parent
                            self._solution = list(reversed(self._solution))
                            return
                        else:
                            if self._algorithm is self.Algorithms.BFS:
                                self._frontier.insert(0, child)
                            elif self._algorithm is self.Algorithms.DFS:
                                self._frontier.append(child)
                            else:
                                pass
                    self._state = node.state.copy()

################################################################################

class Node():

################################################################################

    def __init__(self, state, parent=None):
        """

        :param state:
        :param parent:
        """

        self._state = state
        self._parent = parent
        if parent:
            self._depth = parent.depth+1
        else:
            self._depth = 0

################################################################################

    @property
    def state(self):
        """

        :return:
        """

        return self._state

################################################################################

    @property
    def depth(self):
        """

        :return:
        """

        return self._depth

################################################################################

    @property
    def parent(self):
        """

        :return:
        """

        return self._parent

################################################################################
