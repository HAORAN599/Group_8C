let formToSubmitId = null;

function openCustomModal(message, targetFormId) {
    document.getElementById('customModalMessage').innerText = message;
    formToSubmitId = targetFormId;
    document.getElementById('customConfirmModal').style.display = 'flex';
}

function closeCustomModal() {
    document.getElementById('customConfirmModal').style.display = 'none';
    formToSubmitId = null;
}

document.getElementById('customModalConfirmBtn').addEventListener('click', function() {
    if (formToSubmitId) {
        document.getElementById(formToSubmitId).submit();
    }
    closeCustomModal();
});

document.getElementById('customConfirmModal').addEventListener('click', function(event) {
    if (event.target === this) {
        closeCustomModal();
    }
});