const en = {
  message: {

    common: {
      appName: "Hourtime",
      name: "Name",
      create: "Create new",
      edit: "Edit",
      delete: "Delete",
      manage: "Manage",
    },

    page: {
      auth: {
        loginToUse: "Log in to use",
        username: "Username",
        enterUsername: "Enter username",
        password: "Password",
        enterPassword: "Enter password",
        login: "Log in",
        registrate: "Registrate",
        logout: "Log out",
      },
      organization: {
        createNewOrganization: "Create a new organization",
        organizationName: "Organization name",
        enterOrganizationName: "Enter organization name",
        defaultName: "{userName}'s organization",
      },
    },

    validations: {
      fieldIsRequired: "Oops! This field can't be empty.",
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
