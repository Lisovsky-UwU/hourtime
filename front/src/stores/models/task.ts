export interface TaskModel {
  id: string,
  number: number,
  name: string,
  description: string,
  project_id: number | null,
}
