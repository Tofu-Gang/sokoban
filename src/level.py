__author__ = 'Tofu Gang'

from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal as Signal
from src.tile import Tile, PassiveTile, Player, Box
from random import shuffle
from enum import Enum
from typing import Union, Tuple, Dict


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

################################################################################

    def __init__(self, filePath: str) -> None:
        """
        Level board representation (NOT the graphic one from Graphics View
        framework). Methods are provided to get the board size, player and boxes
        objects, box or a tile in a specific position (row, column), walls and
        goal floor tiles and if the level is solved (all boxes placed on goal
        floor tiles). Additionally, the level can be reset to the original
        state. Furthermore, means for moving the player or boxes are provided
        (with checks if the move is possible).
        Lastly, AI is provided for solving the level (bfs and dfs tree search).
        This AI-created solution can be played as well.

        :param filePath: path to the level file
        :return: None
        """

        super().__init__()

        self._player = None
        self._tiles = []
        self._boxes = []
        self._level = self._openLevelFile(filePath)

        for rowNumber in range(len(self._level)):
            row = self._level[rowNumber]
            for columnNumber in range(len(row)):
                tileType = row[columnNumber]

                if tileType == Tile.Type.PLAYER:
                    self._player = Player(rowNumber, columnNumber, False)
                    self._tiles.append(PassiveTile(Tile.Type.FLOOR, rowNumber, columnNumber))
                elif tileType == Tile.Type.PLAYER_ON_GOAL:
                    self._player = Player(rowNumber, columnNumber, True)
                    self._tiles.append(PassiveTile(Tile.Type.GOAL, rowNumber, columnNumber))
                elif tileType == Tile.Type.BOX:
                    self._boxes.append(Box(rowNumber, columnNumber, False))
                    self._tiles.append(PassiveTile(Tile.Type.FLOOR, rowNumber, columnNumber))
                elif tileType == Tile.Type.BOX_ON_GOAL:
                    self._boxes.append(Box(rowNumber, columnNumber, True))
                    self._tiles.append(PassiveTile(Tile.Type.GOAL, rowNumber, columnNumber))
                else:
                    self._tiles.append(PassiveTile(tileType, rowNumber, columnNumber))

        self._tiles = tuple(self._tiles)
        self._boxes = tuple(self._boxes)
        self._origState = self.state

################################################################################

    @property
    def width(self) -> int:
        """
        :return: number of columns of the level board
        """

        return len(self._level[0])*Tile.SIZE

################################################################################

    @property
    def height(self) -> int:
        """

        :return: number of rows of the level board
        """

        return len(self._level)*Tile.SIZE

################################################################################

    @property
    def player(self) -> Player:
        """
        :return: player object
        """

        return self._player

################################################################################

    @property
    def tiles(self) -> Tuple[PassiveTile]:
        """
        :return: tuple of all tiles in the level (floors, goal floor tiles,
        walls, background)
        """

        return self._tiles

################################################################################

    @property
    def boxes(self) -> Tuple[Box]:
        """
        :return: tuple of all boxes in the level
        """

        return self._boxes

################################################################################

    @property
    # TODO: return annotation Dict[str[Tuple[int, int]]]
    def state(self) -> Dict:
        """
        :return: Current position of the player and all boxes in the level
        """

        return {
            self.KEY_PLAYER_POS: (self._player.row, self._player.column),
            self.KEY_BOXES_POS: tuple((box.row, box.column) for box in self._boxes)
        }

################################################################################

    @property
    def goalCoords(self) -> Tuple[Tuple[int, int]]:
        """
        :return: positions of all goal floor tiles in the level
        """

        return tuple([tuple((tile.row, tile.column))
                      for tile in self._tiles
                      if tile.isFloor and tile.isGoal])

################################################################################

    @property
    def wallsCoords(self) -> Tuple[Tuple[int, int]]:
        """
        :return: positions of all walls in the level
        """

        walls = []
        for tile in self._tiles:
            if not tile.isFloor:
                walls.append((tile.row, tile.column))

        return tuple(walls)

