import { Link } from "react-router-dom"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { formatDate } from "@/lib/dates"
import type { Project } from "@/types/project"

export function ProjectCard({ project }: { project: Project }) {
  return (
    <Link to={`/projects/${project.id}`} className="block h-full">
      <Card className="h-full transition-colors hover:bg-muted/40">
        <CardHeader>
          <CardTitle className="line-clamp-1">{project.name}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="line-clamp-2 text-sm text-muted-foreground">
            {project.description || "No description"}
          </p>
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{project.members.length} members</span>
            <span>{formatDate(project.created_at)}</span>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
