import client from "./client"
import type { Course } from "./types"

export async function getCourses(): Promise<Course[]> {
  const { data } = await client.get<Course[]>("/courses")
  return data
}
