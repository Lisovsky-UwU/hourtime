export interface UserData {
  id: Number,
  username: string,
  display_name: string,
}

export interface RegistratePayload {
  username: string,
  display_name: string,
  password: string,
}

export interface LoginPayload {
  username: string,
  password: string,
}

export interface LoginResponse {
  token: string
}
