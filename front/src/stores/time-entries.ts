import { defineStore } from "pinia";
import { useApiStore } from "./api";
import { ApiEndpoint } from "./models/common";
import { useWorkspaces } from "./workspaces";
import type { TimeEntryModel, TimeEntryResponse } from "./models/time-entry";
import dayjs from "dayjs";

export const useTimeEntries = defineStore("timeEntries", {
  state: () => ({
    apiStore: useApiStore()
  }),

  getters: {

  },

  actions: {
    async getEntriesByPage(page: number = 1, limit: number = 35): Promise<TimeEntryModel[]> {
      const workspaces = useWorkspaces()
      const response: TimeEntryResponse[] = await this.apiStore.doRequest(
        ApiEndpoint.TimeEntryGetMy,
        "GET",
        null,
        {
          workspace_id: workspaces.currentWorkspace?.id,
          page: page,
          limit: limit,
        }
      )
      return response.map((entry) => ({
        id: entry.id,
        comment: entry.comment,
        workspace_id: entry.workspace_id,
        project_id: entry.project_id,
        task_id: entry.task_id,
        start_datetime: dayjs(`${entry.start_date} ${entry.start_time}`),
        end_datetime: entry.end_date !== null && entry.end_time !== null ? dayjs(`${entry.end_date} ${entry.end_time}`) : null,
      }))
    },

    async updateEntry(entry: TimeEntryModel): Promise<TimeEntryModel> {
      return await this.apiStore.doRequest(
        ApiEndpoint.TimeEntryUpdate,
        "PUT",
        {
          time_entry_id: entry.id,
          comment: entry.comment,
          project_id: entry.project_id,
          task_id: entry.task_id,
          start_date: entry.start_datetime.format("YYYY-MM-DD"),
          start_time: entry.start_datetime.format("HH:mm:ss"),
          end_date: entry.end_datetime !== null ? entry.end_datetime.format("YYYY-MM-DD") : null,
          end_time: entry.end_datetime !== null ? entry.end_datetime.format("HH:mm:ss") : null,
        },
      )
    }
  }
})
