from .base_event import Event

class MissHigh(Event):
    name = "miss_high"

    def apply(self, state):
        state.out_of_play = True
        state.active = False
        return state
