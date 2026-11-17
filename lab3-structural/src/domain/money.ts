export function mdl(amount: number): number {
  return Math.round(amount * 100);
}

export function formatMdl(bani: number): string {
  return `${(bani / 100).toFixed(2)} MDL`;
}

export function percentOf(bani: number, percent: number): number {
  return Math.round((bani * percent) / 100);
}
