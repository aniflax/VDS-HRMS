import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import Onboarding from '../../../src/pages/auth/Onboarding.jsx';

const { apiPost } = vi.hoisted(() => ({
  apiPost: vi.fn(),
}));

vi.mock('../../../src/api/axios', () => ({
  default: {
    post: apiPost,
  },
}));

const setMobileViewport = () => {
  window.matchMedia = vi.fn().mockImplementation((query) => ({
    matches: query.includes('899.95px'),
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
};

describe('Onboarding', () => {
  beforeEach(() => {
    sessionStorage.clear();
    apiPost.mockReset();
    setMobileViewport();
    window.URL.createObjectURL = vi.fn(() => 'blob:test-document');
    window.URL.revokeObjectURL = vi.fn();
  });

  it('restores non-sensitive mobile draft fields after a reload', () => {
    sessionStorage.setItem('hrms.onboarding.draft.v1', JSON.stringify({
      first_name: 'Teja',
      last_name: 'Krishna',
      email: 'teja@example.com',
      phone: '9876543210',
      address: 'Bangalore',
      password: 'should-not-restore',
    }));

    render(<Onboarding />);

    expect(screen.getByLabelText(/First Name/i)).toHaveValue('Teja');
    expect(screen.getByLabelText(/Last Name/i)).toHaveValue('Krishna');
    expect(screen.getByLabelText(/Email Address/i)).toHaveValue('teja@example.com');
    expect(screen.getByLabelText(/Phone Number/i)).toHaveValue('9876543210');
    expect(screen.getByLabelText(/Full Address/i)).toHaveValue('Bangalore');
    expect(screen.getByLabelText(/^Password/i)).toHaveValue('');
  });

  it('does not submit the form when a document is uploaded', () => {
    render(<Onboarding />);

    fireEvent.change(screen.getByLabelText(/First Name/i), { target: { value: 'Teja' } });
    const file = new File([new Uint8Array(120 * 1024)], 'id-proof.pdf', { type: 'application/pdf' });
    const fileInput = document.querySelector('input[type="file"]');

    fireEvent.change(fileInput, { target: { files: [file] } });

    expect(apiPost).not.toHaveBeenCalled();
    expect(screen.getByLabelText(/First Name/i)).toHaveValue('Teja');
    expect(screen.getByText('Uploaded')).toBeInTheDocument();
  });

  it('keeps the mobile page state when jpg and png documents are uploaded in later slots', () => {
    render(<Onboarding />);

    fireEvent.change(screen.getByLabelText(/First Name/i), { target: { value: 'Teja' } });
    const fileInputs = document.querySelectorAll('input[type="file"]');
    const pdf = new File([new Uint8Array(120 * 1024)], 'id-proof.pdf', { type: 'application/pdf' });
    const jpg = new File([new Uint8Array(120 * 1024)], 'pan-card.jpg', { type: 'image/jpeg' });
    const png = new File([new Uint8Array(120 * 1024)], 'passbook.png', { type: 'image/png' });

    fireEvent.change(fileInputs[0], { target: { files: [pdf] } });
    fireEvent.change(fileInputs[1], { target: { files: [jpg] } });
    fireEvent.change(fileInputs[2], { target: { files: [png] } });

    expect(document.querySelector('form')).toBeNull();
    expect(apiPost).not.toHaveBeenCalled();
    expect(screen.getByLabelText(/First Name/i)).toHaveValue('Teja');
    expect(screen.getAllByText('Uploaded')).toHaveLength(3);
  });

  it('shows the actual request failure when onboarding registration cannot reach the API', async () => {
    apiPost.mockRejectedValueOnce(new Error('Network Error'));
    render(<Onboarding />);

    fireEvent.change(screen.getByLabelText(/First Name/i), { target: { value: 'Teja' } });
    fireEvent.change(screen.getByLabelText(/Last Name/i), { target: { value: 'Krishna' } });
    fireEvent.change(screen.getByLabelText(/Phone Number/i), { target: { value: '9876543210' } });
    fireEvent.change(screen.getByLabelText(/Email Address/i), { target: { value: 'teja@example.com' } });
    fireEvent.change(screen.getByLabelText(/^Password/i), { target: { value: 'ChangeMe@123' } });
    fireEvent.change(screen.getByLabelText(/^Confirm Password/i), { target: { value: 'ChangeMe@123' } });
    fireEvent.change(screen.getByLabelText(/Full Address/i), { target: { value: 'Bangalore' } });

    const fileInputs = document.querySelectorAll('input[type="file"]');
    const pdf = new File([new Uint8Array(120 * 1024)], 'id-proof.pdf', { type: 'application/pdf' });
    fireEvent.change(fileInputs[0], { target: { files: [pdf] } });
    fireEvent.change(fileInputs[1], { target: { files: [pdf] } });
    fireEvent.change(fileInputs[2], { target: { files: [pdf] } });
    fireEvent.click(screen.getByRole('button', { name: /Register for Onboarding/i }));

    expect(await screen.findByText('Network Error')).toBeInTheDocument();
  });
});
