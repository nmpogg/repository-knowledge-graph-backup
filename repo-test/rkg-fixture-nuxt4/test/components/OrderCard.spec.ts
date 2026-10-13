import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import OrderCard from '../../app/components/OrderCard.vue'
import type { Order } from '#shared/types/order'

const order: Order = {
  id: 'ord-1001',
  customerName: 'Ada Lovelace',
  totalCents: 12900,
  status: 'processing',
  updatedAt: '2026-10-01T09:00:00Z',
}

describe('OrderCard', () => {
  it('renders props and emits the order id', async () => {
    const wrapper = mount(OrderCard, {
      props: { order },
      global: {
        stubs: { NuxtLink: { template: '<a><slot /></a>' } },
      },
    })

    expect(wrapper.text()).toContain('Ada Lovelace')
    expect(wrapper.text()).toContain('processing')
    await wrapper.get('button').trigger('click')
    expect(wrapper.emitted('cancel')).toEqual([['ord-1001']])
  })
})
