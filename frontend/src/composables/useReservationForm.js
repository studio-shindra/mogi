import { ref, computed } from 'vue'

export function useReservationForm() {
  // --- state ---
  const step = ref(1)
  const performance = ref(null)
  const selectedTier = ref(null)
  const quantity = ref(1)
  // Phase A: 支払方法は当日精算のみ。内部的に cash 固定
  const reservationType = ref('cash')
  const guestName = ref('')
  const guestEmail = ref('')
  const guestPhone = ref('')

  // --- computed ---
  const unitPrice = computed(() => {
    if (!selectedTier.value) return 0
    return selectedTier.value.price_card
  })

  const totalPrice = computed(() => unitPrice.value * quantity.value)

  const canProceedStep1 = computed(
    () =>
      selectedTier.value !== null &&
      quantity.value >= 1 &&
      quantity.value <= 4 &&
      quantity.value <= (selectedTier.value?.remaining ?? 0),
  )

  const canProceedStep2 = computed(() => {
    if (!guestName.value.trim()) return false
    if (!guestPhone.value.trim()) return false
    return true
  })

  // --- actions ---
  function selectTier(tier) {
    selectedTier.value = tier
    // 枚数が残席を超えていたらリセット
    if (quantity.value > tier.remaining) {
      quantity.value = Math.min(1, tier.remaining)
    }
  }

  function nextStep() {
    if (step.value === 1 && canProceedStep1.value) {
      step.value = 2
    } else if (step.value === 2 && canProceedStep2.value) {
      step.value = 3
    }
  }

  function prevStep() {
    if (step.value > 1) {
      step.value -= 1
    }
  }

  function reset() {
    step.value = 1
    selectedTier.value = null
    quantity.value = 1
    reservationType.value = 'cash'
    guestName.value = ''
    guestEmail.value = ''
    guestPhone.value = ''
  }

  return {
    step,
    performance,
    selectedTier,
    quantity,
    reservationType,
    guestName,
    guestEmail,
    guestPhone,
    unitPrice,
    totalPrice,
    canProceedStep1,
    canProceedStep2,
    selectTier,
    nextStep,
    prevStep,
    reset,
  }
}
