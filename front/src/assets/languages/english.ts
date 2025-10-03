const en = {
  message: {

    common: {
      appName: "Hourtime",
      name: "Name",
      create: "Create new",
      edit: "Edit",
      delete: "Delete",
      manage: "Manage",
      save: "Save",
      cancel: "Cancel",
      add: "Add",
    },

    page: {
      auth: {
        loginToUse: "Log in to use",
        username: "Username",
        enterUsername: "Enter username",
        password: "Password",
        enterPassword: "Enter password",
        displayName: "Display name",
        enterDisplayName: "Enter display name",
        confirmPassword: "Confirm password",
        login: "Log in",
        registrate: "Registrate",
        goLogin: "Go to login",
        goRegistrate: "Create account",
      },
      organization: {
        title: "Organizations",
        createNewOrganization: "Create a new organization",
        organizationName: "Organization name",
        enterOrganizationName: "Enter organization name",
        defaultName: "{userName}'s organization",
        confirmDelete: "Do you really want to delete organization?",
        workspaces: "Workspaces",
        edit: "Edit organization",
        delete: "Delete organization",
        addWorkspace: "Add workspace",
        editWorkspace: "Edit workspace",
        deleteWorkspace: "Delete workspace",
      },
      workspace: {
        workspaceName: "Workspace name",
        enterWorkspaceName: "Enter workspace name",
        forOrganization: "For organization",
        confirmDelete: "Do you really want to delete workspace?",
      },
      project: {
        title: "Projects",
        noProjects: "There are no projects yet.",
        projectName: "Project name",
        enterProjectName: "Enter project name",
        projectDescription: "Project description",
        enterProjectDescription: "Enter project description",
        confirmDelete: "Do you really want to delete project?",
      },
      task: {
        title: "Tasks",
        noTasks: "There are no tasks yet.",
        colId: "#",
        colName: "Name",
        colProject: "Project",
        colActions: "Actions",
        taskName: "Task name",
        enterTaskName: "Enter task name",
        taskDescription: "Task description",
        enterTaskDescription: "Enter task description",
        taskProject: "Project",
        noProject: "No project",
        newTask: "New task",
        taskNumber: "Task #{taskNumber}",
        confirmDelete: "Do you really want to delete task?",
      },
      timeEntry: {
        emptyComment: "Add comment",
        startTime: "Start",
        endTime: "End",
      },
    },

    sideBar: {
      timeTrack: "Time track",
      projects: "Projects",
      tasks: "Tasks",
      logout: "Log out",
    },

    validations: {
      fieldIsRequired: "Oops! This field can't be empty.",
      passwordsDontMatch: "Passwords don't match.",
    },

    notification: {
      serverRequestError: {
        title: "API request error",
        text: "An error occurred when requesting the server API.<br>Check your internet connection.",
      },
      serverParseResponseError: {
        title: "Response parse error",
        text: "The server sent a response in an unexpected format."
      },

      apiError: {
        1: {
          title: "Database Connection Error",
          text: "Server cannot connect to database. Check configuration.",
        },
        2: {
          title: "Database Connection Error",
          text: "Server cannot connect to database. Check configuration.",
        },
        3: {
          title: "Server Cache Error",
          text: "Server cannot use cache service. Check configuration",
        },
        10: {
          title: "Not Found",
          text: "User not found.",
        },
        11: {
          title: "User Already Exists",
          text: "The user with the entered username already exists.",
        },
        12: {
          title: "Not Found",
          text: "User not found in the database by username. Verify the username and try again.",
        },
        13: {
          title: "User Already Exists",
          text: "The user with the entered username already exists. Please choose a different username.",
        },
        14: {
          title: "Login error",
          text: "The username or password is incorrect. Please double-check your credentials and try again.",
        },
        15: {
          title: "Token Expired",
          text: "The provided token has expired. Please log in again.",
        },
        16: {
          title: "Authentication Error",
          text: "The old password does not match the currently installed one. Please verify your old password and try again.",
        },
        20: {
          title: "Not Found",
          text: "Organization not found.",
        },
        21: {
          title: "Access Denied",
          text: "You do not have sufficient rights to access this organization.",
        },
        30: {
          title: "Not Found",
          text: "Workspace not found.",
        },
        40: {
          title: "Not Found",
          text: "Project not found.",
        },
        50: {
          title: "Not Found",
          text: "Project not found.",
        },
        51: {
          title: "Incorrect project",
          text: "Specified project is not part of the workspace.",
        },
        500: {
          title: "Unexpected Server Error",
          text: "An unknown error occurred on the server.",
        },
        503: {
          title: "Database Error",
          text: "An error occurred while making a request to the database.",
        },
        404: {
          title: "Route Not Found",
          text: "The requested path could not be found in server API.",
        },
      }
    },
  },
}

export default en
