<template>
  <div
    class="w-full px-4 py-2 border rounded-lg focus:outline-none transition-all duration-300
    border-border focus:border-highlight flex flex-row gap-2 text-text-muted cursor-pointer
    hover:bg-bg-light relative"
    @click="showEdit = !showEdit"
    id="toggle-popup"
  >
    <div>
      {{ model.start_datetime.format("HH:mm") }}
    </div>
    <div>
      -
    </div>
    <div>
      {{ model.end_datetime.format("HH:mm") }}
    </div>
    <div class="text-text ml-3">
      {{ duration }}
    </div>

    <transition name="fade">
      <div
        v-if="showEdit"
        ref="editPopup"
        @click.stop=""
        class="bg-bg absolute top-full z-50 right-0 rounded-lg border border-border p-2
        flex flex-col gap-3 text-text cursor-auto mt-2"
      >
        <div class="flex flex-row gap-3">
          <div class="flex flex-col w-full">
            <div class="uppercase font-bold text-sm">
              {{ $t("message.page.timeEntry.startTime") }}
            </div>
            <time-field
              class="w-full"
              v-model="model.start_datetime"
              @update:model-value="updateAnyTime"
            />
          </div>

          <div class="flex flex-col w-full">
            <div class="uppercase font-bold text-sm">
              {{ $t("message.page.timeEntry.endTime") }}
            </div>
            <time-field
              class="w-full"
              v-model="model.end_datetime"
              @update:model-value="updateAnyTime"
            />
          </div>
        </div>

        <vue-date-picker
          inline
          auto-apply
          month-change-on-scroll="inverse"
          v-model="modelForCalendar.date"
          :enable-time-picker="false"
          @update:model-value="updateStartDate"
        />
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import type { TimeEntryModel } from '@/stores/models/time-entry';
import { computed, onMounted, reactive, ref, watch } from 'vue';
import VueDatePicker from '@vuepic/vue-datepicker';
import '@vuepic/vue-datepicker/dist/main.css'
import TimeField from '../ui/TimeField.vue';

const emit = defineEmits(["update"])

const model = defineModel<TimeEntryModel>({required: true})
const modelForCalendar = reactive({date: null as null | Date})

const showEdit = ref(false)

const duration = computed(() => {
  const seconds_all = model.value.end_datetime.diff(model.value.start_datetime, "second")
  const seconds = seconds_all % 60
  const minutes_all = seconds_all / 60
  const minutes = minutes_all % 60
  const hours = Math.floor(minutes_all / 60)
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`
})

const handleClickOutside = (event: PointerEvent) => {
  const togglePopup = document.getElementById("toggle-popup")
  if (event.target === togglePopup || togglePopup?.contains(event.target)) {
    return
  }

  const colorPopup = document.getElementById("color-popup")
  if (!colorPopup?.contains(event.target) && event.target !== colorPopup) {
    showEdit.value = false
  }
}

function correlateEndDate() {
  if (model.value.end_datetime === null) {
    return
  }

  model.value.end_datetime = model.value.end_datetime
    .date(model.value.start_datetime.date())
    .month(model.value.start_datetime.month())
    .year(model.value.start_datetime.year())
  if (
    model.value.start_datetime.hour() > model.value.end_datetime.hour() ||
    (
      model.value.start_datetime.hour() == model.value.end_datetime.hour() &&
      model.value.start_datetime.minute() > model.value.end_datetime.minute()
    )
  ) {
    model.value.end_datetime = model.value.end_datetime.add(1, "day")
  }
}

function updateAnyTime() {
  correlateEndDate()
  emit("update", model)
}

function updateStartDate(newDate: Date) {
  if (
    newDate.getDate() === model.value.start_datetime.date() &&
    newDate.getMonth() === model.value.start_datetime.month() &&
    newDate.getFullYear() === model.value.start_datetime.year()
  ) {
    return
  }
  model.value.start_datetime = model.value.start_datetime
    .date(newDate.getDate())
    .month(newDate.getMonth())
    .year(newDate.getFullYear())

  correlateEndDate()
  emit("update", model)
}

watch(
  () => showEdit.value,
  (newVal) => {
    if (newVal) {
      document.addEventListener('click', handleClickOutside)
    } else {
      document.removeEventListener('click', handleClickOutside)
    }
  }
)

onMounted(() => {
  modelForCalendar.date = model.value.start_datetime.toDate()
})

watch(
  () => model.value.start_datetime,
  (newVal) => {
    modelForCalendar.date = newVal.toDate()
  }
)
</script>
