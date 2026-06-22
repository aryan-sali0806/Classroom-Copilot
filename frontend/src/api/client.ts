import axios from "axios"

const client = axios.create({
  baseURL: "/api/v1",
  withCredentials: true,
})

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      window.location.href = "/api/v1/auth/google"
    }
    return Promise.reject(err)
  }
)

export default client
