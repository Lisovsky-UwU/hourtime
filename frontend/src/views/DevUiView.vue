<script setup lang="ts">
import { ref } from 'vue'

import AppIcon from '@/components/AppIcon.vue'
import type { IconName } from '@/components/AppIcon.vue'
import UiButton from '@/components/ui/UiButton.vue'
import type { ComboboxItem } from '@/components/ui/UiCombobox.vue'
import UiCombobox from '@/components/ui/UiCombobox.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import type { MenuEntry } from '@/components/ui/UiDropdownMenu.vue'
import UiDropdownMenu from '@/components/ui/UiDropdownMenu.vue'
import UiIconButton from '@/components/ui/UiIconButton.vue'
import UiField from '@/components/ui/UiField.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiPopover from '@/components/ui/UiPopover.vue'
import UiSegmented from '@/components/ui/UiSegmented.vue'
import UiSwitch from '@/components/ui/UiSwitch.vue'
import UiTooltip from '@/components/ui/UiTooltip.vue'
import { toast } from '@/components/ui/toast'
import type { Theme } from '@/stores/preferences'
import { usePreferencesStore } from '@/stores/preferences'

/** Dev-only showcase of the UI kit; see docs/design.md. Not translated on purpose. */
const preferences = usePreferencesStore()
const themes: { value: Theme; icon: IconName; label: string }[] = [
  { value: 'auto', icon: 'theme-auto', label: 'Auto' },
  { value: 'light', icon: 'theme-light', label: 'Light' },
  { value: 'dark', icon: 'theme-dark', label: 'Dark' },
]

const swatches = [
  ['--bg', 'Card stock'],
  ['--surface', 'Sheet'],
  ['--surface-muted', 'Sheet, muted'],
  ['--border', 'Rule'],
  ['--text', 'Ink'],
  ['--text-muted', 'Pencil'],
  ['--accent', 'Form green'],
  ['--live', 'Punch red'],
] as const

const typeScale = [
  ['--text-clock', '36', 'Clock'],
  ['--text-xl', '24', 'Page title'],
  ['--text-lg', '18', 'Section, day total'],
  ['--text-md', '16', 'Timer description'],
  ['--text-sm', '14', 'Interface text'],
  ['--text-xs', '12', 'Labels and hints'],
] as const

const icons: IconName[] = [
  'play', 'stop', 'plus', 'edit', 'copy', 'trash', 'archive', 'unarchive', 'check', 'close',
  'more', 'search', 'chevron-down', 'chevrons-up-down', 'timer', 'projects', 'settings',
  'sign-out', 'menu', 'sidebar', 'theme-auto', 'theme-light', 'theme-dark', 'info', 'alert',
]

const projects = ref<ComboboxItem[]>([
  { value: 'p1', label: 'hourtime', color: '#1e6a4e' },
  { value: 'p2', label: 'Client portal redesign', color: '#c2572c' },
  { value: 'p3', label: 'Reading', color: '#3b6fb6' },
  { value: 'p4', label: 'Infrastructure and a very long project name that must be cut', color: '#8a5cc2' },
  { value: 'p5', label: 'Без цвета' },
])
const projectId = ref<string | null>('p1')
const emptyProject = ref<string | null>(null)

function createProject(name: string) {
  const value = `p${projects.value.length + 1}`
  projects.value.push({ value, label: name, color: '#b8862b' })
  projectId.value = value
  toast.success('Project created', name)
}

const menu: MenuEntry[] = [
  { label: 'Continue', icon: 'play', select: () => toast.info('Continue') },
  { label: 'Duplicate', icon: 'copy', select: () => toast.info('Duplicate') },
  { label: 'Edit', icon: 'edit', select: () => toast.info('Edit') },
  { label: 'Archive', icon: 'archive', disabled: true, select: () => {} },
  'separator',
  { label: 'Delete', icon: 'trash', variant: 'danger', select: () => toast.error('Deleted') },
]

const name = ref('')
const email = ref('not-an-email')
const switchOn = ref(true)
const switchOff = ref(false)
const segment = ref<'active' | 'archived'>('active')
const segments = [
  { value: 'active' as const, label: 'Active' },
  { value: 'archived' as const, label: 'Archived' },
]
const dialogOpen = ref(false)
const running = ref(true)
</script>

