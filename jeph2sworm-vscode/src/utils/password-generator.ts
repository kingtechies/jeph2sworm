/**
 * Password Generator — client-side secure password generation.
 */

import * as crypto from 'crypto';

const UPPER = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
const LOWER = 'abcdefghijklmnopqrstuvwxyz';
const DIGITS = '0123456789';
const SPECIAL = '!@#$%^&*()-_=+[]{}|;:,.<>?';
const ALL = UPPER + LOWER + DIGITS + SPECIAL;

export function generatePassword(length = 32): string {
  if (length < 16) { length = 16; }
  const result = [
    UPPER[crypto.randomInt(UPPER.length)],
    LOWER[crypto.randomInt(LOWER.length)],
    DIGITS[crypto.randomInt(DIGITS.length)],
    SPECIAL[crypto.randomInt(SPECIAL.length)],
  ];
  for (let i = result.length; i < length; i++) {
    result.push(ALL[crypto.randomInt(ALL.length)]);
  }
  // Fisher-Yates shuffle
  for (let i = result.length - 1; i > 0; i--) {
    const j = crypto.randomInt(i + 1);
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result.join('');
}

export function generateSecret(bytes = 64): string {
  return crypto.randomBytes(bytes).toString('hex');
}

export function calculateEntropy(password: string): number {
  const unique = new Set(password).size;
  return password.length * Math.log2(unique);
}

export function meetsRequirements(password: string): boolean {
  return (
    password.length >= 16 &&
    /[A-Z]/.test(password) &&
    /[a-z]/.test(password) &&
    /[0-9]/.test(password) &&
    /[^A-Za-z0-9]/.test(password) &&
    calculateEntropy(password) >= 128
  );
}
