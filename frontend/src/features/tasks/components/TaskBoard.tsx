import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core"
import { CSS } from "@dnd-kit/utilities"
import { GripVertical } from "lucide-react"
import type { ReactNode } from "react"

import { cn } from "@/lib/utils"
import { TASK_STATUSES, type Task, type TaskStatus } from "@/types/task"

import { STATUS_LABEL } from "./StatusBadge"
import { TaskCard } from "./TaskCard"

function statusFromOver(over: DragEndEvent["over"]): TaskStatus | null {
  if (!over) {
    return null
  }
  const data = over.data.current as { status?: TaskStatus } | undefined
  if (data?.status && TASK_STATUSES.includes(data.status)) {
    return data.status
  }
  if (typeof over.id === "string" && TASK_STATUSES.includes(over.id as TaskStatus)) {
    return over.id as TaskStatus
  }
  return null
}

function DroppableColumn({
  status,
  count,
  children,
}: {
  status: TaskStatus
  count: number
  children: ReactNode
}) {
  const { setNodeRef, isOver } = useDroppable({
    id: status,
    data: { status, type: "column" },
  })

  return (
    <section
      ref={setNodeRef}
      className={cn(
        "rounded-xl border bg-muted/20 p-3 transition-colors",
        isOver && "ring-2 ring-ring",
      )}
    >
      <header className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold">{STATUS_LABEL[status]}</h3>
        <span className="text-xs text-muted-foreground">{count}</span>
      </header>
      <div className="min-h-24 space-y-2">{children}</div>
    </section>
  )
}

function DraggableTask({
  task,
  onStatusChange,
  statusPending,
}: {
  task: Task
  onStatusChange?: (taskId: string, status: TaskStatus) => void
  statusPending?: boolean
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({
      id: task.id,
      data: { status: task.status, type: "task" },
    })

  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Translate.toString(transform) }}
      className={cn(isDragging && "z-10 opacity-80")}
    >
      <TaskCard
        task={task}
        statusPending={statusPending}
        onStatusChange={
          onStatusChange ? (next) => onStatusChange(task.id, next) : undefined
        }
        dragHandle={
          <button
            type="button"
            className="mt-0.5 text-muted-foreground hover:text-foreground"
            aria-label={`Move ${task.title}`}
            {...listeners}
            {...attributes}
          >
            <GripVertical className="size-4" />
          </button>
        }
      />
    </div>
  )
}

export function TaskBoard({
  tasks,
  onStatusChange,
  pendingTaskId,
}: {
  tasks: Task[]
  onStatusChange?: (taskId: string, status: TaskStatus) => void
  pendingTaskId?: string | null
}) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor),
  )

  const grouped: Record<TaskStatus, Task[]> = {
    todo: [],
    in_progress: [],
    completed: [],
  }
  for (const task of tasks) {
    grouped[task.status].push(task)
  }

  function handleDragEnd(event: DragEndEvent) {
    const nextStatus = statusFromOver(event.over)
    const taskId = String(event.active.id)
    const task = tasks.find((item) => item.id === taskId)
    if (!nextStatus || !task || task.status === nextStatus) {
      return
    }
    onStatusChange?.(task.id, nextStatus)
  }

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div className="grid gap-4 lg:grid-cols-3">
        {TASK_STATUSES.map((status) => (
          <DroppableColumn
            key={status}
            status={status}
            count={grouped[status].length}
          >
            {grouped[status].length === 0 ? (
              <p className="px-1 py-6 text-center text-xs text-muted-foreground">
                No tasks
              </p>
            ) : (
              grouped[status].map((task) => (
                <DraggableTask
                  key={task.id}
                  task={task}
                  statusPending={pendingTaskId === task.id}
                  onStatusChange={onStatusChange}
                />
              ))
            )}
          </DroppableColumn>
        ))}
      </div>
    </DndContext>
  )
}