<template>
  <div class="page stack dev">
    <header class="row-between dev-head">
      <h1>UI kit</h1>
      <div class="row" role="radiogroup" aria-label="Theme">
        <UiButton
          v-for="theme in themes"
          :key="theme.value"
          size="sm"
          :variant="preferences.theme === theme.value ? 'primary' : 'secondary'"
          :icon="theme.icon"
          role="radio"
          :aria-checked="preferences.theme === theme.value"
          @click="preferences.theme = theme.value"
        >
          {{ theme.label }}
        </UiButton>
      </div>
    </header>

    <section class="dev-section">
      <h2>Clock</h2>
      <div class="clock-specimen">
        <span class="live-dot" :class="{ on: running }" />
        <span class="num clock" :class="{ on: running }">0:42:17</span>
        <button
          type="button"
          class="timer-action"
          :class="{ on: running }"
          :aria-label="running ? 'Stop timer' : 'Start timer'"
          @click="running = !running"
        >
          <AppIcon :name="running ? 'stop' : 'play'" :size="20" />
        </button>
      </div>
      <p class="muted">
        Draft of the stage 2 signature: the only loud element on a screen. Digits use
        <code>.num</code>.
      </p>
    </section>

    <section class="dev-section">
      <h2>Colors</h2>
      <div class="swatches">
        <div v-for="[token, label] in swatches" :key="token" class="swatch">
          <span class="swatch-chip" :style="{ background: `var(${token})` }" />
          <span>{{ label }}</span>
          <code class="muted">{{ token }}</code>
        </div>
      </div>
    </section>

    <section class="dev-section">
      <h2>Type</h2>
      <div class="type-scale">
        <div v-for="[token, px, role] in typeScale" :key="token" class="type-row">
          <span class="muted num">{{ px }}</span>
          <span :style="{ fontSize: `var(${token})` }">{{ role }} - Учет времени</span>
        </div>
      </div>
      <div class="ledger">
        <div class="ledger-row">
          <span>Fix login redirect</span>
          <span class="muted num">09:10 - 10:02</span>
          <span class="num">0:52:08</span>
        </div>
        <div class="ledger-row">
          <span>Code review</span>
          <span class="muted num">10:05 - 12:23</span>
          <span class="num">2:18:41</span>
        </div>
        <div class="ledger-row total">
          <span>Today</span>
          <span />
          <span class="num">3:10:49</span>
        </div>
      </div>
    </section>

    <section class="dev-section">
      <h2>Buttons</h2>
      <div class="row wrap">
        <UiButton variant="primary" icon="plus">Add entry</UiButton>
        <UiButton>Cancel</UiButton>
        <UiButton variant="ghost">Show archived</UiButton>
        <UiButton variant="danger" icon="trash">Delete project</UiButton>
        <UiButton variant="primary" disabled>Saving…</UiButton>
      </div>
      <div class="row wrap">
        <UiButton variant="primary" size="sm">Save</UiButton>
        <UiButton size="sm">Cancel</UiButton>
        <UiButton variant="ghost" size="sm" icon="edit">Edit</UiButton>
        <UiButton variant="danger" size="sm">Delete</UiButton>
      </div>
      <div class="row wrap">
        <UiIconButton icon="play" label="Continue" />
        <UiIconButton icon="edit" label="Edit" variant="secondary" />
        <UiIconButton icon="trash" label="Delete" variant="danger" />
        <UiIconButton icon="copy" label="Duplicate" size="sm" />
        <UiIconButton icon="archive" label="Archive" disabled />
      </div>
    </section>

    <section class="dev-section">
      <h2>Icons</h2>
      <div class="icons">
        <UiTooltip v-for="icon in icons" :key="icon" :content="icon">
          <span class="icon-cell" tabindex="0"><AppIcon :name="icon" /></span>
        </UiTooltip>
      </div>
    </section>

    <section class="dev-section">
      <h2>Fields and choices</h2>
      <div class="fields">
        <UiField label="Project name">
          <UiInput v-model="name" placeholder="Client, product or activity" />
        </UiField>
        <UiField label="Email (invalid)" hint="Hints sit under the control">
          <UiInput v-model="email" type="email" invalid />
        </UiField>
        <UiField label="Disabled">
          <UiInput model-value="Read only" disabled />
        </UiField>
      </div>
      <UiSegmented v-model="segment" :options="segments" label="Projects to show" />
    </section>

    <section class="dev-section">
      <h2>Combobox</h2>
      <div class="row wrap">
        <UiCombobox
          v-model="projectId"
          :items="projects"
          label="Select project"
          placeholder="Project"
          none-label="No project"
          creatable
          @create="createProject"
        />
        <UiCombobox
          v-model="emptyProject"
          :items="projects"
          label="Select project"
          placeholder="Project"
          none-label="No project"
        />
        <UiCombobox :items="[]" label="Disabled" placeholder="Disabled" disabled />
      </div>
      <p class="muted">Type a new name in the first one to see "Create".</p>
    </section>

    <section class="dev-section">
      <h2>Menus and popovers</h2>
      <div class="row wrap">
        <UiDropdownMenu :items="menu" label="More actions" />
        <UiPopover>
          <template #trigger>
            <UiButton icon="info">Popover</UiButton>
          </template>
          <template #default="{ close }">
            <div class="stack popover-demo">
              <p>Popovers hold small forms, like editing the start time of an entry.</p>
              <UiButton size="sm" variant="primary" @click="close">Done</UiButton>
            </div>
          </template>
        </UiPopover>
        <UiTooltip content="Tooltips name icon-only controls">
          <UiButton variant="ghost">Hover me</UiButton>
        </UiTooltip>
      </div>
    </section>

    <section class="dev-section">
      <h2>Switch</h2>
      <div class="switches">
        <UiSwitch v-model="switchOn" label="Billable" hint="New entries of this project are billable" />
        <UiSwitch v-model="switchOff" label="Show seconds" />
        <UiSwitch :model-value="false" label="Disabled" disabled />
      </div>
    </section>

    <section class="dev-section">
      <h2>Dialog and toasts</h2>
      <div class="row wrap">
        <UiButton @click="dialogOpen = true">Open dialog</UiButton>
        <UiButton variant="ghost" @click="toast.info('Timer stopped', '0:42:17 on hourtime')">
          Info toast
        </UiButton>
        <UiButton variant="ghost" @click="toast.success('Project created')">Success toast</UiButton>
        <UiButton
          variant="ghost"
          @click="toast.error('Cannot reach the server', 'Check your connection and try again.')"
        >
          Error toast
        </UiButton>
      </div>
    </section>

    <UiDialog v-model:open="dialogOpen" title="Edit project">
      <UiField label="Name">
        <UiInput model-value="hourtime" />
      </UiField>
      <UiSwitch v-model="switchOn" label="Billable" />
      <template #footer="{ close }">
        <UiButton @click="close">Cancel</UiButton>
        <UiButton variant="primary" @click="close">Save changes</UiButton>
      </template>
    </UiDialog>
  </div>
