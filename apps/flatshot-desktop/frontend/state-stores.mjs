import "./state-stores.js";

const stores = globalThis.FlatShotAppStateStores;

if (!stores) {
  throw new Error("FlatShotAppStateStores is unavailable");
}

export const stateStoreFields = stores.stateStoreFields;
export const stateStoreSnapshot = stores.stateStoreSnapshot;
export const storeNames = stores.storeNames;
