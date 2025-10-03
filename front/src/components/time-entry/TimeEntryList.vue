<template>
  <div
    v-for="(entry, index) in listEntrie"
    :key="entry.id"
    class="w-full hover:bg-bg-dark py-2 px-4 flex flex-row gap-4"
  >
    <div v-if="entry.project_id !== null">
      {{ projectsMap[entry.project_id] }}
    </div>
    <TextField
      v-model="entry.comment"
      class="flex-grow"
      :placeholder="$t('message.page.timeEntry.emptyComment')"
    />
    <div>
      <TimeElement
        v-model="listEntrie[index]"
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
</template>

<script setup lang="ts">
import { TimeEntryModel } from "@/stores/models/time-entry";
import { useProjects } from "@/stores/projects";
import { useTimeEntries } from "@/stores/time-entries";
import InfiniteLoading from "v3-infinite-loading";
import "v3-infinite-loading/lib/style.css"; //required if you're not going to override default slots
import { computed, ref } from "vue";
import TextField from "../ui/TextField.vue";
import TimeElement from "./TimeElement.vue";

const timeEntries = useTimeEntries()
const projects = useProjects()

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
</script>
