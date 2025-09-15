class CacheConst:
    class User:
        AuthToken = "user:auth:token:{}"
        class Model:
            ById = "user:model:id:{}"
            ByUsername = "user:model:username:{}"

    class Organization:
        NamespaceOrganization = "organization:{}"

    class Workspace:
        WorkspaceOrganization = "workspace:{}:organization"
        WorkspaceUserAccess = "workspace:{}:user:{}:access"

