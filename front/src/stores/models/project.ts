export interface ProjectModel {
  id: number,
  workspace_id: number,
  name: string,
  description: string | null,
}

export interface ProjectCreateModel {
  name: string,
  description: string | null,
}

export interface ProjectUpdateModel {
  project_id: number,
  name: string,
  description: string | null,
}
