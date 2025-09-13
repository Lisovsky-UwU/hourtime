import { defineStore } from "pinia";
import { useApiStore } from "./api";
import { ApiEndpoint } from "./models/common";
import {
  type UserData,
  type RegistratePayload,
  type LoginPayload,
  type LoginResponse,
} from "./models/user";



export const useUserData = defineStore('userData', {
  state: () => ({
    currentUserData: null as UserData | null,
    apiStore: useApiStore(),
  }),

  getters: {
    data(): UserData | null {
      return this.currentUserData
    },
  },

  actions: {
    set(data: UserData) {
      this.currentUserData = data
    },

    invalidate() {
      this.currentUserData = null
    },

    async loadMyData() {
      const response: UserData = await this.apiStore.doRequest(
        ApiEndpoint.UserMyInfo,
        "GET",
      )
      this.set(response)
    },

    async registrate(payload: RegistratePayload) {
      const response: LoginResponse = await this.apiStore.doRequest(
        ApiEndpoint.AuthRegistrate,
        "POST",
        payload,
      )
      this.apiStore.setToken(response.token)
    },

    async login(payload: LoginPayload) {
      const response: LoginResponse = await this.apiStore.doRequest(
        ApiEndpoint.AuthLogin,
        "POST",
        payload,
      )
      this.apiStore.setToken(response.token)
    }
  }
})
