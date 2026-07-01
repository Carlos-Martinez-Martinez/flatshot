function readOutputProfiles(activeProfileId = "") {
  const saved = storageHelpers.readJson(window.localStorage, STORAGE_KEYS.outputProfiles, null);
  const profiles = Array.isArray(saved) ? saved : defaultOutputProfiles;
  const activeFormatIds = storageHelpers.readJson(window.localStorage, STORAGE_KEYS.activeOutputFormats, null);
  const normalized = outputProfileHelpers.normalizeOutputProfileList(profiles, activeProfileId).map((profile) => (
    Array.isArray(activeFormatIds)
      ? { ...profile, enabled: activeFormatIds.includes(profile.id) }
      : profile
  ));
  return normalized.length ? normalized : outputProfileHelpers.normalizeOutputProfileList(defaultOutputProfiles, activeProfileId);
}
