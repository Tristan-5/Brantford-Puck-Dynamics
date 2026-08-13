"""Arena feature package.

Importing each feature module here ensures they are loaded and registered
when the rink discovers available arena features.
"""

from .benches import Benches
from .blue_line import BlueLines
from .boards import Boards
from .crease import Crease
from .faceoff_circle import FaceoffCircles
from .faceoff_dot import FaceoffDots
from .glass import Glass
from .goal import Goals
from .goal_line import GoalLines
from .netting import Netting
from .penalty_boxes import PenaltyBoxes
from .red_line import CenterRedLine
from .rink_surface import RinkSurface
from .seating import Seating
from .trapezoid import Trapezoid

__all__ = [
    "Benches",
    "BlueLines",
    "Boards",
    "Crease",
    "FaceoffCircles",
    "FaceoffDots",
    "Glass",
    "Goals",
    "GoalLines",
    "Netting",
    "PenaltyBoxes",
    "CenterRedLine",
    "RinkSurface",
    "Seating",
    "Trapezoid",
]
