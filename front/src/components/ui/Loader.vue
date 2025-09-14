<template>
  <div v-if="type === 'braces'" class="loader-braces" />
  <div v-else-if="type === 'dots'" class="loader-dots" />
  <div v-else-if="type === 'circle'" class="loader-circle" />
</template>

<script setup lang="ts">
defineProps({
  type: {
    type: String,
    default: "braces",
  },
})
</script>

<style scoped>
/* braces */
.loader-braces {
  color: #fff;
  font-family: Consolas, Menlo, Monaco, monospace;
  font-weight: bold;
  font-size: 78px;
  opacity: 0.8;
}
.loader-braces:before {
  content: "{";
  display: inline-block;
  animation: pulse 0.4s alternate infinite ease-in-out;
}
.loader-braces:after {
  content: "}";
  display: inline-block;
  animation: pulse 0.4s 0.3s alternate infinite ease-in-out;
}

@keyframes pulse {
  to {
    transform: scale(0.8);
    opacity: 0.5;
  }
}

/* dots */
.loader-dots {
  width: 4px;
  aspect-ratio: 1;
  border-radius: 50%;
  box-shadow: 19px 0 0 7px, 38px 0 0 3px, 57px 0 0 0;
  transform: translateX(-38px);
  animation: l21 .5s infinite alternate linear;
}

@keyframes l21 {
  50%  {box-shadow: 19px 0 0 3px, 38px 0 0 7px, 57px 0 0 3px}
  100% {box-shadow: 19px 0 0 0  , 38px 0 0 3px, 57px 0 0 7px}
}

/* circle */
.loader-circle {
  border: 5px solid #FFF;
  border-bottom-color: transparent;
  border-radius: 50%;
  display: inline-block;
  box-sizing: border-box;
  animation: rotation 1s linear infinite;
}

@keyframes rotation {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