################################################################################

    @property
    def isSolved(self) -> bool:
        """
        :return: True if the level is solved (all boxes placed on goal floor
        tiles), False otherwise
        """

        return all(self.tileOnCoords(box.row, box.column).isGoal for box in self._boxes)

################################################################################

    # TODO: return annotation Tuple[Tuple[Tile.Type]]
    def _openLevelFile(self, filePath: str):
        """
        Loads level board from a specified file.

        :param filePath: path to the level file
        :return: level board structure created from Tile.Type enum values
        """

        level = []

        with open(filePath, "r") as f:
            for line in f.readlines():
                stripped = line.strip()
                row = []
                for literal in stripped:
                    if literal == Tile.Type.WALL.value:
                        row.append(Tile.Type.WALL)
                    elif literal == Tile.Type.PLAYER.value:
                        row.append(Tile.Type.PLAYER)
                    elif literal == Tile.Type.PLAYER_ON_GOAL.value:
                        row.append(Tile.Type.PLAYER_ON_GOAL)
                    elif literal == Tile.Type.BOX.value:
                        row.append(Tile.Type.BOX)
                    elif literal == Tile.Type.BOX_ON_GOAL.value:
                        row.append(Tile.Type.BOX_ON_GOAL)
                    elif literal == Tile.Type.GOAL.value:
                        row.append(Tile.Type.GOAL)
                    elif literal == Tile.Type.FLOOR.value:
                        row.append(Tile.Type.FLOOR)
                    elif literal == Tile.Type.BACKGROUND.value:
                        row.append(Tile.Type.BACKGROUND)
                    else:
                        row.append(None)
                level.append(tuple(row))
            return tuple(level)

################################################################################

    def tileOnCoords(self, row: int, column: int) -> Tile:
        """
        :param row: row number in the level board
        :param column: column number in the level board
        :return: tile in the specified position from the params
        """

        return [tile for tile in self._tiles if
                tile.row == row and tile.column == column][0]

################################################################################

    def box(self, row, column) -> Union[Box, None]:
        """
        :param row: row number in the level board
        :param column: column number in the level board
        :return: Box object if there is a box in the specified position (by
        params), None otherwise
        """

        try:
            return [box for box in self._boxes
                    if box.row == row and box.column == column][0]
        except IndexError:
            return None

################################################################################

    def reset(self, state: dict=None) -> None:
        """
        Resets the level to the specified state. If the state is not provided
        (param value is None), the original state is used.

        :return: None
        """

        if not state:
            state = self._origState
        playerRowTo = state[self.KEY_PLAYER_POS][0]
        playerColumnTo = state[self.KEY_PLAYER_POS][1]
        movePlayerToGoal = (playerRowTo, playerColumnTo) in self.goalCoords
        self._player.setCoords(playerRowTo, playerColumnTo, movePlayerToGoal)

        for i in range(len(self._boxes)):
            boxRowTo = state[self.KEY_BOXES_POS][i][0]
            boxColumnTo = state[self.KEY_BOXES_POS][i][1]
            moveBoxToGoal = (boxRowTo, boxColumnTo) in self.goalCoords
            box = self._boxes[i]
            box.setCoords(boxRowTo, boxColumnTo, moveBoxToGoal)

################################################################################

    def _canPlayerBeMoved(self, dRow: int, dColumn: int) -> bool:
        """
        Indicates whether the player can be moved in the specified direction.

        :param dRow: number of rows to move (negative is up, positive is down)
        :param dColumn: number of columns to move (negative is left, positive is
        right)
        :return: True if the target tile is a floor/goal tile without a box or
        if the box can be pushed aside on a free floor/goal tile, False
        otherwise.
        """

        rowTo = self._player.row+dRow
        columnTo = self._player.column+dColumn
        tileTo = self.tileOnCoords(rowTo, columnTo)

        if tileTo.isFloor:
            box = self.box(rowTo, columnTo)
            if box is not None:
                return self._canBoxBeMoved(dRow, dColumn, box)
            else:
                return True
        else:
            return False

