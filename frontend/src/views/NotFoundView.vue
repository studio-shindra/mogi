<script setup>
import { IconMoodSad } from '@tabler/icons-vue'
</script>

<template>
  <div class="container py-5 text-center" style="padding-top: 80px">
    <IconMoodSad :size="48" class="text-muted mb-3" stroke-width="1.2" />
    <h1 class="fs-4 fw-bold mb-2">ページが見つかりません</h1>
    <p class="text-muted mb-4">お探しのページは存在しないか、移動した可能性があります。</p>
    <RouterLink to="/" class="btn btn-outline-primary">トップに戻る</RouterLink>
  </div>
</template>
