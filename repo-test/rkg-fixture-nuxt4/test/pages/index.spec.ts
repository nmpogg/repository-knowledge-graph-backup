import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import IndexPage from '../../app/pages/index.vue'

describe('home page', () => {
  it('renders a link to the deterministic orders route', () => {
    const wrapper = mount(IndexPage, {
      global: {
        stubs: { NuxtLink: { props: ['to'], template: '<a :href="to"><slot /></a>' } },
      },
    })

    expect(wrapper.get('h1').text()).toBe('Order Customer Portal')
    expect(wrapper.get('a').attributes('href')).toBe('/orders')
  })
})
