"""This is a GUI to display the board of Reversi."""

from logging import getLogger
import wx

from .color import color_pallet as cp
from .menu import MenuBar

logger = getLogger(__name__)

__all__ = ["MyFrame"]


class MyFrame(wx.Frame):
    """Make frame for GUI."""
    def __init__(
            self, parent=None, id=-1, title=None,
            size=(640, 480), othello=None,
            ):
        wx.Frame.__init__(self, parent, id, title, size=size)
        self.othello = othello
        self.result = False
        self.update = True

        # Initialize status bar
        self.CreateStatusBar()
        self.SetStatusText("status bar")
        self.GetStatusBar().SetBackgroundColour(None)

        # Initialize menu bar
        self.SetMenuBar(MenuBar(self))

        # Set panels
        self._game_panel = GamePanel(self)
        self._user_panel = UserPanel(self)
        layout = wx.BoxSizer(wx.HORIZONTAL)
        layout.Add(self._game_panel, proportion=3, flag=wx.EXPAND)
        layout.Add(self._user_panel, proportion=1, flag=wx.EXPAND)
        self.SetSizer(layout)

        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)
        self._timer.Start(100)
        self.user_auto = False
        logger.info("GUI for the board was set.")

    def on_timer(self, event):
        self.result, self.update = self.othello.process_game()
        # time.sleep(0.5)
        # logger.debug("Frame update.")


class GamePanel(wx.Panel):

    def __init__(self, frame):
        wx.Panel.__init__(self, frame)
        self.SetBackgroundColour("white")
        self._frame = frame
        self._disks = [[None for _ in range(8)] for _ in range(8)]
        self._position = [
            [(row*30, column*30) for column in range(8)]
            for row in range(8)
            ]
        self._line_position = [[0 for _ in range(9)] for _ in range(2)]

        # Set board and disks
        for row in range(8):
            for column in range(8):
                self._disks[row][column] = Disk()
        self._square = SquareMap()

        self._client_DC = wx.ClientDC(self)
        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self._timer.Start(100)

    def on_left_down(self, event):
        """If a disk area was clicked, return the position of disk."""
        logger.info("Mouse bottun was put.")
        different = self._line_position[0][1] - self._line_position[0][0]
        select_x = (event.X - self._line_position[0][0])//different
        select_y = (event.Y - self._line_position[1][0])//different
        try:
            self._frame.othello.play_turn(int(select_x*8 + select_y))
        except AssertionError:
            self._frame.SetStatusText("This position is out of the board.")
        except ValueError:
            self._frame.SetStatusText("You can not reverse disks.")
        else:
            self._frame.SetStatusText("Success.")

    def update_data(self):
        """Get the size of panel and calculate the size of board."""
        width, height = self.GetSize()
        BOARD_SIZE = min(width, height)*0.7
        DISK_SIZE = (BOARD_SIZE/7)*0.7/2
        self._board = self._frame.othello.display_board()

        self._width = width
        self._height = height
        self._BOARD_SIZE = BOARD_SIZE
        self._DISK_SIZE = DISK_SIZE
        self._position = [
            [
                (
                    width/2 - BOARD_SIZE/2 + row*BOARD_SIZE/7,
                    height/2 - BOARD_SIZE/2 + column*BOARD_SIZE/7
                    )
                for column in range(8)] for row in range(8)
            ]
        self._line_position = [
            [width/2 + (x-4)*BOARD_SIZE/7 for x in range(9)],
            [height/2 + (x-4)*BOARD_SIZE/7 for x in range(9)]
        ]

    def draw_board(self):
        """Determine disks" position and draw area."""
        self._bit_map = wx.Bitmap(self._width, self._height)
        self._buffer_DC = wx.BufferedDC(self._client_DC, self._bit_map)
        self._buffer_DC.Clear()

        self._square.draw(self._buffer_DC, self._line_position)
        for row in range(8):
            for column in range(8):
                if self._board[row][column] == 1:
                    self._disks[row][column].draw(
                        cp.CLR_BLACK_DISK,
                        self._buffer_DC,
                        self._position[row][column],
                        self._DISK_SIZE,
                        )
                elif self._board[row][column] == -1:
                    self._disks[row][column].draw(
                        cp.CLR_WHITE_DISK,
                        self._buffer_DC,
                        self._position[row][column],
                        self._DISK_SIZE,
                        )
                else:
                    self._disks[row][column].draw(
                        cp.CLR_BOARD,
                        self._buffer_DC,
                        self._position[row][column],
                        self._DISK_SIZE,
                        )
        self._client_DC.DrawBitmap(self._bit_map, 0, 0)

    def on_timer(self, event):
        self.update_data()
        self.draw_board()
        # logger.debug("Panel update.")


