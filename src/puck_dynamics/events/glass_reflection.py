from .base_event import Event

class GlassImpact(Event):
    name = "glass"

    def __init__(self, restitution=0.85):
        self.e = restitution

    def apply(self, state):
        state.vx = -self.e * state.vx
        return state
