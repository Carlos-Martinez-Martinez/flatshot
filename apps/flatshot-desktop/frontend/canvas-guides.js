(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotCanvasGuides = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const DEFAULT_GUIDE_SYSTEMS = [
    {
      id: "center",
      name: "Centro",
      color: "#0f766e",
      opacity: 0.85,
      thickness: 1,
      system: true,
      rules: [
        { id: "center-x", type: "center", axis: "x" },
        { id: "center-y", type: "center", axis: "y" },
      ],
    },
    {
      id: "thirds",
      name: "Tercios",
      color: "#2563eb",
      opacity: 0.7,
      thickness: 1,
      system: true,
      rules: [
        { id: "thirds-x", type: "division", axis: "x", mode: "equal", parts: 3 },
        { id: "thirds-y", type: "division", axis: "y", mode: "equal", parts: 3 },
      ],
    },
    {
      id: "safe-10",
      name: "Márgenes 10%",
      color: "#b45309",
      opacity: 0.78,
      thickness: 1,
      system: true,
      rules: [
        { id: "safe-x", type: "mirror-pair", axis: "x", inset: 0.1 },
        { id: "safe-y", type: "mirror-pair", axis: "y", inset: 0.1 },
      ],
    },
  ];

  function clamp01(value, fallback = 0) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) {
      return fallback;
    }
    return Math.max(0, Math.min(1, numeric));
  }

  function roundPosition(value) {
    return Math.round(clamp01(value) * 10000) / 10000;
  }

  function normalizeAxis(axis) {
    return axis === "y" ? "y" : "x";
  }

  function normalizeColor(value, fallback = "#0f766e") {
    const text = String(value || "").trim();
    return /^#[0-9a-fA-F]{6}$/.test(text) ? text.toLowerCase() : fallback;
  }

  function slugify(value, fallback = "guide") {
    const base = String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    return base || fallback;
  }

  function uniqueId(base, usedIds) {
    const normalized = slugify(base);
    let candidate = normalized;
    let index = 2;
    while (usedIds.has(candidate)) {
      candidate = `${normalized}-${index}`;
      index += 1;
    }
    usedIds.add(candidate);
    return candidate;
  }

  function dedupePositions(positions, tolerance = 0.0001) {
    const sorted = positions.map(roundPosition).sort((a, b) => a - b);
    return sorted.filter((position, index) => index === 0 || Math.abs(position - sorted[index - 1]) > tolerance);
  }

  function normalizeRule(ruleInput, usedRuleIds = new Set()) {
    const rule = ruleInput && typeof ruleInput === "object" ? ruleInput : {};
    const type = ["center", "mirror-pair", "division", "line"].includes(rule.type) ? rule.type : "";
    if (!type) {
      return null;
    }
    const axis = normalizeAxis(rule.axis);
    const id = uniqueId(rule.id || `${type}-${axis}`, usedRuleIds);
    if (type === "center") {
      return { id, type, axis };
    }
    if (type === "mirror-pair") {
      const inset = roundPosition(rule.inset);
      if (inset <= 0 || inset >= 0.5) {
        return null;
      }
      return { id, type, axis, inset };
    }
    if (type === "line") {
      return { id, type, axis, position: roundPosition(rule.position) };
    }
    if (type === "division") {
      const mode = rule.mode === "custom" ? "custom" : "equal";
      if (mode === "custom") {
        const positions = Array.isArray(rule.positions)
          ? dedupePositions(rule.positions.map(roundPosition).filter((value) => value > 0 && value < 1))
          : [];
        return positions.length ? { id, type, axis, mode, positions } : null;
      }
      const parts = Math.max(2, Math.min(24, Math.round(Number(rule.parts) || 2)));
      return { id, type, axis, mode: "equal", parts };
    }
    return null;
  }

  function normalizeGuideSystem(input, usedIds = new Set()) {
    const name = String(input?.name || "").trim();
    if (!name) {
      return null;
    }
    const ruleIds = new Set();
    const rules = Array.isArray(input.rules)
      ? input.rules.map((rule) => normalizeRule(rule, ruleIds)).filter(Boolean)
      : [];
    return {
      id: uniqueId(input.id || name, usedIds),
      name,
      color: normalizeColor(input.color),
      opacity: Math.max(0.1, Math.min(1, Number(input.opacity) || 0.85)),
      thickness: Math.max(1, Math.min(4, Math.round(Number(input.thickness) || 1))),
      rules,
    };
  }

  function normalizeGuideSystemList(items = [], options = {}) {
    const defaultSystems = (options.defaultSystems || DEFAULT_GUIDE_SYSTEMS).map((system) => ({
      ...system,
      system: true,
      rules: system.rules.map((rule) => ({ ...rule })),
    }));
    const usedIds = new Set(defaultSystems.map((system) => system.id));
    const custom = Array.isArray(items) ? items : [];
    const normalizedCustom = custom
      .filter((item) => item && typeof item === "object" && !defaultSystems.some((system) => system.id === item.id))
      .map((item) => normalizeGuideSystem(item, usedIds))
      .filter(Boolean);
    return [...defaultSystems, ...normalizedCustom];
  }

  function guideSystemsForStorage(systems = [], options = {}) {
    const defaultIds = new Set((options.defaultSystems || DEFAULT_GUIDE_SYSTEMS).map((system) => system.id));
    return normalizeGuideSystemList(systems, options)
      .filter((system) => !defaultIds.has(system.id))
      .map(({ system, ...item }) => item);
  }

  function readGuideSystems(storage, key, options = {}) {
    const stored = options.storageHelpers?.readJson
      ? options.storageHelpers.readJson(storage, key, [])
      : [];
    return normalizeGuideSystemList(stored, options);
  }

  function expandRule(rule) {
    if (rule.type === "center") {
      return [{ axis: rule.axis, position: 0.5, sourceRuleId: rule.id }];
    }
    if (rule.type === "line") {
      return [{ axis: rule.axis, position: roundPosition(rule.position), sourceRuleId: rule.id }];
    }
    if (rule.type === "mirror-pair") {
      return [
        { axis: rule.axis, position: roundPosition(rule.inset), sourceRuleId: rule.id },
        { axis: rule.axis, position: roundPosition(1 - rule.inset), sourceRuleId: rule.id },
      ];
    }
    if (rule.type === "division" && rule.mode === "equal") {
      const positions = [];
      for (let index = 1; index < rule.parts; index += 1) {
        positions.push(roundPosition(index / rule.parts));
      }
      return positions.map((position) => ({ axis: rule.axis, position, sourceRuleId: rule.id }));
    }
    if (rule.type === "division" && rule.mode === "custom") {
      return rule.positions.map((position) => ({ axis: rule.axis, position, sourceRuleId: rule.id }));
    }
    return [];
  }

  function activeGuideSystems(systems = [], activeIds = []) {
    const ids = new Set(Array.isArray(activeIds) ? activeIds.map(String) : []);
    return systems.filter((system) => ids.has(system.id));
  }

  function guideLinesForSystems(systems = [], activeIds = []) {
    return activeGuideSystems(systems, activeIds).flatMap((system) => (
      system.rules.flatMap((rule) => expandRule(rule)).map((line) => ({
        ...line,
        systemId: system.id,
        systemName: system.name,
        color: system.color,
        opacity: system.opacity,
        thickness: system.thickness,
      }))
    ));
  }

  function normalizeGuideSystemOrderIds(ids = [], systems = []) {
    const available = new Set(systems.map((system) => system.id));
    const ordered = Array.isArray(ids)
      ? ids.map(String).filter((id, index, list) => available.has(id) && list.indexOf(id) === index)
      : [];
    systems.forEach((system) => {
      if (!ordered.includes(system.id)) {
        ordered.push(system.id);
      }
    });
    return ordered;
  }

  function normalizeHiddenGuideSystemIds(ids = [], systems = []) {
    const available = new Set(systems.map((system) => system.id));
    return Array.isArray(ids)
      ? ids.map(String).filter((id, index, list) => available.has(id) && list.indexOf(id) === index)
      : [];
  }

  function orderGuideSystems(systems = [], orderIds = []) {
    const byId = new Map(systems.map((system) => [system.id, system]));
    return normalizeGuideSystemOrderIds(orderIds, systems).map((id) => byId.get(id)).filter(Boolean);
  }

  function pickerGuideSystems(systems = [], orderIds = [], hiddenIds = []) {
    const hidden = new Set(normalizeHiddenGuideSystemIds(hiddenIds, systems));
    return orderGuideSystems(systems, orderIds).filter((system) => !hidden.has(system.id));
  }

  function normalizeActiveGuideSystemIds(ids = [], systems = []) {
    const available = new Set(systems.map((system) => system.id));
    return Array.isArray(ids)
      ? ids.map(String).filter((id, index, list) => available.has(id) && list.indexOf(id) === index)
      : [];
  }

  function formatPercent(value) {
    const percent = roundPosition(value) * 100;
    return `${Number(percent.toFixed(2))}%`;
  }

  function parsePercent(value, fallback = 0) {
    const text = String(value ?? "").replace("%", "").trim();
    const numeric = Number(text);
    return Number.isFinite(numeric) ? roundPosition(numeric / 100) : fallback;
  }

  return {
    DEFAULT_GUIDE_SYSTEMS,
    activeGuideSystems,
    expandRule,
    formatPercent,
    guideLinesForSystems,
    guideSystemsForStorage,
    normalizeGuideSystemOrderIds,
    normalizeActiveGuideSystemIds,
    normalizeGuideSystemList,
    normalizeHiddenGuideSystemIds,
    orderGuideSystems,
    parsePercent,
    pickerGuideSystems,
    readGuideSystems,
  };
});
