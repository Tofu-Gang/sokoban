__author__ = 'Tofu Gang'

from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtCore import QPointF, QRectF, Qt
from src.level import Level

################################################################################

class DataModel(QGraphicsScene):

################################################################################

    def __init__(self):
        """

        """

        super().__init__()
        self._level = Level()
        width = self._level.width
        height = self._level.height
        self.setSceneRect(QRectF(QPointF(0, 0), QPointF(width, height)))
        [self.addItem(item) for item in self._level.tiles+self._level.boxes+[self._level.player]]
        self._level.player.moveFinished.connect(self.unlockMoving)
        self._moveLock = False

################################################################################

    @property
    def level(self):
        """

        :return:
        """

        return self._level

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

    def keyPressEvent(self, event):
        """

        """

        if not self._moveLock:
            key = event.key()
            if key in self._level.DIRECTIONS:
                dRow = self._level.DIRECTIONS[key][0]
                dColumn = self._level.DIRECTIONS[key][1]
                self._level.movePlayer(dRow, dColumn, animated=True)
            elif key == Qt.Key_R:
                self._level.reset()
            elif key == Qt.Key_B:
                if event.modifiers() == Qt.ShiftModifier:
                    self._level.bfs(deterministic=False)
                else:
                    self._level.bfs()
            elif key == Qt.Key_D:
                if event.modifiers() == Qt.ShiftModifier:
                    self._level.dfs(deterministic=False)
                else:
                    self._level.dfs()
        super().keyPressEvent(event)

################################################################################
