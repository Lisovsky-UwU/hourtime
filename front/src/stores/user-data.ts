import { defineStore } from "pinia";
import { useApiStore } from "./api";
import { ApiEndpoint } from "./models/common";
import { type UserData, type RegistratePayload, type LoginResponse } from "./models/user";

const apiStore = useApiStore()


export const useUserData = defineStore('userData', {
  state: () => ({
    currentUserData: null as UserData | null,
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

    async registrate(payload: RegistratePayload) {
      const response: LoginResponse = await apiStore.doRequest(
        ApiEndpoint.AuthRegistrate,
        "POST",
        payload,
      )
    }
  }
})
