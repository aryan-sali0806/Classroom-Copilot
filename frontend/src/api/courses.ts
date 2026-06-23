import client from "./client"
import type { Course } from "./types"

export async function getCourses(): Promise<Course[]> {
  const { data } = await client.get<Course[]>("/courses")
  return data
}

export async function syncCourses(): Promise<{ synced: number; created: number; total: number }> {
  const { data } = await client.post("/courses/sync")
  return data
}
