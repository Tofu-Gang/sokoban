__author__ = 'Tofu Gang'

from PyQt5.QtWidgets import QGraphicsObject, QStyleOptionGraphicsItem, QWidget
from PyQt5.QtGui import QPixmap, QPainterPath, QPainter
from PyQt5.QtCore import QPointF, QPropertyAnimation, QRectF, pyqtSignal as Signal
from enum import Enum
from abc import abstractmethod
from res import sokoban_rc

################################################################################

class Tile(QGraphicsObject):
    SIZE = 30 # tile size in pixels
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

    def __init__(self, tileType: Type, row: int, column: int) -> None:
        """
        Sokoban tile representation. Methods are provided for painting the tile
        (from Graphics View framework) and to get the tile row and column number.
        It is not meant to be instantiated directly; instead, it is used as a
        parent class for more specific tile classes.

        :param tileType: value from the enum Type
        :param row: tile row number
        :param column: tile column number
        :return: None
        """

        super().__init__()
        self._tileType = tileType
        self._pixmap = QPixmap(self.PIXMAPS[self._tileType])
        self.setPos(column * self.SIZE, row * self.SIZE)

################################################################################

    def boundingRect(self) -> QRectF:
        """
        Reimplemented QGraphicsObject.boundingRect() method.

        :return: tile bounding rectangle
        """

        return self.BOUNDING_RECT

################################################################################

    def shape(self) -> QPainterPath:
        """
        Reimplemented QGraphicsObject.shape() method.

        :return: tile shape
        """

        return self.SHAPE

################################################################################

    def paint(self,
              painter: QPainter,
              option: QStyleOptionGraphicsItem,
              widget: QWidget=None) -> None:
        """
        Reimplemented QGraphicsObject.paint() method.

        :param painter: QPainter object used for drawing the tile
        :param option: Qt black magic, unused
        :param widget: Qt black magic, unused
        :return: None
        """

        painter.drawPixmap(QPointF(0, 0), self._pixmap)

################################################################################

    @property
    def row(self) -> int:
        """
        :return: tile row number
        """

        return self.pos().y() / self.SIZE

################################################################################

    @property
    def column(self) -> int:
        """
        :return: tile column number
        """

        return self.pos().x() / self.SIZE

################################################################################

class PassiveTile(Tile):
    Z_VALUE = 0

################################################################################

    def __init__(self, tileType: Tile.Type, row: int, column: int) -> None:
        """
        Implementation of floor, wall and background tiles. Methods are provided
        to tell if the tile is a floor or a goal floor tile.

        :param tileType: value from the enum Type
        :param row: tile row number
        :param column: tile column number
        :return: None
        """

        super().__init__(tileType, row, column)
        self.setZValue(self.Z_VALUE)

################################################################################

    @property
    def isFloor(self) -> bool:
        """
        Indicates if this is a floor tile.

        :return: True if this is a floor tile or a goal one, False otherwise
        """

        return self._tileType in (Tile.Type.GOAL, Tile.Type.FLOOR)

################################################################################

    @property
    def isGoal(self) -> bool:
        """
        Indicates if this is a goal floor tile.

        :return: True if this is a goal floor tile, False otherwise
        """

        return self._tileType == self.Type.GOAL

################################################################################

class ActiveTile(Tile):
    ANIMATION_DURATION = 200
    Z_VALUE = 1

################################################################################

    def __init__(self, tileType: Tile.Type, row: int, column: int) -> None:
        """
        Player/box representation. Methods are provided for moving by one tile
        in a specified direction and for moving anywhere in the board. It is not
        meant to be instantiated directly; instead, it is used as a parent class
        for Player and Box classes.

        :param tileType: value from the enum Type
        :param row: tile row number
        :param column: tile column number
        :return: None
        """

        super().__init__(tileType, row, column)
        self.setZValue(self.Z_VALUE)
        self._animation = QPropertyAnimation(self, b'pos')
        self._animation.setDuration(self.ANIMATION_DURATION)

