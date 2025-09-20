import $ from "/static/js/framework.js";

customElements.define(
	"home-screen",
	class extends HTMLElement {
		constructor() {
			super();
		}

		connectedCallback() {
			const container = document.createElement("div");

			$.$registerRoot(container);
			$.$create("p")
				.$textContent("hello from home")
				.$style("color: red; padding: 25px;");

			const names = ["alice", "bob", "james"];
			$.$create("div")
				.$id("names")
				.$addChildren(names.map(
					(name) => $.$create("p").$textContent(name)
				));

			this.appendChild(container);
		}
	},
);
