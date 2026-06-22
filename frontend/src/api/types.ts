export interface User {
  id: number
  email: string
  display_name: string
}

export interface Course {
  id: number
  google_course_id: string
  name: string
  section: string | null
  description: string | null
  state: string
  synced_at: string
}

export interface Assignment {
  id: number
  title: string
  state: "new" | "processing" | "solved" | "approved" | "rejected" | "submitted" | "failed"
  assignment_type: "essay" | "coding" | "math" | "mcq" | "unknown"
  due_date: string | null
  course_id: number
  first_seen_at: string
}
