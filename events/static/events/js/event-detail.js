document.addEventListener('DOMContentLoaded', function () {
    const shareButton = document.getElementById('shareEventButton');
    const shareStatus = document.getElementById('shareEventStatus');
    const bookingForm = document.getElementById('ajaxBookingForm');
    const bookingActionArea = document.getElementById('booking-action-area');
    const bookingButton = document.getElementById('btn-submit');
    const bookingCount = document.getElementById('booked-count');
    const bookingProgressBar = document.getElementById('booking-progress-bar');
    const checkInForm = document.getElementById('ticketCheckInForm');
    const checkInFeedback = document.getElementById('checkInFeedback');
    const checkedInCount = document.getElementById('checkedInCount');
    const checkedInCountInline = document.getElementById('checkedInCountInline');
    const scanQrButton = document.getElementById('scanQrButton');
    const stopQrButton = document.getElementById('stopQrButton');
    const checkInScanner = document.getElementById('checkInScanner');
    const checkInVideo = document.getElementById('checkInVideo');
    const checkInScannerStatus = document.getElementById('checkInScannerStatus');
    let shareStatusTimer = null;
    let scannerStream = null;
    let scannerTimer = null;
    let scannerDetector = null;
    let checkInInFlight = false;
    let bookingInFlight = false;

    function updateShareStatus(message, isError) {
        if (!shareStatus) {
            return;
        }

        shareStatus.textContent = message || '';
        shareStatus.classList.toggle('is-error', Boolean(isError));

        if (shareStatusTimer) {
            window.clearTimeout(shareStatusTimer);
        }

        if (message) {
            shareStatusTimer = window.setTimeout(function () {
                shareStatus.textContent = '';
                shareStatus.classList.remove('is-error');
            }, 2600);
        }
    }

    async function copyShareUrl(url) {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(url);
            return;
        }

        const tempField = document.createElement('textarea');
        tempField.value = url;
        tempField.setAttribute('readonly', '');
        tempField.style.position = 'absolute';
        tempField.style.left = '-9999px';
        document.body.appendChild(tempField);
        tempField.select();
        document.execCommand('copy');
        document.body.removeChild(tempField);
    }

    if (shareButton) {
        shareButton.addEventListener('click', async function () {
            const title = shareButton.dataset.shareTitle || document.title;
            const text = shareButton.dataset.shareText || 'Take a look at this event.';
            const url = window.location.href;

            try {
                if (navigator.share) {
                    await navigator.share({ title: title, text: text, url: url });
                    updateShareStatus('Event link shared.');
                    return;
                }

                await copyShareUrl(url);
                updateShareStatus('Event link copied.');
            } catch (error) {
                if (error && error.name === 'AbortError') {
                    return;
                }

                updateShareStatus('Unable to share right now.', true);
            }
        });
    }

    function setCheckInFeedback(message, tone) {
        if (!checkInFeedback) {
            return;
        }

        checkInFeedback.textContent = message || '';
        checkInFeedback.classList.remove('d-none', 'checkin-feedback-success', 'checkin-feedback-error', 'checkin-feedback-info');

        if (!message) {
            checkInFeedback.classList.add('d-none');
            return;
        }

        checkInFeedback.classList.add('checkin-feedback-' + (tone || 'info'));
    }

    function updateCheckedInCount(count) {
        if (checkedInCount) {
            checkedInCount.textContent = count;
        }

        if (checkedInCountInline) {
            checkedInCountInline.textContent = count;
        }
    }

    function updateParticipantRow(payload) {
        if (!payload || !payload.ticket_id) {
            return;
        }

        const row = document.querySelector('[data-ticket-id="' + payload.ticket_id + '"]');
        if (!row) {
            return;
        }

        const statusNode = row.querySelector('[data-participant-status]');
        if (statusNode) {
            statusNode.textContent = payload.status_label;
            statusNode.className = 'participant-status participant-status-' + payload.status_key;
        }

        const actionArea = row.querySelector('.participant-actions');
        if (actionArea) {
            actionArea.innerHTML = '<span class="participant-checkin-state is-complete">Checked In</span>';
        }
    }

    async function submitCheckIn(formElement) {
        if (!formElement || checkInInFlight) {
            return;
        }

        const submitButton = formElement.querySelector('button[type="submit"]');
        const originalLabel = submitButton ? submitButton.innerHTML : '';
        const formData = new FormData(formElement);
        const csrfToken = formElement.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

        checkInInFlight = true;
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Checking...';
        }

        try {
            const response = await fetch(formElement.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken,
                },
                body: formData,
            });
            const data = await response.json();

            if (!response.ok) {
                throw data;
            }

            setCheckInFeedback(data.message, 'success');
            updateCheckedInCount(data.checked_in_count);
            updateParticipantRow(data);

            const codeInput = checkInForm ? checkInForm.querySelector('input[name="ticket_code"]') : null;
            if (codeInput) {
                codeInput.value = '';
            }
        } catch (error) {
            setCheckInFeedback((error && error.message) || 'Unable to check in this attendee right now.', 'error');
        } finally {
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = originalLabel;
            }
            checkInInFlight = false;
        }
    }

    if (checkInForm) {
        checkInForm.addEventListener('submit', function (event) {
            event.preventDefault();
            submitCheckIn(checkInForm);
        });
    }

    document.querySelectorAll('.participant-checkin-form').forEach(function (formElement) {
        formElement.addEventListener('submit', function (event) {
            event.preventDefault();
            submitCheckIn(formElement);
        });
    });

    function stopScanner() {
        if (scannerTimer) {
            window.clearInterval(scannerTimer);
            scannerTimer = null;
        }

        if (scannerStream) {
            scannerStream.getTracks().forEach(function (track) {
                track.stop();
            });
            scannerStream = null;
        }

        if (checkInVideo) {
            checkInVideo.pause();
            checkInVideo.srcObject = null;
        }

        if (checkInScanner) {
            checkInScanner.classList.add('d-none');
        }
    }

    async function startScanner() {
        if (!checkInScanner || !checkInVideo || !checkInForm) {
            return;
        }

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            setCheckInFeedback('Camera access is not available on this device. Use the ticket code instead.', 'info');
            return;
        }

        if (!('BarcodeDetector' in window)) {
            setCheckInFeedback('QR scanning is not supported here yet. Use the ticket code instead.', 'info');
            return;
        }

        try {
            scannerDetector = new BarcodeDetector({ formats: ['qr_code'] });
            scannerStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: { ideal: 'environment' },
                },
                audio: false,
            });

            checkInVideo.srcObject = scannerStream;
            await checkInVideo.play();
            checkInScanner.classList.remove('d-none');
            if (checkInScannerStatus) {
                checkInScannerStatus.textContent = 'Scanning for a ticket QR code...';
            }

            scannerTimer = window.setInterval(async function () {
                if (!scannerDetector || checkInInFlight || checkInVideo.readyState < 2) {
                    return;
                }

                try {
                    const codes = await scannerDetector.detect(checkInVideo);
                    if (!codes.length || !codes[0].rawValue) {
                        return;
                    }

                    const codeInput = checkInForm.querySelector('input[name="ticket_code"]');
                    if (!codeInput) {
                        return;
                    }

                    codeInput.value = codes[0].rawValue.trim().toUpperCase();
                    if (checkInScannerStatus) {
                        checkInScannerStatus.textContent = 'Ticket found. Checking in attendee...';
                    }
                    stopScanner();
                    submitCheckIn(checkInForm);
                } catch (scanError) {
                    if (checkInScannerStatus) {
                        checkInScannerStatus.textContent = 'Unable to read that code yet. Try holding it a bit steadier.';
                    }
                }
            }, 500);
        } catch (error) {
            stopScanner();
            setCheckInFeedback('Camera access was blocked. Use the ticket code instead.', 'error');
        }
    }

    if (scanQrButton) {
        scanQrButton.addEventListener('click', function () {
            startScanner();
        });
    }

    if (stopQrButton) {
        stopQrButton.addEventListener('click', function () {
            stopScanner();
            if (checkInScannerStatus) {
                checkInScannerStatus.textContent = 'Scanner stopped.';
            }
        });
    }

    function updateProgressBar(value) {
        if (!bookingProgressBar) {
            return;
        }

        const clampedValue = Math.max(0, Math.min(100, value));
        bookingProgressBar.dataset.progressValue = String(clampedValue);
        bookingProgressBar.style.width = clampedValue + '%';
    }

    async function executeAjaxBooking() {
        if (!bookingForm || !bookingButton || bookingInFlight) {
            return;
        }

        bookingInFlight = true;
        bookingButton.disabled = true;
        bookingButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Confirming...';

        try {
            const response = await fetch(window.location.href, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: new FormData(bookingForm),
            });
            const payload = await response.json();

            if (!response.ok) {
                throw payload;
            }

            if (bookingCount) {
                bookingCount.textContent = payload.current_count;
            }
            const nextProgress = payload.capacity ? (payload.current_count / payload.capacity) * 100 : 0;
            updateProgressBar(nextProgress);

            if (bookingActionArea) {
                bookingActionArea.innerHTML = [
                    '<div class="booking-success-banner text-center py-3 mb-3">',
                    '<i class="bi bi-check-circle-fill me-2"></i><strong>Registration confirmed</strong>',
                    '</div>',
                    '<a href="' + (bookingForm.dataset.myTicketsUrl || '/my-tickets/') + '" class="btn btn-outline-primary w-100 py-3 fw-bold">',
                    '<i class="bi bi-ticket-perforated me-2"></i>View My Tickets',
                    '</a>',
                ].join('');
            }
        } catch (error) {
            window.alert((error && error.message) || 'An error occurred during booking.');
            bookingButton.disabled = false;
            bookingButton.textContent = 'Register for Event';
        } finally {
            bookingInFlight = false;
        }
    }

    if (bookingForm) {
        bookingForm.addEventListener('submit', function (event) {
            event.preventDefault();
            window.openCustomModal(bookingForm.dataset.confirmMessage || 'Confirm this action?', bookingForm.id);
        });

        document.addEventListener('customModalConfirmed', function (event) {
            if (event.detail === bookingForm.id) {
                event.preventDefault();
                executeAjaxBooking();
            }
        });
    }
});
