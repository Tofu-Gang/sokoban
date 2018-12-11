__author__ = 'Tofu Gang'

from PyQt5.QtWidgets import QGraphicsObject
from PyQt5.QtGui import QPixmap, QPainterPath
from PyQt5.QtCore import QPointF, QPropertyAnimation, QRectF, pyqtSignal as Signal
from enum import Enum
from res import sokoban_rc

################################################################################

class Tile(QGraphicsObject):
    SIZE = 30
    BOUNDING_RECT = QRectF(QPointF(0, 0), QPointF(SIZE, SIZE))
    SHAPE = QPainterPath()
    SHAPE.addRect(BOUNDING_RECT)
    Z_VALUE = 0

    class Type(Enum):
        WALL = '#'
        PLAYER = '@'
        PLAYER_ON_GOAL = '+'
        BOX = '$'
        BOX_ON_GOAL = '*'
        GOAL = '.'
        FLOOR = ' '
        BACKGROUND = 'x'

    PIXMAPS = {
        Type.WALL: ':/wall.png',
        Type.PLAYER: ':/player.png',
        Type.PLAYER_ON_GOAL: ':/player_on_goal.png',
        Type.BOX: ':/box.png',
        Type.BOX_ON_GOAL: ':/box_on_goal.png',
        Type.GOAL: ':/goal.png',
        Type.FLOOR: ':/floor.png',
        Type.BACKGROUND: ':/background.png'
    }

################################################################################

    def __init__(self, tileType, row, column):
        """
        Basic Sokoban tile representation which knows how to paint itself in the
        scene and its position in the grid.
        :param tileType: value from the enum Type
        :param row: number of the row in the grid
        :param column: number of the column in the grid
        """

        super().__init__()
        self._pixmap = QPixmap(self.PIXMAPS[tileType])
        self._row = row
        self._column = column
        self.setZValue(self.Z_VALUE)

################################################################################

    def boundingRect(self):
        """
        Reimplemented QGraphicsObject.boundingRect() method.
        """

        return self.BOUNDING_RECT

################################################################################

    def shape(self):
        """
        Reimplemented QGraphicsObject.shape() method.
        """

        return self.SHAPE

################################################################################

    def paint(self, painter, option, widget=None):
        """
        Reimplemented QGraphicsObject.paint() method.

        """

        painter.drawPixmap(QPointF(0, 0), self._pixmap)

################################################################################

    @property
    def row(self):
        """
        :return: number of the row in the grid
        """

        return self._row

################################################################################

    @property
    def column(self):
        """
        :return: number of the column in the grid
        """

        return self._column

################################################################################

class PassiveTile(Tile):

################################################################################

    def __init__(self, tileType, row, column):
        """
        Background and wall tiles implementation.
        :param tileType: value from the enum Type
        :param row: number of the row in the grid
        :param column: number of the column in the grid
        """

        super().__init__(tileType, row, column)
        self._tileType = tileType

################################################################################

    @property
    def tileType(self):
        """
        :return: value from the enum Type
        """

        return self._tileType

################################################################################

    @property
    def isFloor(self):
        """
        Indicates if it is possible to move a player or push a box here.
        :return: always False
        """

        return False

################################################################################

class Floor(Tile):

################################################################################

    def __init__(self, tileType, row, column):
        """
        Floor tile implementation.
        :param tileType: value from the enum Type
        :param row: number of the row in the grid
        :param column: number of the column in the grid
        """

        super().__init__(tileType, row, column)
        if tileType in (self.Type.FLOOR, self.Type.PLAYER, self.Type.BOX):
            self._pixmap = QPixmap(self.PIXMAPS[self.Type.FLOOR])
            self.update()
        elif tileType in (self.Type.GOAL, self.Type.PLAYER_ON_GOAL, self.Type.BOX_ON_GOAL):
            self._pixmap = QPixmap(self.PIXMAPS[self.Type.GOAL])
            self.update()
        self._hasBox = tileType in (self.Type.BOX, self.Type.BOX_ON_GOAL)
        self._hasPlayer = tileType in (self.Type.PLAYER, self.Type.PLAYER_ON_GOAL)
        self._isGoal = tileType in (self.Type.GOAL, self.Type.BOX_ON_GOAL, self.Type.PLAYER_ON_GOAL)

################################################################################

    @property
    def tileType(self):
        """
        :return: value from the enum Type
        """

        if self.hasBox:
            if self.isGoal:
                return self.Type.BOX_ON_GOAL
            else:
                return self.Type.BOX
        elif self.hasPlayer:
            if self.isGoal:
                return self.Type.PLAYER_ON_GOAL
            else:
                return self.Type.PLAYER
        else:
            if self.isGoal:
                return self.Type.GOAL
            else:
                return self.Type.FLOOR

################################################################################

    @property
    def isFloor(self):
        """
        Indicates if it is possible to move a player or push a box here.
        :return: always True
        """

        return True

################################################################################

    @property
    def isGoal(self):
        """
        Indicates if this is a goal tile.
        :return: True if this is a goal tile, False otherwise
        """

        return self._isGoal

################################################################################

    @property
    def hasBox(self):
        """
        Indicates if there is a box on this tile.
        :return: True if there is a box on this tile, False otherwise
        """

        return self._hasBox

################################################################################

    def pushBoxOut(self):
        """
        Updates information about box being on this tile.
        """

        self._hasBox = False

################################################################################

    def pushBoxIn(self):
        """
        Updates information about box being on this tile.
        """

        self._hasBox = True

