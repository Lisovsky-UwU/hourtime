<template>
  <Loader v-if="loading" class="flex w-full justify-center h-full items-center"/>
  <div v-else>
    <div
      v-for="(entry, index) in listEntrie"
      :key="entry.id"
      class="w-full hover:bg-bg-dark py-2 px-4 flex flex-row gap-2"
    >
      <div v-if="entry.project_id !== null">
        {{ projectsMap[entry.project_id] }}
      </div>
      <TextField
        v-model="entry.comment"
        class="flex-grow"
        :placeholder="$t('message.page.timeEntry.emptyComment')"
        @blur="updateEntry(entry)"
      />
      <OrganizationAndTaskPicker v-model="listEntrie[index]" @update="(entryModel) => updateEntry(entryModel.value)"/>
      <div>
        <TimeElement
          v-model="listEntrie[index]"
          @update="(entryModel) => updateEntry(entryModel.value)"
        />
      </div>
    </div>

    <InfiniteLoading @infinite="load" >
      <template #complete>
        <div class="w-full text-center text-text-muted text-lg mt-4">
          No more results
        </div>
      </template>

      <template #error>
        <div class="w-full text-center text-text-muted text-lg mt-4">
          Oops something went wrong!
        </div>
      </template>
    </InfiniteLoading>
  </div>
</template>

<script setup lang="ts">
import { TimeEntryModel } from "@/stores/models/time-entry";
import { useProjects } from "@/stores/projects";
import { useTimeEntries } from "@/stores/time-entries";
import InfiniteLoading from "v3-infinite-loading";
import OrganizationAndTaskPicker from "./OrganizationAndTaskPicker.vue";
import "v3-infinite-loading/lib/style.css";
import { computed, onMounted, ref, } from "vue";
import TextField from "../ui/TextField.vue";
import TimeElement from "./TimeElement.vue";
import Loader from "../ui/Loader.vue";
import { useTasks } from "@/stores/tasks";

const timeEntries = useTimeEntries()
const projects = useProjects()
const tasks = useTasks()

const loading = ref(true)
const listEntrie = ref<TimeEntryModel[]>([])
let page = 1
const limit = 35

const projectsMap = computed<{}>(() => {
  return projects.projectsMap === null ? {} : projectsMap
})

const load = async $state => {
  try {
    const response = await timeEntries.getEntriesByPage(page, limit)
    listEntrie.value.push(...response)

    if (response.length < limit) {
      $state.complete()
    } else {
      $state.loaded()
    }
    page++
  } catch (error) {
    $state.error()
  }
}

async function loadStuff() {
  loading.value = true
  const promiseArr = []

  if (projects.projects === null) promiseArr.push(projects.loadProjects())
  if (tasks.tasks === null) promiseArr.push(tasks.loadTasks())

  if (promiseArr.length > 0) await Promise.all(promiseArr)

  loading.value = false
}

onMounted(async () => {
  await loadStuff()
})

async function updateEntry(newModel: TimeEntryModel) {
  await timeEntries.updateEntry(newModel)
}
</script>
