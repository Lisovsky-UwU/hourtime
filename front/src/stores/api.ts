import { defineStore } from "pinia";
import { notify } from "@kyvg/vue3-notification";
import { useI18n } from 'vue-i18n'
import { type ErrorResponse, type ApiEndpoint } from "./models/common";

const { t } = useI18n()


export const useApiStore = defineStore('api', {
  state: () => ({
    userToken: null as String | null,
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
    clearToken() {
      localStorage.removeItem("User-Token")
      this.userToken = null
    },

    async doRequest(endpoint: ApiEndpoint, method: String, data: any | null = null): Promise<any> {
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

      try {
        var r = await fetch(`/api/v1${endpoint}`, fetchOptions)
      } catch (e) {
        notify({
          title: t("message.notification.serverRequestError.title"),
          text: t("message.notification.serverRequestError.text"),
          type: "error",
        })
        console.error(e)
        throw e
      }

      if (r.status != 200) {
        const rJson: ErrorResponse = await r.json()
        if (rJson.error_code === 15) {

        }
        notify({
          title: t(`message.notification.apiError.${rJson.error_code}.title`),
          text: t(`message.notification.apiError.${rJson.error_code}.text`),
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
