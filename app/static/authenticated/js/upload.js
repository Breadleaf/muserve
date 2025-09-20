import $ from "/static/js/framework.js";

async function loadComponentCSS(shadowRoot) {
	const link = document.createElement("link");
	link.rel = "stylesheet";
	link.href = "/static/authenticated/css/upload-screen.css";
	shadowRoot.appendChild(link);
}

customElements.define(
	"upload-screen",
	class extends HTMLElement {
		constructor() {
			super();
			this.attachShadow({ mode: "open", });
		}

		connectedCallback() {
			loadComponentCSS(this.shadowRoot);

			$.$registerRoot(this.shadowRoot);

			$.$create("div").$style("padding: 2% 2%").$addChildren(
				$.$create("div").$id("drop").$addChildren(
					$.$create("p").$textContent("Drop files here (you can drop multiple times)")
				)
			);

			$.$create("br");

			$.$create("div").$id("controls").$addChildren([
				$.$create("button").$id("upload").$disabled(true).$textContent("Upload"),
				$.$create("button").$id("clear").$disabled(true).$textContent("Clear"),
				$.$create("input").$id("picker").$type("file").$multiple(true),
			]);

			$.$create("p").$textContent("Staged Files");
			$.$create("ul").$id("filesList");
			$.$create("pre").$id("dropOutput");


			const formatFileSize = (size) => {
				// NOTE: kibi, mebi, and gibi are
				//       kilo, mega, and giga but in base 2 rather base 10
				const kibibyte = 1024;
				const mebibyte = 1024**2;
				const gibibyte = 1024**3;
				if (size < kibibyte) return `${size} B`;
				if (size < mebibyte) return `${(size/kibibyte).toFixed(1)} KB`;
				if (size < gibibyte) return `${(size/mebibyte).toFixed(1)} MB`;
				return `${(size/gibibyte).toFixed(1)} GB`;
			};

			const fileKey = (file) => `${file.name}::${file.size}::${file.lastModified}`;

			const drop = $.$byId("drop", this.shadowRoot);
			const out = $.$byId("dropOutput", this.shadowRoot);
			const list = $.$byId("filesList", this.shadowRoot);
			const upload = $.$byId("upload", this.shadowRoot);
			const clear = $.$byId("clear", this.shadowRoot);
			const picker = $.$byId("picker", this.shadowRoot);

			const uploadState = $.$createState({
				staged: [],
				output: "",
			});

			const stageFiles = (files) => {
				const newStaged = [...uploadState.staged];
				const seen = new Set(newStaged.map(fileKey));
				for (const file of files) {
					const key = fileKey(file);
					if (!seen.has(key)) {
						newStaged.push(file);
						seen.add(key);
					}
				}
				uploadState.staged = newStaged;
			}

			["dragenter", "dragover"].forEach(eventName => {
				drop.$on(eventName, (event) => {
					event.preventDefault();
					drop.$addClass("is-dragover")
				});
			});

			["dragleave", "drop"].forEach(eventName => {
				drop.$on(eventName, (event) => {
					event.preventDefault();
					drop.$removeClass("is-dragover")
				});
			});

			drop.$on("drop", (event) => {
				const files = [];
				const items = event.dataTransfer?.items;
				if (items && items.length) {
					for (const file of items) {
						if (file.kind === "file") {
							const f = file.getAsFile();
							if (f) files.push(f);
						}
					}
				} else if (event.dataTransfer?.files?.length) {
					for (const f of event.dataTransfer.files) files.push(f);
				}
				if (files.length) stageFiles(files);
			});

			picker.$on("change", (event) => {
				if (event.target.files?.length) stageFiles(event.target.files);
				picker.$value("");
			});

			upload.$on("click", async () => {
				uploadState.output = "Uploading files...";
				const formData = new FormData();
				uploadState.staged.forEach((file, index) => {
					formData.append(`file-${index}`, file, file.name);
				});

				try {
					const res = await fetch("/send", {
						method: "POST",
						body: formData,
					});

					const text = await res.text().catch(() => "");
					if (res.ok) {
						uploadState.output = `Upload successful!\nServer response:\n${text}`;
						uploadState.staged = []; // this will trigger the bind to update the UI
					} else {
						uploadState.output = `Upload failed (${res.status} ${res.statusText || ""}).\n${text}`;
					}
				} catch (err) {
					uploadState.output = `An error occurred: ${err?.message || err}`;
				}
			});

			// this will trigger the bind to update the UI
			clear.$on("click", () => uploadState.staged = []);

			uploadState.$bind("output", out, (value) => { out.$textContent(value) });

			uploadState.$bind("staged", list, (files) => {
				list.innerHTML = "";
				files.forEach((file, idx) => {
					// create the button and set its text content and event listener separately
					const button = $.$create("button", {
						textContent: "x"
					});
					button.$on("click", () => {
						const newStaged = [...uploadState.staged];
						newStaged.splice(idx, 1);
						uploadState.staged = newStaged;
					});

					// create the span and set its text content
					const span = $.$create("span", {
						textContent: `${file.name} - ${formatFileSize(file.size)}`
					});

					// create the list item and append the button and span to it
					const li = $.$create("li", {
						className: "file-row",
						children: [button, span],
					});

					// append the final list item to the main list
					list.appendChild(li);
				});

				const hasFiles = files.length > 0;
				upload.$disabled(!hasFiles);
				clear.$disabled(!hasFiles);
			});
		}
	},
);
