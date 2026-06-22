from .base_event import Event

class MissWide(Event):
    name = "miss_wide"

    def apply(self, state):
        state.out_of_play = True
        state.active = False
        return state