################################################################################

    def move(self, dRow: int, dColumn: int, moveToGoal: bool, animated: bool=False) -> None:
        """
        Moves the tile in the specified direction by one tile. Makes no checks
        if it is actually possible.

        :param dRow: number of rows to move (negative is up, positive is down)
        :param dColumn: number of columns to move (negative is left, positive is
        right)
        :param moveToGoal True if the target tile is a goal tile, False
        otherwise (used for choosing the correct pixmap)
        :param animated: True if the move should be animated, False if not
        :return: None
        """

        endPos = QPointF((self.column+dColumn)*self.SIZE,
                         (self.row+dRow)*self.SIZE)

        if animated:
            self.scene().lockGame()
            self._animation.setStartValue(self.pos())
            self._animation.setEndValue(endPos)
            self._animation.start()
        else:
            self.setPos(endPos)
        self.updatePixmap(moveToGoal)

################################################################################

    def setCoords(self, row: int, column: int, moveToGoal: bool) -> None:
        """
        Moves the tile to the specified place in the board. Makes no checks if
        it is actually possible.

        :param row: target tile row number
        :param column: target tile column number
        :param moveToGoal: True if the target tile is a goal tile, False
        otherwise (used for choosing the correct pixmap)
        :return: None
        """

        self.setPos(QPointF(column*self.SIZE, row*self.SIZE))
        self.updatePixmap(moveToGoal)

################################################################################

    @abstractmethod
    def updatePixmap(self, moveToGoal: bool) -> None:
        """
        Reimplemented in child classes Player and Box.

        :param moveToGoal: unused
        :return: None
        """

        pass

################################################################################

class Player(ActiveTile):
    moveFinished = Signal()

################################################################################

    def __init__(self, row: int, column: int, isOnGoal: bool) -> None:
        """
        Player tile implementation. Method is provided for updating its pixmap
        according to the tile the player is on (goal or non-goal floor tile).

        :param row: tile row number
        :param column: tile column number
        :param isOnGoal: True if the player is initially placed on a goal tile,
        False otherwise (used for choosing the correct pixmap)
        :return: None
        """

        if isOnGoal:
            super().__init__(Tile.Type.PLAYER_ON_GOAL, row, column)
        else:
            super().__init__(Tile.Type.PLAYER, row, column)
        self._animation.finished.connect(self.moveFinished)

################################################################################

    def updatePixmap(self, isOnGoal: bool) -> None:
        """
        Reimplemented abstract method ActiveTile.updatePixmap().
        Updates the pixmap accordingly to the tile the player is on (goal or
        non-goal floor tile).

        :param isOnGoal: True if the player is initially placed on a goal tile,
        False otherwise (used for choosing the correct pixmap)
        :return: None
        """

        if isOnGoal:
            self._pixmap = QPixmap(self.PIXMAPS[self.Type.PLAYER_ON_GOAL])
        else:
            self._pixmap = QPixmap(self.PIXMAPS[self.Type.PLAYER])
        self.update()

################################################################################

class Box(ActiveTile):

################################################################################

    def __init__(self, row: int, column: int, isOnGoal: bool) -> None:
        """
        Box tile implementation. Method is provided for updating its pixmap
        according to the tile the box is on (goal or non-goal floor tile).

        :param row: tile row number
        :param column: tile column number
        :param isOnGoal: True if the box is initially placed on a goal tile,
        False otherwise (used for choosing the correct pixmap)
        :return: None
        """

        if isOnGoal:
            super().__init__(Tile.Type.BOX_ON_GOAL, row, column)
        else:
            super().__init__(Tile.Type.BOX, row, column)

################################################################################

    def updatePixmap(self, isOnGoal: bool) -> None:
        """
        Reimplemented abstract method ActiveTile.updatePixmap().
        Updates the pixmap accordingly to the tile the box is on (goal or
        non-goal floor tile).

        :param isOnGoal: True if the box is initially placed on a goal tile,
        False otherwise (used for choosing the correct pixmap)
        :return: None
        """

        if isOnGoal:
            self._pixmap = QPixmap(self.PIXMAPS[self.Type.BOX_ON_GOAL])
        else:
            self._pixmap = QPixmap(self.PIXMAPS[self.Type.BOX])
        self.update()

################################################################################