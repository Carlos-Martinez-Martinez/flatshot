(function (root, factory) {
  const api = factory(root.FlatShotOutputProfiles || {});
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotExportPayload = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function (outputProfileHelpers) {
  function bridgeImagePaths(images = []) {
    return images
      .filter((image) => image?.source === "bridge" && image.path)
      .map((image) => image.path);
  }

  function failedBridgeExportImages(images = [], completedItems = []) {
    const failedPaths = new Set(
      (Array.isArray(completedItems) ? completedItems : [])
        .filter((item) => item?.success === false && item.path)
        .map((item) => String(item.path))
    );
    if (!failedPaths.size) {
      return [];
    }
    return (Array.isArray(images) ? images : []).filter((image) =>
      image?.source === "bridge"
      && image.path
      && image.exportable !== false
      && failedPaths.has(String(image.path))
    );
  }

  function primaryOutputProfile(profiles = [], activeOutputProfileId = "", fallbackProfile = null) {
    return profiles.find((profile) => profile.id === activeOutputProfileId)
      || profiles[0]
      || fallbackProfile;
  }

  function buildBridgeExportPayload(options = {}) {
    const profiles = Array.isArray(options.profiles) ? options.profiles : [];
    const primary = primaryOutputProfile(profiles, options.activeOutputProfileId, options.fallbackProfile);
    const seenVariantIds = new Set();
    return {
      imagePaths: bridgeImagePaths(options.images),
      presetName: options.presetName,
      settings: options.settings,
      imageOverrides: options.imageOverrides,
      export: {
        format: primary.format,
        size: outputProfileHelpers.outputProfileSize(primary),
        background: primary.background,
        destinationMode: primary.destinationMode,
        destinationValue: primary.destinationValue,
        outputFolderName: primary.destinationMode === "source" ? primary.destinationValue : "Salida",
        customOutputPath: primary.destinationMode === "custom" ? primary.destinationValue : "",
        namingTemplate: primary.naming,
        suffix: primary.suffix,
        variants: profiles.map((profile, index) =>
          outputProfileHelpers.exportVariantPayloadFromProfile(profile, index, seenVariantIds)
        ),
      },
    };
  }

  return {
    bridgeImagePaths,
    buildBridgeExportPayload,
    failedBridgeExportImages,
    primaryOutputProfile,
  };
});
