import { startScene } from "./scene/scene";

const canvas = document.querySelector<HTMLCanvasElement>("#app");
if (!canvas) {
  throw new Error("canvas #app not found");
}
startScene(canvas);
