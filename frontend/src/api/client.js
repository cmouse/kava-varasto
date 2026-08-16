import axios from "axios";

import scriptName from "../utils/scriptName";

const apiClient = axios.create({
  baseURL: `${scriptName}/api/`,
  withCredentials: true,
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFToken",
});

export default apiClient;
