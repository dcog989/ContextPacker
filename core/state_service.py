from .types import AppState
from .signals import app_signals


class StateService:
    """
    Manages the application's global state machine.
    It is the single source of truth for the application's current state.
    """

    def __init__(self):
        self._current_state = AppState.IDLE
        self._temp_dir: str | None = None
        self._final_output_path: str | None = None

    @property
    def current_state(self) -> AppState:
        return self._current_state

    def set_state(self, new_state: AppState):
        """Atomically sets the new application state and emits a signal."""
        if self._current_state != new_state:
            self._current_state = new_state
            app_signals.state_changed.emit(new_state)

    # Properties for other state variables
    @property
    def temp_dir(self) -> str | None:
        return self._temp_dir

    @temp_dir.setter
    def temp_dir(self, value: str | None):
        self._temp_dir = value

    @property
    def final_output_path(self) -> str | None:
        return self._final_output_path

    @final_output_path.setter
    def final_output_path(self, value: str | None):
        self._final_output_path = value
