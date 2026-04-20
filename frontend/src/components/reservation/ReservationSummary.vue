<script setup>
import { IconTicket, IconArmchair, IconCash, IconUser } from '@tabler/icons-vue'

defineProps({
  performanceLabel: { type: String, required: true },
  tierName: { type: String, required: true },
  quantity: { type: Number, required: true },
  reservationType: { type: String, required: true },
  totalPrice: { type: Number, required: true },
  guestName: { type: String, required: true },
  guestEmail: { type: String, default: '' },
  guestPhone: { type: String, default: '' },
})

const typeLabel = { cash: '当日精算', invite: 'ご招待' }
</script>

<template>
  <!-- チケット風カード -->
  <div class="card overflow-hidden">
    <!-- 上部: 予約内容 -->
    <div class="card-body">
      <div class="d-flex justify-content-between align-items-start mb-3">
        <div>
          <div class="small text-muted">公演</div>
          <div class="fw-bold">{{ performanceLabel }}</div>
        </div>
        <span class="badge bg-mogi">{{ typeLabel[reservationType] }}</span>
      </div>

      <div class="row g-3 mb-3">
        <div class="col-6">
          <div class="small text-muted">席種</div>
          <div class="d-flex align-items-center gap-1">
            <IconArmchair :size="16" class="text-mogi" />
            <span class="fw-bold">{{ tierName }}</span>
          </div>
        </div>
        <div class="col-6">
          <div class="small text-muted">枚数</div>
          <div class="d-flex align-items-center gap-1">
            <IconTicket :size="16" class="text-mogi" />
            <span class="fw-bold">{{ quantity }}枚</span>
          </div>
        </div>
      </div>

      <div class="d-flex justify-content-between align-items-center pt-3" style="border-top: 1px dashed var(--mogi-border)">
        <span class="text-muted">合計</span>
        <span class="fs-4 fw-bold text-mogi">{{ totalPrice.toLocaleString() }}<small class="text-muted fw-normal">円</small></span>
      </div>
    </div>

    <!-- 切り離し風の点線 -->
    <div class="position-relative" style="height: 1px;">
      <div style="border-top: 2px dashed var(--mogi-border); position: absolute; left: 20px; right: 20px; top: 0;"></div>
      <div class="position-absolute rounded-circle bg-mogi-light" style="width: 24px; height: 24px; left: -12px; top: -12px;"></div>
      <div class="position-absolute rounded-circle bg-mogi-light" style="width: 24px; height: 24px; right: -12px; top: -12px;"></div>
    </div>

    <!-- 下部: お客様情報 -->
    <div class="card-body pt-3">
      <div class="d-flex align-items-center gap-1 mb-2">
        <IconUser :size="16" class="text-muted" />
        <span class="fw-bold">{{ guestName }}</span>
      </div>
      <div v-if="guestEmail" class="small text-muted mb-1">{{ guestEmail }}</div>
      <div v-if="guestPhone" class="small text-muted">{{ guestPhone }}</div>
    </div>
  </div>
</template>
