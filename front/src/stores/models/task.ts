export interface TaskModel {
  id: string,
  number: number,
  name: string,
  description: string | null,
  project_id: number | null,
}

export interface TaskCreateModel {
  name: string,
  description: string | null,
  project_id: number | null,
}

export interface TaskUpdateModel {
  task_id: string,
  name: string,
  description: string | null,
  project_id: number | null,
}
