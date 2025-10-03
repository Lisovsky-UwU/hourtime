import type { Dayjs } from "dayjs"

export interface TimeEntryModel {
  id: string,
  comment: string,
  workspace_id: number,
  project_id: number | null,
  task_id: string | null,
  start_datetime: Dayjs,
  end_datetime: Dayjs,
}

export interface TimeEntryResponse {
  id: string,
  comment: string,
  workspace_id: number,
  project_id: number | null,
  task_id: string | null,
  start_date: string,
  start_time: string
  end_date: string | null,
  end_time: string | null,
}
