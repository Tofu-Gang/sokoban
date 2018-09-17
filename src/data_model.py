__author__ = 'Tofu Gang'

from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtCore import QPointF, QRectF, Qt
from src.tile import Tile, PassiveTile, Floor, Player, Box
from pickle import dump, load

################################################################################

class DataModel(QGraphicsScene):

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

    def __init__(self, level=None):
        """

        """

        if not level:
            with open('res/levels/world_01/01', 'rb') as f:
                self._level = load(f)

        super().__init__()
        width = len(self._level[0])*Tile.SIZE
        height = len(self._level)*Tile.SIZE
        self.setSceneRect(QRectF(QPointF(-width/2, -height/2), QPointF(width/2, height/2)))

        self._moveLock = False
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
                        self._player = Player(tileType, rowNumber, columnNumber)
                        self._player.setPos(self.sceneRect().left()+columnNumber*Tile.SIZE,
                                            self.sceneRect().top()+rowNumber*Tile.SIZE)
                        self.addItem(self._player)
                    elif tileType in (Tile.Type.BOX, Tile.Type.BOX_ON_GOAL):
                        box = Box(tileType, rowNumber, columnNumber)
                        box.setPos(self.sceneRect().left()+columnNumber*Tile.SIZE,
                                   self.sceneRect().top()+rowNumber*Tile.SIZE)
                        self.addItem(box)
                        self._boxes.append(box)
                    tile = Floor(tileType, rowNumber, columnNumber)
                tile.setPos(self.sceneRect().left()+columnNumber*Tile.SIZE,
                            self.sceneRect().top()+rowNumber*Tile.SIZE)
                self.addItem(tile)
                self._tiles.append(tile)

################################################################################

    def lockMoving(self):
        """

        :return:
        """

        self._moveLock = True

################################################################################

    def unlockMoving(self):
        """

        :return:
        """

        self._moveLock = False

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

    def _movePlayer(self, dRow, dColumn):
        """

        :param dRow:
        :param dColumn:
        :return:
        """

        if self._player.canBeMoved(dRow, dColumn):
            self._player.move(dRow, dColumn)
            self.lockMoving()

################################################################################

    def keyPressEvent(self, event):
        """

        """

        if not self._moveLock:
            key = event.key()
            if key == Qt.Key_Up:
                self._movePlayer(-1, 0)
            elif key == Qt.Key_Down:
                self._movePlayer(1, 0)
            elif key == Qt.Key_Left:
                self._movePlayer(0, -1)
            elif key == Qt.Key_Right:
                self._movePlayer(0, 1)
        super().keyPressEvent(event)

################################################################################