class UserPanel(wx.Panel):
    def __init__(self, frame):
        super().__init__()
        wx.Panel.__init__(self, frame)
        self._frame = frame

        self._user_point_panel = PointPanel(self, frame, cp.CLR_PANEL_USER, 1)
        self._opp_point_panel = PointPanel(self, frame, cp.CLR_PANEL_CPU, 0)
        self._result_panel = ResultPanel(self, frame)

        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(self._user_point_panel, proportion=1, flag=wx.EXPAND)
        layout.Add(self._opp_point_panel, proportion=1, flag=wx.EXPAND)
        layout.Add(self._result_panel, proportion=1, flag=wx.EXPAND)
        self.SetSizer(layout)

        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)
        self._timer.Start(100)

    def on_timer(self, event):
        """Determine disks' position and draw area."""
        [player, opponent] = self._frame.othello.update_count()
        self._user_point_panel.draw(player)
        self._opp_point_panel.draw(opponent)
        self._result_panel.draw()


class PointPanel(wx.Panel):
    def __init__(self, panel, frame, back_clr: str, is_player: int):
        super().__init__()
        wx.Panel.__init__(self, panel)
        self.SetBackgroundColour(back_clr)
        self._is_player = is_player
        self._frame = frame
        if is_player == 1:
            self._text = "You"
        else:
            self._text = "CPU"
        self._client_DC = wx.ClientDC(self)

    def draw(self, point: int):
        """Show each player's points."""
        width, height = self.GetSize()
        size = min(width, height)
        if self._is_player ^ self._frame.othello._player_clr:
            color = cp.CLR_BLACK_DISK
        else:
            color = cp.CLR_WHITE_DISK

        self._bit_map = wx.Bitmap(width, height)
        self._buffer_DC = wx.BufferedDC(self._client_DC, self._bit_map)
        self._buffer_DC.Clear()

        self._buffer_DC.SetPen(wx.Pen(color))
        self._buffer_DC.SetBrush(wx.Brush(color))
        self._buffer_DC.DrawCircle(width/3, height/2, size*0.2)

        self._buffer_DC.SetFont(
            wx.Font(
                size*0.175,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL,
                ))
        self._buffer_DC.DrawText("×" + str(point), width*0.55, height/2)
        self._buffer_DC.DrawText(self._text, width*0.55, height*0.3)

        self._client_DC.DrawBitmap(self._bit_map, 0, 0)


class ResultPanel(wx.Panel):
    def __init__(self, panel, frame):
        super().__init__()
        wx.Panel.__init__(self, panel)
        self._frame = frame
        self._text = ""
        self._client_DC = wx.ClientDC(self)

    def draw(self):
        width, height = self.GetSize()
        size = min(width, height)
        if self._frame.result:
            self._text = self._frame.othello.result
        else:
            self._text = ""

        self._bit_map = wx.Bitmap(width, height)
        self._buffer_DC = wx.BufferedDC(self._client_DC, self._bit_map)
        self._buffer_DC.Clear()

        self._buffer_DC.SetPen(wx.Pen("black"))
        self._buffer_DC.SetBrush(wx.Brush("black"))
        self._buffer_DC.SetFont(
            wx.Font(
                size*0.175,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_NORMAL
                ))
        self._buffer_DC.DrawText(self._text, width*0.5, height/2)

        self._client_DC.DrawBitmap(self._bit_map, 0, 0)


class Disk(object):

    def __init__(self):
        return

    def draw(self, color: str, buffer_DC, position: tuple, size: float):
        buffer_DC.SetPen(wx.Pen(color))
        buffer_DC.SetBrush(wx.Brush(color))
        buffer_DC.DrawCircle(position, size)


class SquareMap(object):
    def __init__(self):
        return

    def draw(self, buffer_DC, line_position: list):
        edge_length = line_position[0][-1] - line_position[0][0]

        buffer_DC.SetPen(wx.Pen(cp.CLR_BOARD_EDGE))
        buffer_DC.SetBrush(wx.Brush(cp.CLR_BOARD_EDGE))
        buffer_DC.DrawRectangle(
            line_position[0][0] - edge_length*0.05,
            line_position[1][0] - edge_length*0.05,
            edge_length*1.1, edge_length*1.1
            )
        buffer_DC.SetPen(wx.Pen(cp.CLR_BOARD))
        buffer_DC.SetBrush(wx.Brush(cp.CLR_BOARD))
        buffer_DC.DrawRectangle(
            line_position[0][0] - edge_length*0.025,
            line_position[1][0] - edge_length*0.025,
            edge_length*1.05, edge_length*1.05
            )

        buffer_DC.SetPen(wx.Pen(cp.CLR_BOARD_LINE))
        buffer_DC.SetBrush(wx.Brush(cp.CLR_BOARD_LINE))
        for row in range(9):
            for column in range(9):
                buffer_DC.DrawLine(
                    line_position[0][row], line_position[1][0],
                    line_position[0][row], line_position[1][-1]
                    )
                buffer_DC.DrawLine(
                    line_position[0][0], line_position[1][column],
                    line_position[0][-1], line_position[1][column]
                    )
        for row in range(1, 8):
            for column in range(1, 8):
                buffer_DC.DrawCircle(
                    line_position[0][row],
                    line_position[1][column],
                    edge_length*0.005,
                    )
