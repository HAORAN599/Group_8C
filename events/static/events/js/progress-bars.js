document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-progress-value]').forEach(function (node) {
        const rawValue = parseFloat(node.dataset.progressValue || '0');
        const clampedValue = Number.isFinite(rawValue) ? Math.max(0, Math.min(100, rawValue)) : 0;

        node.style.width = clampedValue + '%';
    });
});
