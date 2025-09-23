import { defineStore } from "pinia";
import { useNotification } from "@kyvg/vue3-notification";
import { i18n } from "@/plugins/i18n"
import type { ErrorResponse, ApiEndpoint } from "./models/common";

const { notify }  = useNotification()


export const useApiStore = defineStore('api', {
  state: () => ({
    userToken: null as string | null,
  }),

  getters: {
    isLogin(): boolean {
      return this.userToken !== null
    },
    token(): String {
      return this.userToken || ""
    }
  },

  actions: {
    loadToken() {
      this.userToken = localStorage.getItem("User-Token")
    },

    setToken(token: string) {
      this.userToken = token
      localStorage.setItem("User-Token", token)
    },

    clearToken() {
      localStorage.removeItem("User-Token")
      this.userToken = null
    },

    async doRequest(endpoint: ApiEndpoint, method: string, data: any | null = null, query: any | null = null): Promise<any> {
      let fetchOptions = {
        method: method,
        headers: {} as any,
      } as any

      if (data !== null) {
        fetchOptions.headers['content-type'] = 'application/json'
        fetchOptions.body = JSON.stringify(data)
      }
      if (this.isLogin) {
        fetchOptions.headers['User-Token'] = this.token
      }

      const queryString = new URLSearchParams(query).toString()

      try {
        var r = await fetch(`/api/v1${endpoint}?${queryString}`, fetchOptions)
      } catch (e) {
        notify({
          title: i18n.t("message.notification.serverRequestError.title"),
          text: i18n.t("message.notification.serverRequestError.text"),
          type: "error",
        })
        console.error(e)
        throw e
      }

      if (r.status != 200) {
        let rJson: ErrorResponse
        try {
          rJson = await r.json()
        } catch (e) {
          notify({
            title: i18n.t("message.notification.serverParseResponseError.title"),
            text: i18n.t("message.notification.serverParseResponseError.text"),
            type: "error",
          })
          throw e
        }

        if (rJson.error_code === 15) {
          this.clearToken()
        }
        notify({
          title: i18n.t(`message.notification.apiError.${rJson.error_code}.title`),
          text: i18n.t(`message.notification.apiError.${rJson.error_code}.text`),
          type: "error",
        })
        console.error(rJson)

        let e = new Error(`(${rJson.error_type}) ${rJson.detail}`)
        throw e
      } else {
        return await r.json()
      }
    }
  }
})
