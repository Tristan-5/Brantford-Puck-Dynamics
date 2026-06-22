from .base_event import Event

class GoalieDeflection(Event):
    name = "goalie"

    def apply(self, state):
        state.vz += 5.0
        state.vy += 2.0
        return state
