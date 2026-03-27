document.addEventListener('DOMContentLoaded', function () {
    if (typeof QRCode === 'undefined') {
        return;
    }

    document.querySelectorAll('.ticket-qr-code').forEach(function (node) {
        if (node.dataset.qrReady === 'true') {
            return;
        }

        const qrValue = node.dataset.qrValue;
        const qrSize = parseInt(node.dataset.qrSize || '148', 10);

        if (!qrValue) {
            return;
        }

        node.innerHTML = '';
        new QRCode(node, {
            text: qrValue,
            width: qrSize,
            height: qrSize,
            colorDark: '#1f2933',
            colorLight: '#ffffff',
            correctLevel: QRCode.CorrectLevel.M,
        });
        node.dataset.qrReady = 'true';
    });
});
