import "./ui/style.css";

import { mount } from "./ui/app";

const root = document.querySelector<HTMLElement>("#root");
if (!root) {
  throw new Error("#root not found");
}
mount(root);
