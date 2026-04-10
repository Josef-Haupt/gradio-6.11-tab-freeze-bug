function init() {
    function overwriteStyles() {
        console.log("Overwriting styles...");
        const styles = document.createElement("style");
        styles.innerHTML = "@media (width <= 1024px) { .app {max-width: initial !important;}}";
        document.head.appendChild(styles);
    }

    overwriteStyles();
}
