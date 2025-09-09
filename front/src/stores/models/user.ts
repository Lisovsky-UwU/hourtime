export interface UserData {
  id: Number,
  username: String,
  display_name: String,
}

export interface RegistratePayload {
  username: String,
  display_name: String,
  password: String,
}

export interface LoginResponse {
  token: String
}
