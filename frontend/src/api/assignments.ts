import client from "./client"
import type { Assignment } from "./types"

export async function getAssignments(params?: {
  course_id?: number
  status?: string
}): Promise<Assignment[]> {
  const { data } = await client.get<Assignment[]>("/assignments", { params })
  return data
}
