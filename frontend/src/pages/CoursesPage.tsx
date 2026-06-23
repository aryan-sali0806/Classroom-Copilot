import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { BookOpen, ChevronRight, RefreshCw } from "lucide-react"
import { getCourses, syncCourses } from "@/api/courses"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"

export default function CoursesPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: courses, isLoading, isError, isFetching } = useQuery({
    queryKey: ["courses"],
    queryFn: getCourses,
  })
  const { mutate: sync, isPending: isSyncing } = useMutation({
    mutationFn: syncCourses,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["courses"] }),
  })

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BookOpen className="h-6 w-6 text-blue-600" />
          <h1 className="text-xl font-semibold text-gray-900">Classroom Copilot</h1>
        </div>
        <button
          onClick={() => sync()}
          disabled={isSyncing || isFetching}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${isSyncing || isFetching ? "animate-spin" : ""}`} />
          {isSyncing ? "Syncing…" : "Sync from Google"}
        </button>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900">My Courses</h2>
          <p className="text-gray-500 mt-1">Select a course to view pending assignments</p>
        </div>

        {isError && (
          <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-red-700 text-sm">
            Failed to load courses. Make sure you are signed in via Google.
          </div>
        )}

        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-36 w-full" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {courses?.map((course) => (
              <Card
                key={course.id}
                className="cursor-pointer hover:shadow-md hover:border-blue-300 transition-all"
                onClick={() => navigate(`/courses/${course.id}`)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-base leading-snug">{course.name}</CardTitle>
                    <ChevronRight className="h-4 w-4 text-gray-400 mt-0.5 shrink-0" />
                  </div>
                  {course.section && (
                    <CardDescription>{course.section}</CardDescription>
                  )}
                </CardHeader>
                <CardContent>
                  <Badge variant={course.state === "ACTIVE" ? "success" : "secondary"}>
                    {course.state}
                  </Badge>
                </CardContent>
              </Card>
            ))}

            {courses?.length === 0 && (
              <div className="col-span-3 text-center py-16 text-gray-400">
                <BookOpen className="h-10 w-10 mx-auto mb-3 opacity-40" />
                <p className="mb-4">No courses found.</p>
                <button
                  onClick={() => sync()}
                  disabled={isSyncing}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-blue-600 text-white text-sm hover:bg-blue-700 disabled:opacity-50"
                >
                  <RefreshCw className={`h-4 w-4 ${isSyncing ? "animate-spin" : ""}`} />
                  {isSyncing ? "Syncing…" : "Sync from Google Classroom"}
                </button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
