function rangeFillPercent(input) {
  if (!input || input.type !== "range") {
    return 0;
  }
  const min = Number(input.min || 0);
  const max = Number(input.max || 100);
  const value = Number(input.value || min);
  if (!Number.isFinite(min) || !Number.isFinite(max) || max <= min) {
    return 0;
  }
  return Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));
}

function syncRangeFill(input) {
  if (input?.type !== "range") {
    return;
  }
  input.style.setProperty("--range-fill", `${rangeFillPercent(input)}%`);
}

function syncRangeFillStyles() {
  $$(".settings-panel input[type='range']").forEach(syncRangeFill);
}
