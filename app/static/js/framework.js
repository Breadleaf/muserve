const $ = () => {
	console.log("muserve framework");
}

$._setup = function (element) {
	if (!element || !(element instanceof HTMLElement)) {
		console.warn("[framework] _setup(): provided element is not an HTMLElement or is null");
		return null;
	}

	// attach element's prototype object's properties to element as function
	// NOTE: each property is name -> `$${name}`
	let prototype = Object.getPrototypeOf(element);
	while (prototype) {
		Object.getOwnPropertyNames(prototype).forEach((key) => {
			const property = `$${key}`;
			if (!element.hasOwnProperty(property)) {
				element[property] = function (data) {
					this[key] = data;
					return this;
				}
			}
		});

		// move up the prototype chain
		prototype = Object.getPrototypeOf(prototype);
	}

	// give element the $addChildren function if it has appendChild property
	if ("appendChild" in element) {
		element["$addChildren"] = function (children) {
			if (Array.isArray(children)) {
				children.forEach((child) => {
					element.appendChild(child);
				});
			} else {
				element.appendChild(children);
			}
			return this;
		}
	}

	// give element $style function
	element.$style = function (data) {
		this.style.cssText = data;
		return this;
	}

	// give element $on function which attaches an event listener to it
	element.$on = function (eventType, callback) {
		this.addEventListener(eventType, callback);
		return this;
	}

	// Important NOTE: if you pass a arrow function, it will inherit the
	// `this` from the lexical scope, if you pass a `function ()` function,
	// `matching` will be used as `this` inside the function
	element.$delegate = function (eventType, selector, callback) {
		this.addEventListener(eventType, (event) => {
			// get element that triggered the event
			const target = event.target;
			// check if target matches selector
			// closest looks up DOM tree for closest ancestor
			const matching = target.closest(selector);
			// if a matching element is found, it is a child of the
			// element the listener is on, then call the callback
			if (matching && this.contains(matching)) {
				callback.call(matching, event);
			}
		});
		return this;
	}

	element.$addClass = function (className) {
		element.classList.add(className);
		return this;
	}

	element.$removeClass = function (className) {
		element.classList.remove(className);
		return this;
	}

	element.$toggleClass = function (className) {
		if (!className) throw new Error("[framework] $toggleClass(): className must be defined");
		if (element.classList.contains(className)) {
			element.classList.remove(className);
		} else {
			element.classList.add(className);
		}
		return this;
	}

	return element;
}

$.$byId = function (id, target = document) {
	if (!(target instanceof HTMLElement || target instanceof Document || target instanceof ShadowRoot)) {
		throw new Error("[framework] $byId(): The target must be an HTMLElement, Document, or ShadowRoot.");
	}
	return this._setup(target.getElementById(id));
}

$.$byName = function (name, target = document) {
	if (!(target instanceof HTMLElement || target instanceof Document || target instanceof ShadowRoot)) {
		throw new Error("[framework] $byName(): The target must be an HTMLElement, Document, or ShadowRoot.");
	}
	return Array.from(target.getElementsByName(name)).map(element => this._setup(element));
}

$.$byTag = function (name, target = document) {
	if (!(target instanceof HTMLElement || target instanceof Document || target instanceof ShadowRoot)) {
		throw new Error("[framework] $byTag(): The target must be an HTMLElement, Document, or ShadowRoot.");
	}
	return Array.from(target.getElementsByTagName(name)).map(element => this._setup(element));
}

$.$byClass = function (name, target = document) {
	if (!(target instanceof HTMLElement || target instanceof Document || target instanceof ShadowRoot)) {
		throw new Error("[framework] $byClass(): The target must be an HTMLElement, Document, or ShadowRoot.");
	}
	return Array.from(target.getElementsByClassName(name)).map(element => this._setup(element));
}

$.$select = function (selector, target = document) {
	if (!(target instanceof HTMLElement || target instanceof Document || target instanceof ShadowRoot)) {
		throw new Error("[framework] $select(): The target must be an HTMLElement, Document, or ShadowRoot.");
	}
	return this._setup(target.querySelector(selector));
}

$.$selectAll = function (selector, target = document) {
	if (!(target instanceof HTMLElement || target instanceof Document || target instanceof ShadowRoot)) {
		throw new Error("[framework] $selectAll(): The target must be an HTMLElement, Document, or ShadowRoot.");
	}
	return Array.from(target.querySelectorAll(selector)).map(element => this._setup(element));
}

$._root = "uninitialized";

$.$registerRoot = function (element) {
	if (element instanceof HTMLElement || element instanceof ShadowRoot) {
		this._root = element;
	} else {
		throw new Error("[framework] $registerRoot(): root container can only be registered to an HTMLElement or ShadowRoot");
	}
}

$.$create = function (elementType, props = {}, attachToElement = this._root) {
	if (this._root === "uninitialized") {
		throw new Error("[framework] $create(): you need to register the root container first");
	}

	const newElement = document.createElement(elementType);

	for (const key in props) {
		if (props.hasOwnProperty(key)) {
			const value = props[key];
			switch (key) {
				case "children":
					this._setup(newElement).$addChildren(value);
					break;
				case "onClick":
				case "onInput":
				case "onChange":
					this._setup(newElement).$on(key.substring(2).toLowerCase(), value);
					break;
				case "style":
					this._setup(newElement).$style(value);
					break;
				case "className":
					newElement.className = value;
					break;
				case "textContent":
					newElement.textContent = value;
					break;
				default:
					if (typeof value === 'boolean') {
						newElement[key] = value;
					} else {
						newElement.setAttribute(key, value);
					}
				break;
			}
		}
	}

	if (attachToElement) attachToElement.appendChild(newElement);

	return this._setup(newElement);
}

$.$createState = function (initialState) {
	const bindings = new Map();

	const handler = {
		set(target, key, value) {
			// check if value is different
			if (target[key] !== value) {
				target[key] = value;

				// trigger DOM update for any bound elements
				if (bindings.has(key)) {
					bindings.get(key).forEach((binding) => {
						binding.update(value);
					});
				}
			}
			return true;
		}
	};

	const proxy = new Proxy(initialState, handler);

	proxy.$bind = function (key, element, updateFunction) {
		if (!bindings.has(key)) {
			bindings.set(key, []);
		}
		bindings.get(key).push({ element, update: updateFunction });
		updateFunction(proxy[key]); // initial update
	}

	return proxy;
}

export default $;
