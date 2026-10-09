<script setup lang="ts">
import { computed } from 'vue'
import type { Component } from 'vue'
import {
  Archive,
  ArrowDown,
  ArrowUp,
  BriefcaseBusiness,
  CalendarDays,
  ChartColumn,
  ArchiveRestore,
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronsUpDown,
  CircleAlert,
  Copy,
  Ellipsis,
  FolderKanban,
  Info,
  KeyRound,
  Keyboard,
  LogOut,
  Menu,
  Monitor,
  Moon,
  PanelLeft,
  Pencil,
  Play,
  Plus,
  Search,
  Settings,
  Square,
  Tag,
  Tags,
  Sun,
  Timer,
  Trash2,
  X,
} from '@lucide/vue'

/**
 * The only place that knows which icon set is used. Screens ask for a name;
 * listing the imports here lets the bundler drop every other icon.
 */
const ICONS = {
  archive: Archive,
  calendar: CalendarDays,
  unarchive: ArchiveRestore,
  check: Check,
  'chevron-down': ChevronDown,
  'chevron-left': ChevronLeft,
  'chevron-right': ChevronRight,
  'arrow-up': ArrowUp,
  'arrow-down': ArrowDown,
  'chevrons-up-down': ChevronsUpDown,
  alert: CircleAlert,
  copy: Copy,
  more: Ellipsis,
  projects: FolderKanban,
  reports: ChartColumn,
  clients: BriefcaseBusiness,
  tag: Tag,
  tags: Tags,
  info: Info,
  keyboard: Keyboard,
  key: KeyRound,
  'sign-out': LogOut,
  menu: Menu,
  'theme-auto': Monitor,
  'theme-dark': Moon,
  'theme-light': Sun,
  sidebar: PanelLeft,
  edit: Pencil,
  play: Play,
  plus: Plus,
  search: Search,
  settings: Settings,
  stop: Square,
  timer: Timer,
  trash: Trash2,
  close: X,
} satisfies Record<string, Component>

export type IconName = keyof typeof ICONS

/** Play and stop read as buttons of a recorder, so they are drawn solid. */
const FILLED = new Set<IconName>(['play', 'stop'])

const props = withDefaults(defineProps<{ name: IconName; size?: number }>(), { size: 18 })

const icon = computed(() => ICONS[props.name])
</script>

<template>
  <component
    :is="icon"
    :size="props.size"
    :stroke-width="1.75"
    :fill="FILLED.has(props.name) ? 'currentColor' : 'none'"
    aria-hidden="true"
    focusable="false"
  />
</template>
