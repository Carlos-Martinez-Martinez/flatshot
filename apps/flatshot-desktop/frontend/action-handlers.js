(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotActionHandlers = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function createActionDispatcher(handlers = {}, fallback = null) {
    return function dispatchAction(action, target = null) {
      const handler = handlers[action];
      if (typeof handler === "function") {
        return handler(target, action);
      }
      if (typeof fallback === "function") {
        return fallback(action, target);
      }
      return undefined;
    };
  }

  return {
    createActionDispatcher,
  };
});
