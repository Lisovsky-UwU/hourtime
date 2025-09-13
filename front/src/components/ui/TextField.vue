<template>
  <div>
    <label
      v-if="label != null"
      :for="id"
      class="block text-primary-text font-semibold mb-1 uppercase text-sm"
    >
      {{ label }}
    </label>
    <input
      :type="type"
      :id="id"
      :placeholder="placeholder"
      v-model="model"
      class="w-full px-4 py-2 border rounded-lg focus:outline-none transition-all duration-300"
      :class="error ? 'border-error' : 'border-border-light'"
    >
    <div v-if="errorsText.length > 0" class="flex flex-col">
      <label
        v-for="(text, index) of errorsText"
        :key="`$text-field-error-${id}-${index}`"
        class="block text-error text-sm mt-1">
        {{ text }}
      </label>
    </div>
  </div>
</template>

<script setup>
const model = defineModel()
defineProps({
  id: String,
  type: {
    type: String,
    default: "text",
  },
  label: {
    type: String || null,
    default: null,
  },
  placeholder: {
    type: String || null,
    default: null,
  },
  error: {
    type: Boolean,
    default: false,
  },
  errorsText: {
    type: Array,
    default: [],
  }
})
</script>