################################################################################

    def _canBoxBeMoved(self, dRow: int, dColumn: int, box: Box) -> bool:
        """
        Indicates whether the box can be pushed in the specified direction.

        :param dRow: number of rows to move (negative is up, positive is down)
        :param dColumn: number of columns to move (negative is left, positive is
        right)
        :return: True if the target tile is a floor/goal tile without a box,
        False otherwise.
        """

        rowTo = box.row+dRow
        columnTo = box.column+dColumn
        tileTo = self.tileOnCoords(rowTo, columnTo)
        if tileTo.isFloor:
            return self.box(rowTo, columnTo) is None
        else:
            return False

################################################################################

    def _moveBox(self, dRow: int, dColumn: int, box: Box, animated: bool=False) -> None:
        """
        Moves the specified box in the specified direction. Makes no checks if
        it is actually possible.

        :param dRow: number of rows to move (negative is up, positive is down)
        :param dColumn: number of columns to move (negative is left, positive is
        right)
        :param box: the box to be moved
        :param: animated: True if the move should be animated, False otherwise
        :return: None
        """

        if self._canBoxBeMoved(dRow, dColumn, box):
            rowTo = box.row + dRow
            columnTo = box.column + dColumn
            moveToGoal = (rowTo, columnTo) in self.goalCoords
            box.move(dRow, dColumn, moveToGoal, animated)

################################################################################

    def movePlayer(self, dRow: int, dColumn: int, animated: bool=False) -> None:
        """
        Moves the player in the specified direction. Makes no checks if it is
        actually possible.

        :param dRow: number of rows to move (negative is up, positive is down)
        :param dColumn: number of columns to move (negative is left, positive is
        right)
        :param: animated: True if the move should be animated, False otherwise
        :return: None
        """

        playerRowTo = self._player.row+dRow
        playerColumnTo = self._player.column+dColumn

        if self._canPlayerBeMoved(dRow, dColumn):
            box = self.box(playerRowTo, playerColumnTo)

            if box is not None:
                if self._canBoxBeMoved(dRow, dColumn, box):
                    boxRowTo = box.row + dRow
                    boxColumnTo = box.column + dColumn
                    moveBoxToGoal = (boxRowTo, boxColumnTo) in self.goalCoords
                    box.move(dRow, dColumn, moveBoxToGoal, animated)
            movePlayerToGoal = (playerRowTo, playerColumnTo) in self.goalCoords
            self._player.move(dRow, dColumn, movePlayerToGoal, animated)

################################################################################

    def bfs(self, deterministic: bool=True) -> None:
        """
        Launches bfs algorithm to search the level solution.

        :param deterministic: True if directions in the tree are NOT shuffled,
        False otherwise
        :return: None
        """

        self._createGraph()
        self._graph.bfs(deterministic)

################################################################################

    def dfs(self, deterministic: bool=True) -> None:
        """
        Launches dfs algorithm to search the level solution.

        :param deterministic: True if directions in the tree are NOT shuffled,
        False otherwise
        :return: None
        """

        self._createGraph()
        self._graph.dfs(deterministic)

################################################################################

    def _createGraph(self) -> None:
        """
        Creates the graph used for searching the level solution.

        :return: None
        """

        self._graph = Graph(self.state, self.goalCoords, self.wallsCoords)
        self._graph.started.connect(self.algorithmStarted)
        self._graph.finished.connect(self._playSolution)
        self._graph.finished.connect(self.algorithmFinished)

################################################################################

    def _playSolution(self) -> None:
        """
        Plays the solution of the level found by an AI algorithm.

        :return: None
        """

        self.reset()
        self._player.moveFinished.connect(self._nextStep)
        self._nextStep()

################################################################################

    def _nextStep(self) -> None:
        """
        Plays one step in the solution of the level found by an AI algorithm.

        :return: None
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
