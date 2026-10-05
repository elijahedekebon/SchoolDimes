import re

from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication

# Part 4A: endpoints a `student`-role login may call. Everything else is 403.
# Many Part 1/2 querysets scope every non-parent role to "own school" (they
# were written for staff), so a student login must never reach them.
STUDENT_ALLOWED_PATHS = re.compile(
    r"^/api/v1/(me|auth/(refresh|logout)|my-school/?|student-portal/me/?|financial-literacy-tips/(\d+/)?)$"
)


class SchoolDimesJWTAuthentication(JWTAuthentication):
    """simplejwt + the student-role allowlist above."""

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is not None:
            user, _token = result
            if getattr(user, "role", None) == "student" and not STUDENT_ALLOWED_PATHS.match(request.path):
                raise PermissionDenied("Student portal accounts can only use the student portal.")
        return result
