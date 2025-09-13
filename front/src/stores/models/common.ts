export interface ErrorResponse {
  error_type: string,
  error_code: Number,
  user_message: string,
  detail: string | null,
}

export enum ApiEndpoint {
  AuthLogin = "/auth/login",
  AuthRegistrate = "/auth/registrate",

  UserMyInfo = "/user/me/info",
  UserMeChangePassword = "/user/me/change_password",
  UserMeUpdate = "/user/me/update",

  OrganizationCreate = "/organization/create",
  OrganizationMy = "/organization/my",
  OrganizationUpdate = "/organization/update",

  WorkspaceCreate = "/workspace/create",
}
