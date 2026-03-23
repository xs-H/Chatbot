<template>
  <div class="sidebar" :class="{ collapsed }">
    <div class="logo">
      <div class="logo-content">
        <img class="logo-circle" src="/images/logo.png" alt="Logo" />
        <span class="stereo-text" data-text="心语智友">心语智友</span>
      </div>

      <div class="collapse-button-container" @click="$emit('toggle')">
        <i
          class="fa-solid collapse-button"
          :class="collapsed ? 'fa-chevron-right' : 'fa-bars'"
        ></i>
      </div>
    </div>

    <div class="button">
      <i class="fa-solid fa-plus"></i>
      开启新对话
    </div>

    <div class="button">
      <i class="fa-solid fa-comments"></i>
      最近对话
    </div>

    <div class="profile">
      <img class="avatar" src="/images/avatar.jpg" alt="Avatar" />
      HJG
    </div>
  </div>
</template>

<script setup>
defineProps({
  collapsed: Boolean
})

defineEmits(['toggle'])
</script>