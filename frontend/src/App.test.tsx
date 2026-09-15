import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('foundation application', () => {
  it('renders the system status page', () => {
    render(<App />)
    expect(screen.getByText('Voice Cloning Detection System')).toBeTruthy()
    expect(screen.getByText('Frontend online')).toBeTruthy()
  })
})
