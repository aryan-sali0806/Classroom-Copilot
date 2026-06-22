import { useQuery } from "@tanstack/react-query"
import { useNavigate, useParams } from "react-router-dom"
import { ArrowLeft, BookOpen, Bot, Clock } from "lucide-react"
import { getAssignments } from "@/api/assignments"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import type { Assignment } from "@/api/types"

const STATE_VARIANT: Record<Assignment["state"], "secondary" | "processing" | "success" | "destructive" | "warning" | "default"> = {
  new: "secondary",
  processing: "processing",
  solved: "warning",
  approved: "success",
  rejected: "destructive",
  submitted: "success",
  failed: "destructive",
}

const TYPE_ICON: Record<Assignment["assignment_type"], string> = {
  essay: "📝",
  coding: "💻",
  math: "🔢",
  mcq: "🔘",
  unknown: "📄",
}

function formatDue(date: string | null) {
  if (!date) return "No due date"
  return new Date(date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}

function AssignmentRow({ assignment }: { assignment: Assignment }) {
  return (
    <div className="flex items-center gap-4 py-3 border-b last:border-0">
      <span className="text-xl">{TYPE_ICON[assignment.assignment_type]}</span>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-gray-900 truncate">{assignment.title}</p>
        <div className="flex items-center gap-2 mt-0.5">
          <Clock className="h-3 w-3 text-gray-400" />
          <span className="text-xs text-gray-500">{formatDue(assignment.due_date)}</span>
        </div>
      </div>
      <Badge variant={STATE_VARIANT[assignment.state]}>{assignment.state}</Badge>
    </div>
  )
}

export default function CoursePage() {
  const { courseId } = useParams<{ courseId: string }>()
  const navigate = useNavigate()
  const id = Number(courseId)

  const { data: pending, isLoading: pendingLoading } = useQuery({
    queryKey: ["assignments", id, "pending"],
    queryFn: () => getAssignments({ course_id: id, status: "new" }),
    enabled: !!id,
  })

  const { data: aiGenerated, isLoading: aiLoading } = useQuery({
    queryKey: ["assignments", id, "ai"],
    queryFn: () => getAssignments({ course_id: id }),
    enabled: !!id,
    select: (data) => data.filter((a) => a.state !== "new"),
  })

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center gap-4">
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900"
        >
          <ArrowLeft className="h-4 w-4" />
          All Courses
        </button>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8 space-y-8">
        {/* Pending / New assignments */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-orange-500" />
              <CardTitle>Pending Work</CardTitle>
              {pending && (
                <Badge variant="secondary" className="ml-auto">{pending.length}</Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {pendingLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : pending?.length === 0 ? (
              <p className="text-sm text-gray-400 py-4 text-center">No pending assignments</p>
            ) : (
              pending?.map((a) => <AssignmentRow key={a.id} assignment={a} />)
            )}
          </CardContent>
        </Card>

        {/* AI-processed assignments */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Bot className="h-5 w-5 text-blue-500" />
              <CardTitle>Copilot-Generated Solutions</CardTitle>
              {aiGenerated && (
                <Badge variant="secondary" className="ml-auto">{aiGenerated.length}</Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {aiLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : aiGenerated?.length === 0 ? (
              <p className="text-sm text-gray-400 py-4 text-center">
                No AI-generated solutions yet. Run the pipeline on an assignment to get started.
              </p>
            ) : (
              aiGenerated?.map((a) => <AssignmentRow key={a.id} assignment={a} />)
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
