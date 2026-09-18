import { describe, it, expect } from 'vitest';
import { escapeMdCell } from '../../packages/scripts/src/docs/generate-agents-doc';

describe('escapeMdCell — CodeQL #6 (js/incomplete-sanitization)', () => {
  it('should escape a plain pipe', () => {
    expect(escapeMdCell('a | b')).toBe('a \\| b');
  });

  it('should escape a lone backslash', () => {
    expect(escapeMdCell('a \\ b')).toBe('a \\\\ b');
  });

  it('should escape backslash-then-pipe without letting the backslash consume the pipe escape', () => {
    // Este é exactamente o caso que a ordem errada (só escapar | primeiro)
    // deixava passar: um "\|" já existente no texto original ficava
    // indistinguível de um "|" escapado por esta função.
    const input = 'literal backslash \\ then a | pipe';
    const output = escapeMdCell(input);
    expect(output).toBe('literal backslash \\\\ then a \\| pipe');
  });

  it('should not alter text with neither backslash nor pipe', () => {
    expect(escapeMdCell('plain text')).toBe('plain text');
  });
});
