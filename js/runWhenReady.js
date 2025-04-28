export function runWhenReady(fn) {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(fn, 0);
        }, { once: true });
    } else {
        setTimeout(fn, 0);
    }
}