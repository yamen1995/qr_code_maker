document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("qrForm");
  const qrImage = document.getElementById("qrImage");
  const downloadLink = document.getElementById("downloadLink");

  let timeout;

  async function updatePreview() {
    // Skip if no input text
    const text = form.qrdata.value.trim();
    if (!text) {
      qrImage.style.display = "none";
      downloadLink.style.display = "none";
      return;
    }

    const formData = new FormData(form);

    try {
      const response = await fetch("/generate", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to generate QR code.");
      }

      const blob = await response.blob();
      const imageUrl = URL.createObjectURL(blob);

      qrImage.src = imageUrl;
      qrImage.style.display = "block";
      downloadLink.href = imageUrl;
      downloadLink.style.display = "inline-block";
    } catch (err) {
      console.error("QR generation error:", err);
    }
  }

  function debounceUpdate() {
    clearTimeout(timeout);
    timeout = setTimeout(updatePreview, 400); // Wait 400ms after last change
  }

  // Trigger on any change in the form
  Array.from(form.elements).forEach((el) => {
    el.addEventListener("input", debounceUpdate);
    el.addEventListener("change", debounceUpdate);
  });

  // Optional: also prevent default form submission
  form.addEventListener("submit", (e) => e.preventDefault());

  // Initial preview if any data is prefilled
  updatePreview();
});
