import { create } from 'zustand'
import type { TaskInfo } from '@/api/types'

interface TaskState {
  tasks: TaskInfo[]
  drawerOpen: boolean
  setTasks: (tasks: TaskInfo[]) => void
  addTask: (task: TaskInfo) => void
  updateTask: (id: string, updates: Partial<TaskInfo>) => void
  removeTask: (id: string) => void
  toggleDrawer: () => void
  setDrawerOpen: (open: boolean) => void
  activeTasks: () => TaskInfo[]
}

export const useTaskStore = create<TaskState>((set, get) => ({
  tasks: [],
  drawerOpen: false,
  setTasks: (tasks) => set({ tasks }),
  addTask: (task) => set((s) => ({ tasks: [task, ...s.tasks] })),
  updateTask: (id, updates) =>
    set((s) => ({
      tasks: s.tasks.map((t) => (t.id === id ? { ...t, ...updates } : t)),
    })),
  removeTask: (id) =>
    set((s) => ({ tasks: s.tasks.filter((t) => t.id !== id) })),
  toggleDrawer: () => set((s) => ({ drawerOpen: !s.drawerOpen })),
  setDrawerOpen: (open) => set({ drawerOpen: open }),
  activeTasks: () =>
    get().tasks.filter((t) => t.status === 'pending' || t.status === 'running'),
}))
