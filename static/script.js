document.addEventListener('DOMContentLoaded', () => {
    const qrForm = document.getElementById('qrForm');
    const qrImage = document.getElementById('qrImage');
    const spinner = document.getElementById('spinner');
    const downloadLink = document.getElementById('downloadLink');
    const copyBtn = document.getElementById('copyBtn');
    const logoInput = document.getElementById('logo');
    const logoPreview = document.getElementById('logoPreview');
    const styleDrawer = document.querySelector('.style-drawer');
    const styleDrawerToggle = document.querySelector('.style-drawer-toggle');
    const sizeSlider = document.getElementById('size');
    const sizeValue = document.getElementById('sizeValue');

    // === Helper Functions ===
    const showElement = el => el.style.display = 'block';
    const hideElement = el => el.style.display = 'none';

    const updateSizeValue = () => {
        sizeValue.textContent = `${sizeSlider.value}px`;
    };

    const previewLogo = file => {
        const reader = new FileReader();
        reader.onload = e => {
            logoPreview.innerHTML = `<img src="${e.target.result}" alt="Logo Preview">`;
        };
        reader.readAsDataURL(file);
    };

    const resetUIBeforeGeneration = () => {
        showElement(spinner);
        hideElement(qrImage);
        hideElement(downloadLink);
        hideElement(copyBtn);
    };

    const displayQRCode = base64Image => {
        qrImage.onload = () => {
            hideElement(spinner);
            showElement(qrImage);
            showElement(downloadLink);
            showElement(copyBtn);
        };
        qrImage.src = `data:image/png;base64,${base64Image}`;
        downloadLink.href = qrImage.src;
    };

    const showCopyFeedback = () => {
        const original = copyBtn.innerHTML;
        copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
        copyBtn.style.backgroundColor = 'var(--success)';
        setTimeout(() => {
            copyBtn.innerHTML = original;
            copyBtn.style.backgroundColor = 'white';
        }, 2000);
    };

    // === Event Listeners ===

    // Style drawer toggle
    styleDrawerToggle.addEventListener('click', function () {
        styleDrawer.classList.toggle('active');
        this.querySelector('i').classList.toggle('fa-chevron-down');
    });

    // Size slider value
    sizeSlider.addEventListener('input', updateSizeValue);

    // Logo file input change
    logoInput.addEventListener('change', e => {
        const file = e.target.files?.[0];
        if (file) {
            previewLogo(file);
        } else {
            logoPreview.innerHTML = '';
        }
    });

    // QR form submission
    qrForm.addEventListener('submit', e => {
        e.preventDefault();
        resetUIBeforeGeneration();

        const formData = new FormData(qrForm);

        fetch('/generate', {
            method: 'POST',
            body: formData
        })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    displayQRCode(data.image);
                } else {
                    alert(`Error: ${data.message}`);
                    hideElement(spinner);
                }
            })
            .catch(err => {
                console.error('QR generation error:', err);
                alert(`Error: ${err.message}`);
                hideElement(spinner);
            });
    });

    // Copy QR image to clipboard
    copyBtn.addEventListener('click', async () => {
        if (!qrImage.src || qrImage.style.display === 'none') {
            alert('Please generate a QR code first');
            return;
        }

        try {
            const res = await fetch(qrImage.src);
            const blob = await res.blob();

            await navigator.clipboard.write([
                new ClipboardItem({ [blob.type]: blob })
            ]);

            showCopyFeedback();
        } catch (err) {
            console.error('Clipboard error:', err);

            if (err.name === 'DataError') {
                alert('Your browser does not support image copying');
            } else {
                alert('Failed to copy image to clipboard');
            }
        }
    });

    // Initialize slider display
    updateSizeValue();
});
