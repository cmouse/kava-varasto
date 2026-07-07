import axios from "axios";

const scriptName = typeof window !== "undefined" ? window.SCRIPT_NAME || "" : "";

const apiClient = axios.create({
  baseURL: `${scriptName}/api/`,
  withCredentials: true,
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFToken",
});

export default apiClient;
