export interface TimeEntryModel {
  id: string,
  comment: string,
  workspace_id: number,
  project_id: number | null,
  task_id: string | null,
  start_datetime: Date,
  end_datetime: Date | null,
}
