document.getElementById('qrForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const response = await fetch('/generate', {
  method: 'POST',
  body: new FormData(e.target)
});
const blob = await response.blob();
const imageUrl = URL.createObjectURL(blob);

document.getElementById('qrImage').src = imageUrl;
document.getElementById('downloadLink').href = imageUrl;
document.getElementById('downloadLink').style.display = 'inline-block';

  });