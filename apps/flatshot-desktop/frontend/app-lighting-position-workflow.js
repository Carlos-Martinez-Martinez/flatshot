function nudgeLightingScenePosition(deltaX, deltaY, options = {}) {
  if (state.settings.shadow_engine !== "studio_2_5d") {
    return false;
  }
  const scene = cloneLightingScene(state.settings.lighting_scene);
  const x = numberHelpers.roundedSceneValue(scene.main.x + Number(deltaX || 0), -1, 1, scene.main.x);
  const y = numberHelpers.roundedSceneValue(scene.main.y + Number(deltaY || 0), -1, 1, scene.main.y);
  if (scene.main.x === x && scene.main.y === y) {
    return false;
  }
  scene.main.x = x;
  scene.main.y = y;
  state.settings.lighting_scene = scene;
  markPresetDirty({ deferRender: options.deferRender });
  if (options.deferRender) {
    renderLightingSceneControls();
  }
  return true;
}
