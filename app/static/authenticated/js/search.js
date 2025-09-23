import $ from "/static/js/framework.js";

async function loadComponentCSS(shadowRoot) {
	const link = document.createElement("link");
	link.rel = "stylesheet";
	link.href = "/static/authenticated/css/search-screen.css";
	shadowRoot.appendChild(link);
}

function debounce_ms(func, delay) {
	let timeoutID;
	return function(...args) {
		clearTimeout(timeoutID);
		timeoutID = setTimeout(() => func.apply(this, args), delay);
	}
}

// https://www.geeksforgeeks.org/dsa/edit-distance-dp-5/
function editDistance(s1, s2) {
	if (!(typeof s1 === "string") || !(typeof s2 === "string")) return -1;
	const helper = (s1, s2, m, n, memo) => {
		if (m == 0) return n;
		if (n == 0) return m;
		if (memo[m][n] != - 1) return memo[m][n];
		if (s1[m - 1] == s2[n - 1]) {
			memo[m][n] = helper(s1, s2, m - 1, n - 1, memo);
			return memo[m][n];
		}
		memo[m][n] = 1 + Math.min(
			helper(s1, s2, m, n - 1, memo),
			helper(s1, s2, m - 1, n, memo),
			helper(s1, s2, m - 1, n - 1, memo),
		);
		return memo[m][n];
	}
	const createMemo = (m, n) => {
		return Array.from(
			{ length: m + 1 },
			() => Array(n + 1).fill(-1)
		);
	}
	return helper(
		s1,
		s2,
		s1.length,
		s2.length,
		createMemo(s1.length, s2.length),
	);
}

customElements.define(
	"search-screen",
	class extends HTMLElement {
		constructor() {
			super();
			this.attachShadow({ mode: "open", });
		}

		connectedCallback() {
			loadComponentCSS(this.shadowRoot);

			$.$registerRoot(this.shadowRoot);


			const searchContainer = $.$create("div");
			$.$create("p", {}, searchContainer).$textContent("Song:");
			const songSearch = $.$create("input", {}, searchContainer)
				.$type("search")
				.$id("songSearch");
			$.$create("p", {}, searchContainer).$textContent("Artist:");
			const artistSearch = $.$create("input", {}, searchContainer)
				.$type("search")
				.$id("artistSearch");
			// TODO: delete me
			const temp = $.$create("p").$id("searchOut");

			const listContainer = $.$create("div")
				.$id("listContainer");

			const song = (artist, title) => ({ artist, title });

			const songsList = [
				song("boa", "duvet"),
				song("flyleaf", "im so sick"),
				song("laufey", "lover girl"),
			];

			const formatSong = (song) => {
				return `${song.artist}: ${song.title}`;
			};

			const songToMetadata = (song) => {
				const metadata = {};
				for (let key in song) {
					metadata[`data-${key}`] = song[key];
				}
				return metadata;
			};

			const renderSongList = (list) => {
				Array.from(list).forEach((song, idx) => {
					$.$create(
						"p",
						{ ...songToMetadata(song) },
						listContainer,
					)
						.$textContent(formatSong(song))
						.$id(`listItem-${idx}`)
						.$addClass("listItem")
						.$style(`
							background-color: unset;
						`);
				});
			}

			const debouncedSearch = debounce_ms((trigger) => {
				console.log("Search Updated By:", trigger);
				console.log(`Search Term: Artist(${artistSearch.value})/Song(${songSearch.value})`);
			}, 800);
			searchContainer.$delegate(
				"input",
				'input[type="search"]',
				function (event) {
					debouncedSearch(this);
				},
			);

			listContainer.$delegate("click", ".listItem", function (event) {
				console.log("Clicked item:", this);
				console.log(`Event target: ${event.target.textContent}`);

				Array.from(this.parentElement.children).forEach(el => {
					el.$style("background-color: unset;");
				});
				this.$style("background-color: lightblue;");
			});

			renderSongList(songsList);
		}
	},
);
