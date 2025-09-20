import $ from "/static/js/framework.js";

customElements.define(
	"settings-screen",
	class extends HTMLElement {
		constructor() {
			super();
		}

		connectedCallback() {
			const container = document.createElement("div");

			$.$registerRoot(container);
			$.$create("p").$textContent("hello from settings");

			this.appendChild(container);
		}
	},
);
