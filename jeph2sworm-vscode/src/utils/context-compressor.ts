/**
 * Context Compressor — reduces LLM context size while preserving meaning.
 */

export function compressCode(code: string): string {
  const lines = code.split('\n');
  const compressed: string[] = [];
  let inBlockComment = false;

  for (const line of lines) {
    const trimmed = line.trim();
    // Skip empty lines
    if (!trimmed) { continue; }
    // Skip single-line comments
    if (trimmed.startsWith('//') || trimmed.startsWith('#')) { continue; }
    // Handle block comments
    if (trimmed.startsWith('/*')) { inBlockComment = true; }
    if (inBlockComment) {
      if (trimmed.includes('*/')) { inBlockComment = false; }
      continue;
    }
    // Skip docstrings (Python triple quotes)
    if (trimmed.startsWith('"""') || trimmed.startsWith("'''")) { continue; }
    compressed.push(line);
  }
  return compressed.join('\n');
}

export function truncateMessages(
  messages: Array<{ role: string; content: string }>,
  maxTokens: number,
): Array<{ role: string; content: string }> {
  const estimateTokens = (text: string): number => Math.ceil(text.length / 4);

  let totalTokens = 0;
  const result: Array<{ role: string; content: string }> = [];

  // Always keep system message
  const system = messages.find(m => m.role === 'system');
  if (system) {
    totalTokens += estimateTokens(system.content);
    result.push(system);
  }

  // Keep most recent messages, drop old ones
  const nonSystem = messages.filter(m => m.role !== 'system');
  const kept: typeof nonSystem = [];
  for (let i = nonSystem.length - 1; i >= 0; i--) {
    const tokens = estimateTokens(nonSystem[i].content);
    if (totalTokens + tokens > maxTokens) { break; }
    totalTokens += tokens;
    kept.unshift(nonSystem[i]);
  }

  return [...result, ...kept];
}

export function summarizeText(text: string, maxLength = 500): string {
  if (text.length <= maxLength) { return text; }
  const sentences = text.split(/[.!?]+/).filter(s => s.trim());
  let summary = '';
  for (const sentence of sentences) {
    if (summary.length + sentence.length > maxLength) { break; }
    summary += sentence.trim() + '. ';
  }
  return summary.trim() || text.substring(0, maxLength) + '...';
}
