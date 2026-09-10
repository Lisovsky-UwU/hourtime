"""Domain-level errors.

Every layer above the domain translates these into its own vocabulary: the API
layer maps them to HTTP status codes, tests assert on the types directly.
"""


class DomainError(Exception):
    """Base class for every error the business rules can raise."""

    code = "domain_error"
    default_message = "Domain error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class ValidationError(DomainError):
    code = "validation_error"
    default_message = "The submitted data is invalid"


class NotFound(DomainError):
    code = "not_found"
    default_message = "Resource not found"


class PermissionDenied(DomainError):
    code = "permission_denied"
    default_message = "Not allowed"


class EmailAlreadyUsed(DomainError):
    code = "email_already_used"
    default_message = "An account with this email already exists"


class InvalidCredentials(DomainError):
    code = "invalid_credentials"
    default_message = "Invalid email or password"


class RegistrationDisabled(DomainError):
    code = "registration_disabled"
    default_message = "Registration is disabled on this instance"


class AccountDisabled(DomainError):
    code = "account_disabled"
    default_message = "This account is disabled"


class InvalidToken(DomainError):
    code = "invalid_token"
    default_message = "Invalid or expired token"


class SessionExpired(InvalidToken):
    code = "session_expired"
    default_message = "The session has expired"


class ProjectNameTaken(DomainError):
    code = "project_name_taken"
    default_message = "A project with this name already exists"


class TimerAlreadyRunning(DomainError):
    code = "timer_already_running"
    default_message = "A timer is already running"
