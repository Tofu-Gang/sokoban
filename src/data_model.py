__author__ = 'Tofu Gang'

from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QKeyEvent
from src.level import Level

################################################################################

class DataModel(QGraphicsScene):

################################################################################

    def __init__(self) -> None:
        """
        Creates a data model which is used for a graphic representation of
        Sokoban level (QGraphics View framework). QGraphicsScene.keyPressEvent()
        is implemented to process various player input.
        """

        super().__init__()
        self._level = Level("levels/01/01")
        self.setSceneRect(QRectF(QPointF(0, 0), QPointF(self._level.width, self._level.height)))
        [self.addItem(item) for item in self._level.tiles+self._level.boxes+tuple([self._level.player])]
        self._level.player.moveFinished.connect(self.unlockGame)
        self._gameLock = False

################################################################################

    @property
    def level(self) -> Level:
        """
        :return: current level object
        """

        return self._level

################################################################################

    def lockGame(self) -> None:
        """
        Locks the game to deny the player any input.

        :return: None
        """

        self._gameLock = True

################################################################################

    def unlockGame(self) -> None:
        """
        Unlocks the game to allow the player any input.

        :return: None
        """

        self._gameLock = False

################################################################################

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Handles the player's keyboard input.
        Possible actions:
        -move player up, down, left, right
        -reset level to the initial state
        -start bfs algorithm (deterministic)
        -start bfs algorithm (non-deterministic)
        -start dfs algorithm (deterministic)
        -start dfs algorithm (non-deterministic)
        
        :param event: QKeyEvent to be handled
        :return: None
        """

        if not self._gameLock:
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