################################################################################

    @property
    def hasPlayer(self):
        """
        Indicates if there is the player on this tile.
        :return: True if there is the player on this tile, False otherwise
        """

        return self._hasPlayer

################################################################################

    def movePlayerOut(self):
        """
        Updates information about the player being on this tile.
        """

        self._hasPlayer = False

################################################################################

    def movePlayerIn(self):
        """
        Updates information about the player being on this tile.
        """

        self._hasPlayer = True

################################################################################

class ActiveTile(Tile):
    ANIMATION_DURATION = 200
    Z_VALUE = 1

################################################################################

    def __init__(self, level, tileType, row, column):
        """

        :param level: Level object to see what is around
        :param tileType: value from the enum Type
        :param row: number of the row in the grid
        :param column: number of the column in the grid
        """

        super().__init__(tileType, row, column)
        self._animation = QPropertyAnimation(self, b'pos')
        self._animation.setDuration(self.ANIMATION_DURATION)
        self._level = level

################################################################################

    def setCoords(self, row, column, animated=False):
        """

        :param row:
        :param column:
        :return:
        """

        self._row = row
        self._column = column
        endPos = QPointF(column*self.SIZE, row*self.SIZE)
        if animated:
            self._animation.setStartValue(self.pos())
            self._animation.setEndValue(endPos)
            self._animation.start()
        else:
            self.setPos(endPos)

################################################################################

class Player(ActiveTile):
    moveFinished = Signal()

################################################################################

    def __init__(self, level, tileType, row, column):
        """

        :param level: Level object to see what is around
        :param tileType: value from the enum Type
        :param row: number of the row in the grid
        :param column: number of the column in the grid
        """

        super().__init__(level, tileType, row, column)
        self._animation.finished.connect(self.moveFinished)

################################################################################

    def setCoords(self, row, column, animated=False):
        """

        :param row:
        :param column:
        :return:
        """

        tileFrom = self._level.tileOnCoords(self._row, self._column)
        tileFrom.movePlayerOut()
        tileTo = self._level.tileOnCoords(row, column)
        tileTo.movePlayerIn()
        if tileTo.isGoal:
            self._pixmap = QPixmap(self.PIXMAPS[self.Type.PLAYER_ON_GOAL])
        else:
            self._pixmap = QPixmap(self.PIXMAPS[self.Type.PLAYER])
        self.update()

        super().setCoords(row, column, animated)

################################################################################

    def canBeMoved(self, dRow, dColumn):
        """
        Indicates whether the player can be moved in the specified direction.
        :param dRow: number of rows to move (negative is up, positive is down)
        :param dColumn: number of columns to move (negative is left, positive is
        right)
        :return: True if the target tile is a floor/goal tile without a box or
        if the box can be pushed aside on a free floor/goal tile, False
        otherwise.
        """

        rowTo = self._row+dRow
        columnTo = self._column+dColumn
        tileTo = self._level.tileOnCoords(rowTo, columnTo)
        if tileTo.isFloor:
            if tileTo.hasBox:
                return self._level.box(rowTo, columnTo).canBeMoved(dRow, dColumn)
            else:
                return True
        else:
            return False

################################################################################

    def move(self, dRow, dColumn, animated=False):
        """
        Moves the player in the specified direction. Makes no checks if it is
        actually possible.
        :param dRow: number of rows to move (negative is up, positive is down)
        :param dColumn: number of columns to move (negative is left, positive is
        right)
        """

        rowTo = self._row+dRow
        columnTo = self._column+dColumn
        tileTo = self._level.tileOnCoords(rowTo, columnTo)
        if tileTo.hasBox:
            box = self._level.box(rowTo, columnTo)
            box.move(dRow, dColumn, animated)
        if animated:
            self.scene().lockMoving()
        self.setCoords(rowTo, columnTo, animated)

################################################################################

class Box(ActiveTile):

################################################################################

    def setCoords(self, row, column, animated=False):
        """

        :param row:
        :param column:
        :return:
        """

        tileFrom = self._level.tileOnCoords(self._row, self._column)
        tileFrom.pushBoxOut()
        tileTo = self._level.tileOnCoords(row, column)
        tileTo.pushBoxIn()
        if tileTo.isGoal:
            self._pixmap = QPixmap(self.PIXMAPS[self.Type.BOX_ON_GOAL])
        else:
            self._pixmap = QPixmap(self.PIXMAPS[self.Type.BOX])
        self.update()

        super().setCoords(row, column, animated)

################################################################################

    def canBeMoved(self, dRow, dColumn):
        """
        Indicates whether the box can be pushed in the specified direction.
        :param dRow: number of rows to move (negative is up, positive is down)
        :param dColumn: number of columns to move (negative is left, positive is
        right)
        :return: True if the target tile is a floor/goal tile without a box,
        False otherwise.
        """

        rowTo = self._row+dRow
        columnTo = self._column+dColumn
        tileTo = self._level.tileOnCoords(rowTo, columnTo)
        if tileTo.isFloor:
            return not tileTo.hasBox
        else:
            return False

################################################################################

    def move(self, dRow, dColumn, animated=False):
        """
        Moves the box in the specified direction. Makes no checks if it is
        actually possible.
        :param dRow: number of rows to move (negative is up, positive is down)
        :param dColumn: number of columns to move (negative is left, positive is
        right)
        """

        rowTo = self._row+dRow
        columnTo = self._column+dColumn
        self.setCoords(rowTo, columnTo, animated)

################################################################################
