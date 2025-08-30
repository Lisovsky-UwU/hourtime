from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from .link_user_organization import LinkUserOrganizationORM  # noqa: F401
from .organization import OrganizationORM  # noqa: F401
from .project import ProjectORM  # noqa: F401
from .task import TaskORM  # noqa: F401
from .time_entry import TimeEntryORM  # noqa: F401
from .user import UserORM  # noqa: F401
from .user_token import UserTokenORM  # noqa: F401
from .workspace import WorkspaceORM  # noqa: F401

