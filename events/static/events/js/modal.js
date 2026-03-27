document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('customConfirmModal');
    const modalMessage = document.getElementById('customModalMessage');
    const confirmButton = document.getElementById('customModalConfirmBtn');
    let formToSubmitId = null;

    if (!modal || !modalMessage || !confirmButton) {
        return;
    }

    function openCustomModal(message, targetFormId) {
        modalMessage.innerText = message;
        formToSubmitId = targetFormId || null;
        modal.hidden = false;
    }

    function closeCustomModal() {
        modal.hidden = true;
        formToSubmitId = null;
    }

    window.openCustomModal = openCustomModal;
    window.closeCustomModal = closeCustomModal;

    document.addEventListener('click', function (event) {
        const trigger = event.target.closest('[data-confirm-target]');
        if (trigger) {
            openCustomModal(trigger.dataset.confirmMessage || 'Are you sure?', trigger.dataset.confirmTarget);
            return;
        }

        if (event.target.closest('[data-modal-close]')) {
            closeCustomModal();
        }
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && !modal.hidden) {
            closeCustomModal();
        }
    });

    confirmButton.addEventListener('click', function () {
        if (!formToSubmitId) {
            closeCustomModal();
            return;
        }

        const confirmationEvent = new CustomEvent('customModalConfirmed', {
            detail: formToSubmitId,
            cancelable: true,
        });
        const shouldSubmit = document.dispatchEvent(confirmationEvent);
        const targetForm = document.getElementById(formToSubmitId);

        if (shouldSubmit && targetForm) {
            targetForm.submit();
        }

        closeCustomModal();
    });

    modal.addEventListener('click', function (event) {
        if (event.target === modal) {
            closeCustomModal();
        }
    });
});
