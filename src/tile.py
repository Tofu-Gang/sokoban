__author__ = 'Tofu Gang'

from PyQt5.QtWidgets import QGraphicsObject
from PyQt5.QtGui import QPixmap, QPainterPath
from PyQt5.QtCore import QPointF, QPropertyAnimation, QRectF
from enum import Enum
import sokoban_rc

################################################################################

class Tile(QGraphicsObject):
    SIZE = 30
    BOUNDING_RECT = QRectF(QPointF(0, 0), QPointF(SIZE, SIZE))
    SHAPE = QPainterPath()
    SHAPE.addRect(BOUNDING_RECT)

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
        self.setZValue(0)
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
        self.setZValue(0)
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

class Player(Tile):

################################################################################

    def __init__(self, tileType, row, column):
        """
        Player implementation.
        :param tileType: value from the enum Type
        :param row: number of the row in the grid
        :param column: number of the column in the grid
        """

        super().__init__(tileType, row, column)
        self.setZValue(100)
        self._animation = QPropertyAnimation(self, b'pos')
        self._animation.setDuration(50)

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
        tileTo = self.scene().tileOnCoords(rowTo, columnTo)
        if tileTo.isFloor:
            if tileTo.hasBox:
                rowTo2 = self._row + 2*dRow
                columnTo2 = self._column + 2*dColumn
                tileTo2 = self.scene().tileOnCoords(rowTo2, columnTo2)
                return tileTo2.isFloor and not tileTo2.hasBox
            else:
                return True
        else:
            return False

################################################################################

    def move(self, dRow, dColumn):
        """
        Moves the player in the specified direction. Makes no checks if it is
        actually possible.
        :param dRow: number of rows to move (negative is up, positive is down)
        :param dColumn: number of columns to move (negative is left, positive is
        right)
        """

        rowTo = self._row+dRow
        columnTo = self._column+dColumn
        tile = self.scene().tileOnCoords(self._row, self._column)
        tileTo = self.scene().tileOnCoords(rowTo, columnTo)
        if tileTo.hasBox:
            box = self.scene().box(rowTo, columnTo)
            box.move(dRow, dColumn)
        self._animation.setStartValue(self.pos())
        self._animation.setEndValue(tileTo.pos())
        self._animation.finished.connect(self.scene().unlockMoving)
        self._animation.start()
        self._row += dRow
        self._column += dColumn
        tile.movePlayerOut()
        tileTo.movePlayerIn()
        if tileTo.isGoal:
            self._pixmap = QPixmap(self.PIXMAPS[self.Type.PLAYER_ON_GOAL])
        else:
            self._pixmap = QPixmap(self.PIXMAPS[self.Type.PLAYER])
        self.update()

################################################################################

class Box(Tile):

################################################################################

    def __init__(self, tileType, row, column):
        """
        Box implementation.
        :param tileType: value from the enum Type
        :param row: number of the row in the grid
        :param column: number of the column in the grid
        """

        super().__init__(tileType, row, column)
        self.setZValue(100)
        self._animation = QPropertyAnimation(self, b'pos')
        self._animation.setDuration(50)

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
        tileTo = self.scene().tileOnCoords(rowTo, columnTo)
        if tileTo.isFloor:
            return not tileTo.hasBox
        else:
            return False

################################################################################

    def move(self, dRow, dColumn):
        """
        Moves the box in the specified direction. Makes no checks if it is
        actually possible.
        :param dRow: number of rows to move (negative is up, positive is down)
        :param dColumn: number of columns to move (negative is left, positive is
        right)
        """

        rowTo = self._row+dRow
        columnTo = self._column+dColumn
        tile = self.scene().tileOnCoords(self._row, self._column)
        tileTo = self.scene().tileOnCoords(rowTo, columnTo)
        self._animation.setStartValue(self.pos())
        self._animation.setEndValue(tileTo.pos())
        self._animation.start()
        self._row += dRow
        self._column += dColumn
        tile.pushBoxOut()
        tileTo.pushBoxIn()
        if tileTo.isGoal:
            self._pixmap = QPixmap(self.PIXMAPS[self.Type.BOX_ON_GOAL])
        else:
            self._pixmap = QPixmap(self.PIXMAPS[self.Type.BOX])
        self.update()

################################################################################
