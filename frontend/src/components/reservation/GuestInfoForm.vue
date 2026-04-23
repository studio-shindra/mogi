<script setup>
import { IconUser, IconMail, IconPhone } from '@tabler/icons-vue'

const props = defineProps({
  guestName: { type: String, default: '' },
  guestEmail: { type: String, default: '' },
  guestPhone: { type: String, default: '' },
  emailRequired: { type: Boolean, default: true },
})

const emit = defineEmits([
  'update:guestName',
  'update:guestEmail',
  'update:guestPhone',
])
</script>

<template>
  <div>
    <div class="mb-3">
      <label class="form-label small text-muted">
        お名前 <span class="text-danger">*</span>
      </label>
      <div class="input-group">
        <span class="input-group-text bg-white"><IconUser :size="18" class="text-muted" /></span>
        <input
          type="text"
          class="form-control"
          placeholder="山田 太郎"
          :value="guestName"
          @input="emit('update:guestName', $event.target.value)"
        />
      </div>
    </div>

    <div class="mb-3">
      <label class="form-label small text-muted">
        メールアドレス
        <span v-if="emailRequired" class="text-danger">*</span>
        <span v-else>（任意）</span>
      </label>
      <div class="input-group">
        <span class="input-group-text bg-white"><IconMail :size="18" class="text-muted" /></span>
        <input
          type="email"
          class="form-control"
          placeholder="example@email.com"
          :value="guestEmail"
          @input="emit('update:guestEmail', $event.target.value)"
        />
      </div>
      <div v-if="emailRequired" class="form-text small">予約確認メールをお送りします</div>
    </div>

    <div class="mb-3">
      <label class="form-label small text-muted">
        電話番号 <span class="text-danger">*</span>
      </label>
      <div class="input-group">
        <span class="input-group-text bg-white"><IconPhone :size="18" class="text-muted" /></span>
        <input
          type="tel"
          class="form-control"
          placeholder="090-1234-5678"
          :value="guestPhone"
          @input="emit('update:guestPhone', $event.target.value)"
        />
      </div>
    </div>
  </div>
</template>
