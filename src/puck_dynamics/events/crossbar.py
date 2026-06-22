from .base_event import Event

class CrossbarDeflection(Event):
    name = "crossbar"

    def apply(self, state):
        state.vz = abs(state.vz) + 3.0
        return state
