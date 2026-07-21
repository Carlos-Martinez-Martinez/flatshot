(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotAdjustmentHistory = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function cloneValue(value) {
    if (value === undefined) {
      return undefined;
    }
    return JSON.parse(JSON.stringify(value));
  }

  function snapshotsEqual(first, second) {
    return JSON.stringify(first) === JSON.stringify(second);
  }

  function createAdjustmentHistory(options = {}) {
    return {
      limit: Math.max(1, Math.min(100, Number(options.limit) || 50)),
      undo: [],
      redo: [],
      active: null,
    };
  }

  function pushAdjustmentHistory(history, before, after, label = "Ajuste") {
    if (!history || !before || !after || snapshotsEqual(before, after)) {
      return false;
    }
    history.undo.push({
      before: cloneValue(before),
      after: cloneValue(after),
      label,
    });
    if (history.undo.length > history.limit) {
      history.undo.splice(0, history.undo.length - history.limit);
    }
    history.redo = [];
    return true;
  }

  function startAdjustmentHistoryChange(history, token, before) {
    if (!history || !token || history.active?.token === token) {
      return false;
    }
    history.active = {
      token,
      before: cloneValue(before),
    };
    return true;
  }

  function commitAdjustmentHistoryChange(history, token, after, label = "Ajuste") {
    if (!history?.active || history.active.token !== token) {
      return false;
    }
    const before = history.active.before;
    history.active = null;
    return pushAdjustmentHistory(history, before, after, label);
  }

  function undoAdjustmentHistory(history, currentSnapshot) {
    const record = history?.undo?.pop();
    if (!record) {
      return null;
    }
    history.active = null;
    history.redo.push({
      before: cloneValue(record.before),
      after: cloneValue(currentSnapshot || record.after),
      label: record.label,
    });
    return cloneValue(record.before);
  }

  function redoAdjustmentHistory(history, currentSnapshot) {
    const record = history?.redo?.pop();
    if (!record) {
      return null;
    }
    history.active = null;
    history.undo.push({
      before: cloneValue(currentSnapshot || record.before),
      after: cloneValue(record.after),
      label: record.label,
    });
    return cloneValue(record.after);
  }

  return {
    cloneValue,
    commitAdjustmentHistoryChange,
    createAdjustmentHistory,
    pushAdjustmentHistory,
    redoAdjustmentHistory,
    snapshotsEqual,
    startAdjustmentHistoryChange,
    undoAdjustmentHistory,
  };
});
