<script setup>
import { IconHome, IconTicket } from '@tabler/icons-vue'
</script>

<template>
  <nav class="footer-nav">
    <div class="d-flex justify-content-around">
      <RouterLink to="/">
        <IconHome :size="22" stroke-width="1.5" />
        <span>ホーム</span>
      </RouterLink>
      <RouterLink to="/myticket">
        <IconTicket :size="22" stroke-width="1.5" />
        <span>チケット</span>
      </RouterLink>
    </div>
  </nav>
</template>
