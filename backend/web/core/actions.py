"""Small reusable dialog actions (ConfirmAction with fixed text)."""
from .mixins import ActionView


class ConfirmView(ActionView):
    """A ConfirmAction whose dialog is just title + description (+ colour)."""

    title = ""
    description = ""
    color = None
    confirm_label = None

    def get_title(self):
        return self.title

    def get_description(self):
        return self.description

    def dialog_context(self):
        return {"title": self.get_title(), "description": self.get_description(), "color": self.color,
                "confirm_label": self.confirm_label}