</template>

<style scoped>
.dev {
  gap: 20px;
}

.dev-head {
  flex-wrap: wrap;
}

.dev-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 20px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sheet);
  background: var(--surface);
}

.wrap {
  flex-wrap: wrap;
}

code {
  font-size: var(--text-xs);
}

.clock-specimen {
  display: flex;
  align-items: center;
  gap: 16px;
}

.clock {
  font-size: var(--text-clock);
  font-weight: 600;
  line-height: 1;
  letter-spacing: -0.02em;
  color: var(--text-muted);
}

.clock.on {
  color: var(--text);
}

.live-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--border-strong);
}

.live-dot.on {
  background: var(--live);
  animation: live-pulse 2s ease-in-out infinite;
}

.timer-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: var(--accent);
  color: var(--accent-contrast);
  cursor: pointer;
  transition: background-color var(--dur) var(--ease);
}

.timer-action.on {
  background: var(--live);
  color: var(--live-contrast);
}

.swatches {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
}

.swatch {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.swatch-chip {
  height: 44px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.type-scale {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.type-row {
  display: grid;
  grid-template-columns: 32px 1fr;
  align-items: baseline;
  gap: 12px;
  overflow-wrap: anywhere;
}

.ledger {
  display: flex;
  flex-direction: column;
}

.ledger-row {
  display: grid;
  grid-template-columns: 1fr auto 72px;
  gap: 16px;
  padding: 8px 0;
  border-top: 1px solid var(--border);
}

.ledger-row > :last-child {
  text-align: right;
}

.ledger-row.total {
  font-size: var(--text-lg);
  font-weight: 600;
}

.icons {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(40px, 1fr));
  gap: 4px;
}

.icon-cell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
}

.icon-cell:hover {
  background: var(--surface-muted);
  color: var(--text);
}

.fields {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.switches {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 420px;
}

.popover-demo {
  gap: 10px;
  align-items: flex-start;
}

@media (width < 768px) {
  .dev-section {
    padding: 16px;
  }

  .ledger-row {
    grid-template-columns: 1fr 64px;
  }

  .ledger-row > :nth-child(2) {
    display: none;
  }
}
</style>
